
from core.code_parser import parse_python_file


def test_function_extraction(tmp_path):

    file = tmp_path / "sample.py"

    file.write_text(
        """
def authenticate(username, password):
    return username == "admin"
"""
    )

    chunks = parse_python_file(file)

    assert len(chunks) == 1
    assert chunks[0]["name"] == "authenticate"
    assert chunks[0]["type"] == "function"
    assert "username" in chunks[0]["parameters"]


def test_class_and_method_extraction(tmp_path):

    file = tmp_path / "auth.py"

    file.write_text(
        """
class AuthHandler:

    def generate_token(self, user_id):
        return str(user_id)
"""
    )

    chunks = parse_python_file(file)

    assert len(chunks) == 2
    assert chunks[0]["type"] == "class"
    assert chunks[1]["type"] == "method"
    assert chunks[1]["class_name"] == "AuthHandler"


def test_invalid_python_file(tmp_path):

    file = tmp_path / "broken.py"

    file.write_text("def broken(:\n")

    chunks = parse_python_file(file)

    assert chunks == []
