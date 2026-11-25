
import json
import hashlib
import os
import tempfile

from pathlib import Path
from datetime import datetime, timezone


class RepositoryHistory:
    """
    Maintains persistent history of repositories
    loaded into RepoMind.
    """

    def __init__(self, history_file="data/repository_history.json"):
        self.history_file = Path(history_file)
        self.history_file.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        if not self.history_file.exists():
            self._save([])

    def _load(self):
        """Read repository history from JSON."""

        try:
            with self.history_file.open(
                "r",
                encoding="utf-8"
            ) as file:
                data = json.load(file)

            if not isinstance(data, list):
                raise ValueError("Invalid repository history format.")

            return data

        except json.JSONDecodeError:
            raise ValueError(
                "Repository history file is corrupted."
            )

    def _save(self, repositories):
        """Safely save history using an atomic file replacement."""

        temporary_path = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.history_file.parent,
                suffix=".tmp",
                delete=False
            ) as file:

                json.dump(
                    repositories,
                    file,
                    indent=4
                )

                temporary_path = file.name

            os.replace(
                temporary_path,
                self.history_file
            )

        finally:
            if (
                temporary_path
                and os.path.exists(temporary_path)
            ):
                os.unlink(temporary_path)

    @staticmethod
    def _generate_id(source_type, source_reference, repository_path):
        """
        Generate a stable ID for a repository.

        GitHub repositories use their URL.
        Other repositories use their resolved folder path.
        """

        if source_type.lower() == "github" and source_reference:
            identity = source_reference.strip().lower().rstrip("/")
            identity = identity.removesuffix(".git")
        else:
            identity = str(
                Path(repository_path).resolve()
            ).lower()

        unique_key = f"{source_type.lower()}|{identity}"

        return hashlib.sha256(
            unique_key.encode("utf-8")
        ).hexdigest()[:16]

    def add_repository(
        self,
        name,
        repository_path,
        source_type,
        source_reference=None
    ):
        """
        Add a repository to history.

        If it already exists, update its location
        and last-opened timestamp.
        """

        now = datetime.now(timezone.utc).isoformat()

        repository_id = self._generate_id(
            source_type,
            source_reference,
            repository_path
        )

        repositories = self._load()

        existing = next(
            (
                repo for repo in repositories
                if repo["id"] == repository_id
            ),
            None
        )

        if existing:

            existing["name"] = name
            existing["path"] = str(
                Path(repository_path).resolve()
            )
            existing["source_type"] = source_type
            existing["source_reference"] = source_reference
            existing["last_opened_at"] = now

            record = existing

        else:

            record = {
                "id": repository_id,
                "name": name,
                "path": str(Path(repository_path).resolve()),
                "source_type": source_type,
                "source_reference": source_reference,
                "loaded_at": now,
                "last_opened_at": now,
                "indexed": False,
                "collection_name": None,
                "index_stats": None
            }

            repositories.append(record)

        self._save(repositories)

        return record.copy()

    def get_repositories(self):
        """Return all repositories, newest activity first."""

        repositories = self._load()

        return sorted(
            repositories,
            key=lambda repo: repo.get("last_opened_at", ""),
            reverse=True
        )

    def get_repository(self, repository_id):
        """Find a repository using its unique ID."""

        for repository in self._load():

            if repository["id"] == repository_id:
                return repository

        return None

    def mark_indexed(
        self,
        repository_id,
        collection_name,
        index_stats
    ):
        """Save indexing information for a repository."""

        repositories = self._load()

        for repository in repositories:

            if repository["id"] == repository_id:

                repository["indexed"] = True
                repository["collection_name"] = collection_name
                repository["index_stats"] = index_stats

                self._save(repositories)

                return True

        return False

    def mark_unindexed(self, repository_id):
        """Mark a repository as not indexed."""

        repositories = self._load()

        for repository in repositories:

            if repository["id"] == repository_id:

                repository["indexed"] = False
                repository["index_stats"] = None

                self._save(repositories)

                return True

        return False

    def delete_repository_record(self, repository_id):
        """
        Remove a repository from history.

        This only removes its history record.
        It does not delete repository files or ChromaDB data.
        """

        repositories = self._load()

        updated_repositories = [
            repo for repo in repositories
            if repo["id"] != repository_id
        ]

        if len(updated_repositories) == len(repositories):
            return False

        self._save(updated_repositories)

        return True
