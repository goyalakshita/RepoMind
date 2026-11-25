
import os
import re
import shutil
import tempfile
import zipfile

from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

from git import Repo


# Directories that should not be scanned
IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".idea",
    ".vscode",
    "chroma_db",
    ".pytest_cache",
    "site-packages"
}

# File extensions that RepoMind can analyze
SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx",
    ".java", ".c", ".cpp", ".h", ".hpp",
    ".cs", ".go", ".rs", ".php",
    ".html", ".css", ".sql",
    ".md", ".txt", ".json", ".yaml",
    ".yml", ".toml", ".sh"
}

# Files and patterns containing unnecessary or sensitive data
IGNORED_FILES = {
    ".env",
    ".env.local",
    ".env.production",
    ".gitignore",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml"
}

MAX_FILE_SIZE = 1 * 1024 * 1024  # 1 MB
MAX_ZIP_SIZE = 500 * 1024 * 1024  # 500 MB


def clone_github_repository(repo_url, destination_root):
    """
    Clone a public GitHub repository.

    Args:
        repo_url: GitHub repository URL.
        destination_root: Folder where repository will be stored.

    Returns:
        Path of the cloned repository.
    """

    parsed_url = urlparse(repo_url)

    if parsed_url.scheme != "https":
        raise ValueError("Only HTTPS GitHub URLs are supported.")

    if parsed_url.hostname not in {"github.com", "www.github.com"}:
        raise ValueError("Please provide a valid GitHub URL.")

    parts = [part for part in parsed_url.path.strip("/").split("/") if part]

    if len(parts) != 2:
        raise ValueError(
            "Provide a repository URL in the format "
            "https://github.com/owner/repository"
        )

    owner, repo_name = parts

    repo_name = repo_name.removesuffix(".git")

    if not re.fullmatch(r"[A-Za-z0-9_.-]+", repo_name):
        raise ValueError("Invalid repository name.")

    destination_root = Path(destination_root)
    destination_root.mkdir(parents=True, exist_ok=True)

    repository_path = Path(
        tempfile.mkdtemp(
            prefix=f"{repo_name}_",
            dir=destination_root
        )
    )

    try:
        Repo.clone_from(
            f"https://github.com/{owner}/{repo_name}.git",
            str(repository_path),
            depth=1
        )

        return repository_path

    except Exception:
        shutil.rmtree(repository_path, ignore_errors=True)
        raise


def extract_zip_file(zip_path, destination_root):
    """
    Safely extract a repository ZIP file.

    Prevents ZIP path traversal and oversized archives.

    Returns:
        Path of the extracted repository.
    """

    zip_path = Path(zip_path)
    destination_root = Path(destination_root)

    if not zipfile.is_zipfile(zip_path):
        raise ValueError("The uploaded file is not a valid ZIP archive.")

    destination_root.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as archive:

        total_size = sum(
            info.file_size for info in archive.infolist()
        )

        if total_size > MAX_ZIP_SIZE:
            raise ValueError("ZIP archive exceeds the 500 MB limit.")

        if len(archive.infolist()) > 20000:
            raise ValueError("ZIP archive contains too many entries.")

        extraction_path = Path(
            tempfile.mkdtemp(
                prefix="uploaded_repo_",
                dir=destination_root
            )
        )

        try:
            root = extraction_path.resolve()

            for info in archive.infolist():

                member = PurePosixPath(info.filename)

                if member.is_absolute() or ".." in member.parts:
                    raise ValueError("Unsafe path found inside ZIP archive.")

                target = (root / Path(*member.parts)).resolve()

                if not target.is_relative_to(root):
                    raise ValueError("Invalid ZIP extraction path.")

                # Reject symbolic links
                mode = info.external_attr >> 16

                if (mode & 0o170000) == 0o120000:
                    raise ValueError("Symbolic links are not allowed.")

                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue

                target.parent.mkdir(parents=True, exist_ok=True)

                with archive.open(info) as source:
                    with target.open("wb") as destination:
                        shutil.copyfileobj(source, destination)

            return extraction_path

        except Exception:
            shutil.rmtree(extraction_path, ignore_errors=True)
            raise


def load_local_repository(folder_path):
    """
    Validate and return an existing local repository folder.
    """

    folder_path = Path(folder_path).expanduser().resolve()

    if not folder_path.exists():
        raise FileNotFoundError("Repository folder does not exist.")

    if not folder_path.is_dir():
        raise ValueError("The supplied path is not a directory.")

    return folder_path


def get_repository_files(repository_path):
    """
    Find supported source files in a repository.

    Ignores unnecessary directories, files and oversized files.

    Returns:
        List of source file paths.
    """

    repository_path = Path(repository_path).resolve()

    if not repository_path.is_dir():
        raise ValueError("Invalid repository directory.")

    source_files = []

    for root, directories, files in os.walk(repository_path):

        # Remove ignored directories from traversal
        directories[:] = [
            directory
            for directory in directories
            if directory not in IGNORED_DIRS
        ]

        for filename in files:

            file_path = Path(root) / filename

            if filename in IGNORED_FILES:
                continue

            if filename.startswith(".env"):
                continue

            if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue

            try:
                if file_path.stat().st_size > MAX_FILE_SIZE:
                    continue

                source_files.append(file_path)

            except OSError:
                continue

    return source_files


def get_repository_summary(repository_path):
    """
    Return basic repository information.
    """

    source_files = get_repository_files(repository_path)

    extensions = {}

    for file_path in source_files:
        extension = file_path.suffix.lower()

        extensions[extension] = extensions.get(extension, 0) + 1

    return {
        "repository_path": str(Path(repository_path).resolve()),
        "total_files": len(source_files),
        "file_types": extensions,
        "files": source_files
    }
