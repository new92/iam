import json
import os
import pytest
from iam.errors import IAMError
from iam.session import SessionManager
from iam.settings import private_dir, save_selected_user, selected_user, session_path


def test_login_restore_logout(client, tmp_path):
    store = SessionManager(home=tmp_path, client_factory=lambda: client)
    store.login("Alice", "test-password")
    file = session_path("alice", tmp_path)
    assert file.is_file()
    assert selected_user(tmp_path) == "alice"
    assert json.loads(file.read_text())["cookies"]["sessionid"] == "fake-test-token"
    assert store.restore("alice") is client
    store.logout("alice")
    assert not file.exists()


def test_unavailable_session(client, tmp_path):
    store = SessionManager(home=tmp_path, client_factory=lambda: client)
    with pytest.raises(IAMError): store.restore("alice")


def test_empty_password_rejected(client, tmp_path):
    with pytest.raises(IAMError): SessionManager(home=tmp_path, client_factory=lambda: client).login("alice", "")


def test_symlink_session_rejected(client, tmp_path):
    root = private_dir(tmp_path / "sessions")
    real = tmp_path / "other.json"; real.write_text("{}")
    (root / "alice.json").symlink_to(real)
    with pytest.raises(IAMError): SessionManager(home=tmp_path, client_factory=lambda: client).login("alice", "test")


def test_symlinked_directory_rejected(tmp_path):
    actual = tmp_path / "actual"; actual.mkdir()
    folder = tmp_path / "link"; folder.symlink_to(actual)
    with pytest.raises(IAMError): private_dir(folder)


def test_permissions_on_posix(client, tmp_path):
    store = SessionManager(home=tmp_path, client_factory=lambda: client)
    store.login("alice", "test")
    if os.name == "posix":
        assert session_path("alice", tmp_path).stat().st_mode & 0o777 == 0o600
        assert (tmp_path / "sessions").stat().st_mode & 0o777 == 0o700


def test_preferences_invalid_json(tmp_path):
    (tmp_path / "preferences.json").write_text("NOT JSON")
    with pytest.raises(IAMError): selected_user(tmp_path)


def test_preferences_roundtrip(tmp_path):
    save_selected_user("Alice", tmp_path)
    assert selected_user(tmp_path) == "alice"


def test_restore_refuses_account_mismatch(client, tmp_path):
    store = SessionManager(home=tmp_path, client_factory=lambda: client)
    store.login("bob", "test")
    with pytest.raises(IAMError, match="does not belong"):
        store.restore("bob")
