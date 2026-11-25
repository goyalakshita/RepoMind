
import pytest

from core.repository_history import RepositoryHistory


@pytest.fixture
def history(tmp_path):
    return RepositoryHistory(
        history_file=str(tmp_path / "repository_history.json")
    )


def test_initial_history_is_empty(history):
    assert history.get_repositories() == []


def test_add_repository(history, tmp_path):
    repo_path = tmp_path / "my_project"
    repo_path.mkdir()

    repository = history.add_repository(
        name="My Project",
        repository_path=repo_path,
        source_type="Local Folder"
    )

    assert repository["name"] == "My Project"
    assert repository["indexed"] is False
    assert len(history.get_repositories()) == 1


def test_update_existing_repository(history, tmp_path):
    repo_path = tmp_path / "project"
    repo_path.mkdir()

    first = history.add_repository(
        "Project",
        repo_path,
        "Local Folder"
    )

    second = history.add_repository(
        "Project",
        repo_path,
        "Local Folder"
    )

    assert first["id"] == second["id"]
    assert len(history.get_repositories()) == 1


def test_mark_indexed(history, tmp_path):
    repo_path = tmp_path / "project"
    repo_path.mkdir()

    repository = history.add_repository(
        "Project",
        repo_path,
        "Local Folder"
    )

    result = history.mark_indexed(
        repository["id"],
        "repomind_test",
        {
            "files_processed": 5,
            "chunks_created": 10,
            "chunks_stored": 10
        }
    )

    saved = history.get_repository(repository["id"])

    assert result is True
    assert saved["indexed"] is True
    assert saved["collection_name"] == "repomind_test"


def test_mark_unindexed(history, tmp_path):
    repo_path = tmp_path / "project"
    repo_path.mkdir()

    repository = history.add_repository(
        "Project",
        repo_path,
        "Local Folder"
    )

    history.mark_indexed(
        repository["id"],
        "repomind_test",
        {"chunks_stored": 10}
    )

    history.mark_unindexed(repository["id"])

    saved = history.get_repository(repository["id"])

    assert saved["indexed"] is False
    assert saved["index_stats"] is None


def test_delete_repository_record(history, tmp_path):
    repo_path = tmp_path / "project"
    repo_path.mkdir()

    repository = history.add_repository(
        "Project",
        repo_path,
        "Local Folder"
    )

    result = history.delete_repository_record(
        repository["id"]
    )

    assert result is True
    assert history.get_repositories() == []


def test_github_repository_identity(history, tmp_path):
    first = history.add_repository(
        "Example",
        tmp_path / "first",
        "GitHub",
        "https://github.com/user/example"
    )

    second = history.add_repository(
        "Example",
        tmp_path / "second",
        "GitHub",
        "https://github.com/user/example.git"
    )

    assert first["id"] == second["id"]
    assert len(history.get_repositories()) == 1

