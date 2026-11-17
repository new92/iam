"""Small, testable boundary around instagrapi. No bulk engagement automation."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import IAMError
from .validation import bounded_limit, identifier, local_media, nonempty_text, username

# Never serialize platform tokens, passwords, TOTP seeds, security codes, or sessions.
PUBLIC_PROFILE_FIELDS = (
    "pk", "username", "full_name", "biography", "is_private", "is_verified",
    "follower_count", "following_count", "media_count", "external_url", "category",
)
SAFE_SECURITY_FIELDS = (
    "is_phone_confirmed", "is_two_factor_enabled", "is_totp_two_factor_enabled",
    "is_trusted_notifications_enabled", "has_reachable_email",
    "is_whatsapp_two_factor_enabled",
)
PUBLIC_USER_FIELDS = ("pk", "username", "full_name", "is_private", "is_verified")
PUBLIC_MEDIA_FIELDS = ("pk", "id", "code", "media_type", "caption_text", "taken_at", "like_count", "comment_count")
PUBLIC_HIGHLIGHT_FIELDS = ("pk", "title", "media_count")


def field(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def view(obj: Any, fields: tuple[str, ...]) -> dict[str, Any]:
    """Allowlist only. Prevent accidental leakage of private library objects."""
    return {name: field(obj, name) for name in fields if field(obj, name) is not None}


def user_view(item: Any) -> dict[str, Any]:
    return view(item, PUBLIC_USER_FIELDS)


def short_media(item: Any) -> dict[str, Any]:
    data = view(item, PUBLIC_MEDIA_FIELDS)
    data["owner"] = view(field(item, "user", {}), ("pk", "username"))
    return data


def collection(items: Any, limit: int, convert=user_view) -> list[dict[str, Any]]:
    if isinstance(items, dict):
        values = list(items.values())
    else:
        values = list(items or [])
    return [convert(item) for item in values[:limit]]


class AccountManager:
    def __init__(self, client: Any, own_username: str):
        self.client = client
        self.username = username(own_username)
        self._own_id: str | None = None

    def own_id(self) -> str:
        if self._own_id is None:
            self._own_id = identifier(str(self.client.user_id_from_username(self.username)))
        return self._own_id

    def account(self) -> dict[str, Any]:
        return view(self.client.account_info(), PUBLIC_PROFILE_FIELDS)

    def security(self) -> dict[str, Any]:
        # Deliberately exclude backup codes, phone, emails, and TOTP seeds.
        return view(self.client.account_security_info(), SAFE_SECURITY_FIELDS)

    def user(self, target: str) -> dict[str, Any]:
        target = username(target)
        return view(self.client.user_info_by_username(target), PUBLIC_PROFILE_FIELDS)

    def user_id(self, target: str) -> str:
        return identifier(str(self.client.user_id_from_username(username(target))))

    def username_from_id(self, pk: str) -> dict[str, str]:
        return {"username": username(str(self.client.username_from_user_id(identifier(pk))))}

    def followers(self, target: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        limit = bounded_limit(limit)
        pk = self.user_id(target) if target else self.own_id()
        return collection(self.client.user_followers(pk, amount=limit), limit)

    def following(self, target: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        limit = bounded_limit(limit)
        pk = self.user_id(target) if target else self.own_id()
        return collection(self.client.user_following(pk, amount=limit), limit)

    def not_following_back(self, limit: int = 50) -> dict[str, Any]:
        """Compare *sampled* follow relationships only; never claim completeness."""
        limit = bounded_limit(limit, maximum=100)
        followers = self.followers(limit=limit)
        following = self.following(limit=limit)
        follower_ids = {str(u.get("pk")) for u in followers}
        return {"sample_size": limit, "partial": True,
                "not_following_back_in_sample": [u for u in following if str(u.get("pk")) not in follower_ids]}

    def pending(self, limit: int = 20) -> list[dict[str, Any]]:
        limit = bounded_limit(limit)
        return collection(self.client.user_follow_requests(amount=limit), limit)

    def blocked(self, limit: int = 20) -> list[dict[str, Any]]:
        limit = bounded_limit(limit)
        return collection(self.client.user_blocking(), limit)

    def posts(self, target: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        limit = bounded_limit(limit)
        pk = self.user_id(target) if target else self.own_id()
        return collection(self.client.user_medias(pk, amount=limit), limit, short_media)

    def stories(self, target: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        limit = bounded_limit(limit)
        pk = self.user_id(target) if target else self.own_id()
        return collection(self.client.user_stories(pk, amount=limit), limit, short_media)

    def highlights(self, target: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        limit = bounded_limit(limit)
        pk = self.user_id(target) if target else self.own_id()
        return collection(self.client.user_highlights(pk), limit, lambda obj: view(obj, PUBLIC_HIGHLIGHT_FIELDS))

    def saved(self, limit: int = 20) -> list[dict[str, Any]]:
        limit = bounded_limit(limit)
        return collection(self.client.collection_medias("saved", amount=limit), limit, short_media)

    def tagged(self, target: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        limit = bounded_limit(limit)
        pk = self.user_id(target) if target else self.own_id()
        return collection(self.client.usertag_medias(pk, amount=limit), limit, short_media)

    def story_viewers(self, pk: str, limit: int = 20) -> list[dict[str, Any]]:
        limit = bounded_limit(limit)
        pk = identifier(pk)
        own_story_ids = {str(item.get("pk")) for item in self.stories(limit=100)}
        if pk not in own_story_ids:
            raise IAMError("Only viewer lists for your own active stories can be viewed.")
        return collection(self.client.story_viewers(pk, amount=limit), limit)

    def highlight(self, pk: str) -> dict[str, Any]:
        return view(self.client.highlight_info(identifier(pk)), PUBLIC_HIGHLIGHT_FIELDS)

    def collections(self, limit: int = 20) -> list[dict[str, Any]]:
        limit = bounded_limit(limit)
        return collection(self.client.collections(), limit, lambda obj: view(obj, ("id", "name", "type", "media_count")))

    def liked(self, limit: int = 20) -> list[dict[str, Any]]:
        limit = bounded_limit(limit)
        return collection(self.client.liked_medias(amount=limit), limit, short_media)

    def media(self, pk: str) -> dict[str, Any]:
        return short_media(self.client.media_info(identifier(pk)))

    def _done(self, method: str, result: Any, **details: Any) -> dict[str, Any]:
        if result is False:
            raise IAMError(f"Instagram did not complete {method}.")
        return {"status": "ok", "action": method, **details}

    def follow(self, target: str) -> dict[str, Any]:
        return self._done("follow", self.client.user_follow(self.user_id(target)), username=username(target))

    def unfollow(self, target: str) -> dict[str, Any]:
        return self._done("unfollow", self.client.user_unfollow(self.user_id(target)), username=username(target))

    def block(self, target: str) -> dict[str, Any]:
        return self._done("block", self.client.user_block(self.user_id(target)), username=username(target))

    def unblock(self, target: str) -> dict[str, Any]:
        return self._done("unblock", self.client.user_unblock(self.user_id(target)), username=username(target))

    def approve(self, target: str) -> dict[str, Any]:
        return self._done("approve follow request", self.client.user_follow_request_approve(self.user_id(target)), username=username(target))

    def reject(self, target: str) -> dict[str, Any]:
        return self._done("reject follow request", self.client.user_follow_request_decline(self.user_id(target)), username=username(target))

    def remove_follower(self, target: str) -> dict[str, Any]:
        return self._done("remove follower", self.client.user_remove_follower(self.user_id(target)), username=username(target))

    def close_friend_add(self, target: str) -> dict[str, Any]:
        return self._done("add close friend", self.client.close_friend_add(self.user_id(target)), username=username(target))

    def close_friend_remove(self, target: str) -> dict[str, Any]:
        return self._done("remove close friend", self.client.close_friend_remove(self.user_id(target)), username=username(target))

    def notification(self, target: str, kind: str, state: str) -> dict[str, Any]:
        if kind not in {"posts", "reels", "stories", "videos"} or state not in {"on", "off"}:
            raise IAMError("Invalid notification type or state.")
        method = ("enable_" if state == "on" else "disable_") + kind + "_notifications"
        result = getattr(self.client, method)(self.user_id(target))
        return self._done(f"{state} {kind} notifications", result, username=username(target))

    def bio(self, text: str) -> dict[str, Any]:
        text = nonempty_text(text, max_length=150)
        return self._done("update bio", self.client.account_edit(biography=text))

    def photo(self, path: str, caption: str = "") -> dict[str, Any]:
        file = local_media(path)
        caption = caption.strip()
        if len(caption) > 2200:
            raise IAMError("Caption cannot exceed 2200 characters.")
        result = self.client.photo_upload(path=file, caption=caption)
        return self._done("upload photo", result, media_pk=str(field(result, "pk", "")))

    def reel(self, path: str, caption: str = "") -> dict[str, Any]:
        file = local_media(path, kind="video")
        if file.suffix.lower() != ".mp4":
            raise IAMError("Please convert reels to MP4 before uploading.")
        if len(caption) > 2200:
            raise IAMError("Caption cannot exceed 2200 characters.")
        result = self.client.clip_upload(path=file, caption=caption)
        return self._done("upload reel", result, media_pk=str(field(result, "pk", "")))

    def story(self, path: str) -> dict[str, Any]:
        file = local_media(path)
        result = self.client.photo_upload_to_story(path=file)
        return self._done("upload story", result, story_pk=str(field(result, "pk", "")))

    def avatar(self, path: str) -> dict[str, Any]:
        file = local_media(path)
        return self._done("change avatar", self.client.account_change_picture(file))

    def direct(self, target: str, message: str) -> dict[str, Any]:
        message = nonempty_text(message, max_length=1000)
        return self._done("send message", self.client.direct_send(message, [self.user_id(target)]), recipient=username(target))

    def _media_call(self, action: str, method: str, pk: str, *args: Any) -> dict[str, Any]:
        pk = identifier(pk)
        result = getattr(self.client, method)(pk, *args)
        return self._done(action, result, media_pk=pk)

    def like(self, pk: str) -> dict[str, Any]:
        return self._media_call("like", "media_like", pk)

    def unlike(self, pk: str) -> dict[str, Any]:
        return self._media_call("unlike", "media_unlike", pk)

    def save(self, pk: str) -> dict[str, Any]:
        return self._media_call("save", "media_save", pk)

    def unsave(self, pk: str) -> dict[str, Any]:
        return self._media_call("unsave", "media_unsave", pk)

    def comment(self, pk: str, text: str) -> dict[str, Any]:
        return self._media_call("comment", "media_comment", pk, nonempty_text(text))

    def delete(self, pk: str) -> dict[str, Any]:
        pk = identifier(pk)
        item = self.client.media_info(pk)
        owner = str(field(field(item, "user", {}), "pk", ""))
        if owner != self.own_id():
            raise IAMError("Refusing to delete media that is not owned by the signed-in account.")
        return self._media_call("delete media", "media_delete", pk)

    def download_media(self, pk: str, folder: str) -> dict[str, Any]:
        pk = identifier(pk)
        path = Path(folder).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        if path.is_symlink():
            raise IAMError("Refusing to save to a symlinked output directory.")
        result = self.client.media_download(pk, folder=path)
        return {"status": "ok", "saved_to": str(result)}

    def download_story(self, pk: str, folder: str) -> dict[str, Any]:
        pk = identifier(pk)
        # No anonymous/private-story bypass; API access is determined by Instagram.
        path = Path(folder).expanduser()
        if path.is_symlink():
            raise IAMError("Refusing to save to a symlinked output directory.")
        path.mkdir(parents=True, exist_ok=True)
        result = self.client.story_download(pk, folder=path)
        return {"status": "ok", "saved_to": str(result)}
