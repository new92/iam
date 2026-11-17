"""In-memory facsimile of the Instagram client; tests never contact Instagram."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace as NS
import pytest


class FakeClient:
    def __init__(self):
        self.calls = []
        self.active = False
        self.error = None
        self.user_id = "100"

    def login(self, user, password, **kwargs):
        self.calls.append(("login", user, kwargs))
        self.active = True
        return True

    def load_settings(self, filename):
        self.calls.append(("load_settings", filename))
        json.loads(Path(filename).read_text())
        self.active = True

    def dump_settings(self, filename):
        self.calls.append(("dump_settings", filename))
        Path(filename).write_text(json.dumps({"cookies": {"sessionid": "fake-test-token"}}))

    def account_info(self):
        self.calls.append(("account_info",))
        if not self.active:
            raise RuntimeError("not authenticated")
        return NS(pk="100", username="alice", full_name="Alice", biography="test", follower_count=10,
                  email="secret@example.org", password="do-not-print")

    def account_security_info(self):
        return {"is_two_factor_enabled": True, "backup_codes": ["PRIVATE"],
                "totp_seeds": ["PRIVATE"], "has_reachable_email": True}

    def user_id_from_username(self, username):
        self.calls.append(("user_id_from_username", username))
        return "100" if username == "alice" else "200"

    def username_from_user_id(self, pk):
        return "alice" if pk == "100" else "bob"

    def user_info_by_username(self, username):
        return {"pk": "200", "username": username, "full_name": "Bob", "private_phone": "PRIVATE"}

    def user_followers(self, pk, amount):
        self.calls.append(("user_followers", pk, amount))
        return {"1": NS(pk="1", username="bobby", full_name="Bobby", token="PRIVATE")}

    def user_following(self, pk, amount):
        self.calls.append(("user_following", pk, amount))
        return {"2": NS(pk="2", username="cindy", full_name="Cindy")}

    def user_follow_requests(self, amount):
        return [NS(pk="3", username="pending")]

    def user_blocking(self):
        return [NS(pk="4", username="blocked")]

    def user_medias(self, pk, amount):
        return [NS(pk="501", code="CODE", media_type=1, user=NS(pk=pk, username="alice"))]

    def user_stories(self, pk, amount):
        return [NS(pk="601", media_type=1, user=NS(pk=pk, username="alice"))]

    def user_highlights(self, pk):
        return [NS(pk="701", title="Vacation", secret="PRIVATE")]

    def collection_medias(self, *args, **kwargs):
        return [NS(pk="801", user=NS(pk="100"))]

    def usertag_medias(self, pk, amount):
        return [NS(pk="802", user=NS(pk="100"))]

    def story_viewers(self, pk, amount):
        return [NS(pk="8", username="viewer")]

    def media_info(self, pk):
        return NS(pk=pk, user=NS(pk="100", username="alice"))

    def user_follow(self, pk):
        self.calls.append(("user_follow", pk)); return True

    def user_unfollow(self, pk):
        self.calls.append(("user_unfollow", pk)); return True

    def user_block(self, pk):
        self.calls.append(("user_block", pk)); return True

    def user_unblock(self, pk):
        self.calls.append(("user_unblock", pk)); return True

    def user_follow_request_approve(self, pk):
        self.calls.append(("friendships_approve", pk)); return True

    def user_follow_request_decline(self, pk):
        self.calls.append(("friendships_reject", pk)); return True

    def account_edit(self, **kwargs):
        self.calls.append(("account_edit", kwargs)); return True

    def account_change_picture(self, path):
        self.calls.append(("account_change_picture", path)); return True

    def photo_upload(self, path, caption):
        self.calls.append(("photo_upload", path, caption)); return NS(pk="900")

    def photo_upload_to_story(self, path):
        self.calls.append(("photo_upload_to_story", path)); return NS(pk="901")

    def direct_send(self, message, user_ids):
        self.calls.append(("direct_send", message, user_ids)); return NS(pk="1000")

    def media_like(self, pk):
        self.calls.append(("media_like", pk)); return True

    def media_unlike(self, pk):
        self.calls.append(("media_unlike", pk)); return True

    def media_save(self, pk):
        self.calls.append(("media_save", pk)); return True

    def media_unsave(self, pk):
        self.calls.append(("media_unsave", pk)); return True

    def media_comment(self, pk, text):
        self.calls.append(("media_comment", pk, text)); return True

    def media_delete(self, pk):
        self.calls.append(("media_delete", pk)); return True

    def media_download(self, pk, folder):
        self.calls.append(("media_download", pk, folder)); return str(folder / "media.jpg")

    def story_download(self, pk, folder):
        self.calls.append(("story_download", pk, folder)); return str(folder / "story.jpg")


@pytest.fixture
def client():
    return FakeClient()


@pytest.fixture
def mgr(client):
    from iam.operations import AccountManager
    return AccountManager(client, "alice")
