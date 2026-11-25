import os
import ast
import chromadb
from sentence_transformers import SentenceTransformer


REPO_PATH = "sample_repo"


# Load embedding model
print("=" * 60)
print("RepoMind - Milestone 1 Prototype")
print("=" * 60)

print("\n[1] Loading repository...")

model = SentenceTransformer("all-MiniLM-L6-v2")


# Extract functions from Python files
def extract_functions(file_path):

    with open(file_path, "r", encoding="utf-8") as file:
        code = file.read()

    tree = ast.parse(code)

    functions = []

    for node in ast.walk(tree):

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):

            function_code = ast.get_source_segment(code, node)

            functions.append({
                "name": node.name,
                "code": function_code
            })

    return functions


# Process repository
documents = []
metadatas = []
ids = []

chunk_id = 0

for root, dirs, files in os.walk(REPO_PATH):

    for filename in files:

        if filename.endswith(".py"):

            file_path = os.path.join(root, filename)

            functions = extract_functions(file_path)

            print(
                f"    ✓ {filename}: "
                f"{len(functions)} function(s)"
            )

            for function in functions:

                documents.append(function["code"])

                metadatas.append({
                    "file": filename,
                    "function": function["name"]
                })

                ids.append(str(chunk_id))

                chunk_id += 1


print(f"\n[2] Total chunks extracted: {len(documents)}")


# Generate embeddings
print("\n[3] Generating embeddings...")

embeddings = model.encode(documents).tolist()

print("    ✓ Embeddings generated")


# Create ChromaDB
print("\n[4] Loading chunks into ChromaDB...")

client = chromadb.PersistentClient(
    path="./chroma_db"
)

# Delete old collection if it exists
try:
    client.delete_collection("repomind")
except:
    pass

collection = client.create_collection(
    name="repomind"
)


collection.add(
    ids=ids,
    documents=documents,
    embeddings=embeddings,
    metadatas=metadatas
)

print(
    f"    ✓ Vector store contains "
    f"{len(documents)} chunks"
)


# Ask question
query = input(
    "\n[5] Ask RepoMind a question:\n> "
)


print("\n[6] Retrieving relevant code...")


query_embedding = model.encode(
    [query]
).tolist()[0]


results = collection.query(
    query_embeddings=[query_embedding],
    n_results=3
)


print("\n" + "-" * 60)
print("RETRIEVED RESULTS")
print("-" * 60)


for i in range(len(results["documents"][0])):

    metadata = results["metadatas"][0][i]
    document = results["documents"][0][i]

    print(f"\nMatch {i + 1}")
    print(
        f"File: {metadata['file']}"
    )
    print(
        f"Function: {metadata['function']}"
    )

    print("\nCode:")
    print(document)


print("\n" + "=" * 60)
print("RepoMind Retrieval Completed")
print("=" * 60)