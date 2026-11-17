import pytest
from iam.errors import IAMError


def test_account_allowlist(mgr, client):
    client.active = True
    profile = mgr.account()
    assert profile["username"] == "alice"
    assert "email" not in profile and "password" not in profile


def test_security_does_not_leak_secrets(mgr):
    sec = mgr.security()
    assert sec["is_two_factor_enabled"] is True
    assert "backup_codes" not in sec and "totp_seeds" not in sec


def test_profile_lookup_filters_private_values(mgr):
    user = mgr.user("@bob")
    assert user["username"] == "bob"
    assert "private_phone" not in user


def test_followers_bounded(mgr, client):
    result = mgr.followers(limit=10)
    assert result == [{"pk": "1", "username": "bobby", "full_name": "Bobby"}]
    assert ("user_followers", "100", 10) in client.calls
    with pytest.raises(IAMError): mgr.followers(limit=999999)


def test_sampled_nonfollowers_is_partial(mgr):
    result = mgr.not_following_back(10)
    assert result["partial"] is True
    assert result["not_following_back_in_sample"][0]["username"] == "cindy"


def test_collections(mgr):
    assert mgr.pending()[0]["username"] == "pending"
    assert mgr.blocked()[0]["username"] == "blocked"
    assert mgr.posts()[0]["pk"] == "501"
    assert mgr.stories()[0]["pk"] == "601"
    assert mgr.highlights()[0]["title"] == "Vacation"
    assert mgr.saved()[0]["pk"] == "801"
    assert mgr.tagged()[0]["pk"] == "802"


def test_story_viewers_are_own_stories_only(mgr):
    assert mgr.story_viewers("601")[0]["username"] == "viewer"
    with pytest.raises(IAMError): mgr.story_viewers("602")


@pytest.mark.parametrize("action", ["follow", "unfollow", "block", "unblock", "approve", "reject"])
def test_single_user_actions(mgr, client, action):
    res = getattr(mgr, action)("bob")
    assert res["status"] == "ok"
    assert res["username"] == "bob"


def test_media_actions(mgr):
    for action in ("like", "unlike", "save", "unsave", "delete"):
        assert getattr(mgr, action)("501")["status"] == "ok"
    assert mgr.comment("501", "Thanks!")["action"] == "comment"
    with pytest.raises(IAMError): mgr.comment("501", " ")


def test_delete_refuses_other_users_media(mgr, client):
    client.media_info = lambda pk: {"pk": pk, "user": {"pk": "999"}}
    with pytest.raises(IAMError, match="not owned"):
        mgr.delete("101")
    assert not any(c[0] == "media_delete" for c in client.calls)


def test_bio_and_dm(mgr, client):
    assert mgr.bio("Hello")["status"] == "ok"
    assert mgr.direct("bob", "Hello Bob")["recipient"] == "bob"
    assert ("direct_send", "Hello Bob", ["200"]) in client.calls


def test_photo_story_avatar(mgr, tmp_path):
    f = tmp_path / "image.jpg"; f.write_bytes(b"image")
    assert mgr.photo(str(f), "caption")["media_pk"] == "900"
    assert mgr.story(str(f))["story_pk"] == "901"
    assert mgr.avatar(str(f))["status"] == "ok"


def test_media_download(mgr, tmp_path):
    dest = tmp_path / "downloads"
    assert mgr.download_media("100", str(dest))["status"] == "ok"
    assert mgr.download_story("100", str(dest))["status"] == "ok"


def test_no_arbitrary_serialization():
    from iam.cli import json_value
    assert json_value(object()) == "[unsupported value]"


def test_new_features_with_fake_client(mgr, client, tmp_path):
    client.collections = lambda: [{"id": "1", "name": "Travel", "media_count": 3, "secret": "PRIVATE"}]
    client.liked_medias = lambda amount: [{"pk": "10", "user": {"pk": "100"}}]
    client.highlight_info = lambda pk: {"pk": pk, "title": "My trip"}
    client.user_remove_follower = lambda pk: True
    client.close_friend_add = lambda pk: True
    client.close_friend_remove = lambda pk: True
    client.enable_posts_notifications = lambda pk: True
    assert mgr.collections()[0]["name"] == "Travel"
    assert "secret" not in mgr.collections()[0]
    assert mgr.liked()[0]["pk"] == "10"
    assert mgr.highlight("701")["title"] == "My trip"
    assert mgr.remove_follower("bob")["status"] == "ok"
    assert mgr.close_friend_add("bob")["status"] == "ok"
    assert mgr.close_friend_remove("bob")["status"] == "ok"
    assert mgr.notification("bob", "posts", "on")["status"] == "ok"
    file = tmp_path / "video.mp4"; file.write_bytes(b"video")
    client.clip_upload = lambda **kwargs: {"pk": "901"}
    assert mgr.reel(str(file), "caption")["media_pk"] == "901"


def test_notifications_invalid_type(mgr):
    with pytest.raises(IAMError): mgr.notification("bob", "fake", "on")
