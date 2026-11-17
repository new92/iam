import json
import pytest
from iam.cli import main, make_parser, private_output, json_value
from iam.errors import IAMError, public_error
from iam.settings import session_path


def run_login(client, tmp_path, capsys):
    code = main(["--username", "alice", "login"], home=tmp_path, client_factory=lambda: client,
                secret_input=lambda _: "mock-password")
    assert code == 0
    assert session_path("alice", tmp_path).exists()
    capsys.readouterr()


def test_doctor_no_network(tmp_path, capsys):
    def fail(): raise AssertionError("should never create client")
    assert main(["doctor"], client_factory=fail, home=tmp_path) == 0
    obj = json.loads(capsys.readouterr().out)
    assert obj["browser_cookie_import"] == "disabled"


def test_login_and_account(client, tmp_path, capsys):
    run_login(client, tmp_path, capsys)
    assert main(["account"], client_factory=lambda: client, home=tmp_path) == 0
    text = capsys.readouterr().out
    assert '"username": "alice"' in text
    assert "secret@example.org" not in text


def test_security_filtered(client, tmp_path, capsys):
    run_login(client, tmp_path, capsys)
    assert main(["security"], client_factory=lambda: client, home=tmp_path) == 0
    out = capsys.readouterr().out
    assert "PRIVATE" not in out and "totp_seeds" not in out


def test_dry_run_no_login_or_network(tmp_path, capsys):
    def fail(): raise AssertionError("should never create client")
    assert main(["--dry-run", "follow", "@bob"], client_factory=fail, home=tmp_path) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["dry_run"] and not data["will_contact_instagram"]


def test_write_requires_yes_in_non_tty(client, tmp_path, capsys):
    run_login(client, tmp_path, capsys)
    code = main(["follow", "bob"], client_factory=lambda: client, home=tmp_path)
    assert code == 2
    assert not any(c[0] == "user_follow" for c in client.calls)


def test_confirmed_write(client, tmp_path, capsys):
    run_login(client, tmp_path, capsys)
    assert main(["--yes", "follow", "bob"], client_factory=lambda: client, home=tmp_path) == 0
    assert ("user_follow", "200") in client.calls


def test_invalid_command_rejected_before_network(tmp_path, capsys):
    assert main(["--dry-run", "follow", "bad user"], home=tmp_path) == 2


def test_output_private(tmp_path):
    filename = tmp_path / "report.json"
    private_output({"name": "Alice"}, str(filename))
    assert json.loads(filename.read_text()) == {"name": "Alice"}
    with pytest.raises(IAMError): private_output({"x": 1}, str(filename))


def test_doctor_output_json(tmp_path):
    target = tmp_path / "diagnostics.json"
    assert main(["--output", str(target), "doctor"], home=tmp_path) == 0
    assert json.loads(target.read_text())["mode"] == "manual, user-confirmed actions"


def test_safe_error_message():
    assert "secret" not in public_error(RuntimeError("password=secret"))


def test_full_parser_support():
    p = make_parser()
    for args in (["followers", "bob", "--limit", "5"], ["photo", "image.jpg"],
                 ["download-story", "123"], ["comment", "42", "hello"], ["--yes", "bio", "hi"]):
        assert p.parse_args(args).command


def test_json_value_datetime():
    from datetime import datetime
    assert json_value({"time": datetime(2026, 1, 1)})["time"].startswith("2026")


def test_extras_appear_in_parser():
    p = make_parser()
    for args in (["notification", "bob", "posts", "on"], ["reel", "file.mp4"],
                 ["remove-follower", "bob"], ["close-friend-add", "bob"],
                 ["collections"], ["highlight", "701"]):
        assert p.parse_args(args).command
