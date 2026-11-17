import pytest
from iam.errors import IAMError
from iam.validation import username, identifier, bounded_limit, nonempty_text, local_media


@pytest.mark.parametrize("value, expected", [("Alice", "alice"), ("@john_doe", "john_doe"),
                                            ("  New.User  ", "new.user"), ("x" * 30, "x" * 30)])
def test_username_valid(value, expected):
    assert username(value) == expected


@pytest.mark.parametrize("value", ["", "a..b", ".abc", "abc.", "!bad", "a b", "x" * 31, "@"])
def test_username_invalid(value):
    with pytest.raises(IAMError): username(value)


@pytest.mark.parametrize("value", ["0", "-1", "1e4", "x", "1.1", ""])
def test_invalid_id(value):
    with pytest.raises(IAMError): identifier(value)


def test_valid_id():
    assert identifier("15") == "15"


@pytest.mark.parametrize("value", [0, -1, 101, 999])
def test_invalid_limit(value):
    with pytest.raises(IAMError): bounded_limit(value)


def test_valid_limit():
    assert bounded_limit(100) == 100


def test_text_length():
    with pytest.raises(IAMError): nonempty_text(" ")
    with pytest.raises(IAMError): nonempty_text("a" * 151, max_length=150)
    assert nonempty_text(" hi ") == "hi"


def test_local_media(tmp_path):
    photo = tmp_path / "photo.jpg"
    photo.write_bytes(b"x")
    assert local_media(str(photo)) == photo.resolve()
    with pytest.raises(IAMError): local_media(str(tmp_path / "missing.jpg"))
    wrong = tmp_path / "script.py"; wrong.write_text("hi")
    with pytest.raises(IAMError): local_media(str(wrong))


def test_symlink_media_rejected(tmp_path):
    file = tmp_path / "real.jpg"; file.write_bytes(b"x")
    sym = tmp_path / "sym.jpg"; sym.symlink_to(file)
    with pytest.raises(IAMError): local_media(str(sym))
