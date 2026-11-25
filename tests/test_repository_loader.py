
from pathlib import Path

from core.repository_loader import (
    load_local_repository,
    get_repository_files,
    get_repository_summary
)


def test_load_local_repository(tmp_path):

    folder = load_local_repository(tmp_path)

    assert folder.exists()
    assert folder.is_dir()


def test_get_repository_files(tmp_path):

    (tmp_path / "main.py").write_text(
        "print('Hello RepoMind')"
    )

    (tmp_path / "README.md").write_text(
        "# Sample Project"
    )

    (tmp_path / ".env").write_text(
        "SECRET_KEY=123"
    )

    (tmp_path / ".venv").mkdir()

    (tmp_path / ".venv" / "test.py").write_text(
        "print('Ignore me')"
    )

    files = get_repository_files(tmp_path)

    filenames = [file.name for file in files]

    assert "main.py" in filenames
    assert "README.md" in filenames
    assert ".env" not in filenames
    assert "test.py" not in filenames


def test_repository_summary(tmp_path):

    (tmp_path / "main.py").write_text(
        "print('Hello')"
    )

    summary = get_repository_summary(tmp_path)

    assert summary["total_files"] == 1
    assert summary["file_types"][".py"] == 1
