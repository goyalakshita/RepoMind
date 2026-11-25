
from pathlib import Path
from core.repository_loader import (
    clone_github_repository,
    extract_zip_file,
    get_repository_summary
)

# Change this to a small public GitHub repository
GITHUB_URL = "https://github.com/psf/requests"

if __name__ == "__main__":

    output_folder = Path("data/repositories")

    print("Testing GitHub repository ingestion...")

    repo_path = clone_github_repository(
        GITHUB_URL,
        output_folder
    )

    print("\nRepository downloaded successfully!")

    summary = get_repository_summary(repo_path)

    print("Total supported files:", summary["total_files"])
    print("File types:", summary["file_types"])

    print("\nFiles found:")

    for file in summary["files"]:
        print(file.relative_to(repo_path))
