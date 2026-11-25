
import ast
from pathlib import Path


def parse_python_file(file_path, repository_root=None):
    """
    Extract functions, classes and methods from a Python file.
    """

    file_path = Path(file_path)

    try:
        source_code = file_path.read_text(
            encoding="utf-8",
            errors="replace"
        )

        tree = ast.parse(source_code)

    except (SyntaxError, OSError, ValueError) as error:
        print(f"Error parsing {file_path}: {error}")
        return []

    lines = source_code.splitlines()

    if repository_root:
        relative_path = str(
            file_path.relative_to(Path(repository_root).resolve())
        )
    else:
        relative_path = str(file_path)

    extracted_chunks = []

    def get_source(node):
        start = min(
            [node.lineno] +
            [d.lineno for d in getattr(node, "decorator_list", [])]
        )

        end = node.end_lineno

        return "\n".join(lines[start - 1:end])

    # Extract top-level functions and classes
    for node in tree.body:

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):

            extracted_chunks.append({
                "type": "function",
                "name": node.name,
                "class_name": None,
                "file_path": relative_path,
                "start_line": node.lineno,
                "end_line": node.end_lineno,
                "parameters": [
                    arg.arg for arg in node.args.args
                ],
                "code": get_source(node)
            })

        elif isinstance(node, ast.ClassDef):

            extracted_chunks.append({
                "type": "class",
                "name": node.name,
                "class_name": None,
                "file_path": relative_path,
                "start_line": node.lineno,
                "end_line": node.end_lineno,
                "parameters": [],
                "code": get_source(node)
            })

            # Extract methods inside the class
            for child in node.body:

                if isinstance(
                    child,
                    (ast.FunctionDef, ast.AsyncFunctionDef)
                ):

                    extracted_chunks.append({
                        "type": "method",
                        "name": child.name,
                        "class_name": node.name,
                        "file_path": relative_path,
                        "start_line": child.lineno,
                        "end_line": child.end_lineno,
                        "parameters": [
                            arg.arg for arg in child.args.args
                        ],
                        "code": get_source(child)
                    })

    return extracted_chunks


def parse_repository(repository_path, files=None):
    """
    Parse all Python files in a repository.
    """

    repository_path = Path(repository_path).resolve()

    if files is None:
        files = list(repository_path.rglob("*.py"))

    all_chunks = []

    for file_path in files:

        if Path(file_path).suffix.lower() != ".py":
            continue

        chunks = parse_python_file(
            file_path,
            repository_root=repository_path
        )

        all_chunks.extend(chunks)

    return all_chunks
