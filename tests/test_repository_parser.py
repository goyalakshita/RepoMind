
from core.repository_loader import get_repository_files
from core.code_parser import parse_repository


def test_repository_loader_and_parser(tmp_path):

    # Create a sample repository
    (tmp_path / "auth.py").write_text(
        """
def authenticate(username, password):
    return username == "admin"


class AuthHandler:

    def generate_token(self, user_id):
        return str(user_id)
"""
    )

    (tmp_path / "README.md").write_text(
        "# Sample Repository"
    )

    # Step 1: Find repository files
    files = get_repository_files(tmp_path)

    # Step 2: Parse Python files
    chunks = parse_repository(tmp_path, files)

    # Verify extracted components
    names = [chunk["name"] for chunk in chunks]

    assert "authenticate" in names
    assert "AuthHandler" in names
    assert "generate_token" in names

    assert len(chunks) == 3


