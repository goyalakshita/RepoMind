
from pathlib import Path

from core.repository_loader import get_repository_files
from core.code_parser import parse_repository
from core.embeddings import EmbeddingGenerator
from core.vector_store import VectorStore
from core.retriever import CodeRetriever
from core.llm_handler import LLMHandler
from core.repository_history import RepositoryHistory


class RAGPipeline:
    """
    Complete Retrieval-Augmented Generation pipeline
    for understanding software repositories.

    Each repository gets its own ChromaDB collection.
    Repository details are saved in persistent history.
    """

    def __init__(self, persist_directory="chroma_db"):
        self.embedding_generator = EmbeddingGenerator()

        self.vector_store = VectorStore(
            persist_directory=persist_directory
        )

        self.retriever = CodeRetriever(
            vector_store=self.vector_store,
            embedding_generator=self.embedding_generator
        )

        self.llm_handler = LLMHandler()

        self.repository_history = RepositoryHistory()

        self.repository_path = None
        self.repository_id = None

    def _get_repository_record(
        self,
        repository_path,
        repository_name=None,
        source_type="local",
        source_reference=None
    ):
        """
        Find or create a repository history record.
        """

        repository_path = str(Path(repository_path).resolve())

        record = self.repository_history.add_repository(
            name=repository_name or Path(repository_path).name,
            repository_path=repository_path,
            source_type=source_type,
            source_reference=source_reference
        )

        return record

    def select_repository(self, repository_id):
        """
        Select a previously saved repository and its collection.
        """

        repository = self.repository_history.get_repository(
            repository_id
        )

        if not repository:
            raise ValueError("Repository not found in history.")

        repository_path = repository.get("path")

        if not repository_path or not Path(repository_path).exists():
            raise ValueError(
                "The repository folder could not be found. "
                "Please load the repository again."
            )

        collection_name = repository.get("collection_name")

        if not collection_name:
            collection_name = f"repomind_{repository_id}"

        if hasattr(self.vector_store, "set_collection"):
            self.vector_store.set_collection(collection_name)

        self.repository_path = repository_path
        self.repository_id = repository_id

        return repository

    def index_repository(
        self,
        repository_path,
        repository_id=None,
        repository_name=None,
        source_type="local",
        source_reference=None
    ):
        """
        Parse a repository, generate embeddings,
        and store code chunks in its own collection.
        """

        repository_path = str(Path(repository_path).resolve())

        print("Reading repository files...")

        files = get_repository_files(repository_path)

        if not files:
            raise ValueError(
                "No supported source files found in the repository."
            )

        print(f"Found {len(files)} supported files.")

        print("Parsing repository code...")

        chunks = parse_repository(
            repository_path,
            files
        )

        if not chunks:
            raise ValueError(
                "No Python functions or classes could be extracted."
            )

        print(f"Extracted {len(chunks)} code chunks.")

        # Find or create the repository history record.
        if repository_id:
            repository = self.repository_history.get_repository(
                repository_id
            )

            if not repository:
                raise ValueError(
                    "Repository ID was not found in history."
                )

            self.repository_id = repository_id

        else:
            repository = self._get_repository_record(
                repository_path=repository_path,
                repository_name=repository_name,
                source_type=source_type,
                source_reference=source_reference
            )

            self.repository_id = repository["id"]

        # Create a separate collection for this repository.
        collection_name = f"repomind_{self.repository_id}"

        if hasattr(self.vector_store, "set_collection"):
            self.vector_store.set_collection(collection_name)

        self.repository_path = repository_path

        print("Generating embeddings...")

        texts = [
            f"{chunk['type']} {chunk['name']}\n{chunk['code']}"
            for chunk in chunks
        ]

        embeddings = self.embedding_generator.generate_embeddings(
            texts
        )

        print("Storing code in ChromaDB...")

        # Clear only the currently selected repository's collection.
        self.vector_store.clear_collection()

        self.vector_store.add_chunks(
            chunks,
            embeddings
        )

        index_stats = {
            "files_processed": len(files),
            "chunks_created": len(chunks),
            "chunks_stored": self.vector_store.get_collection_count()
        }

        # Save successful indexing information.
        self.repository_history.mark_indexed(
            repository_id=self.repository_id,
            collection_name=collection_name,
            index_stats=index_stats
        )

        print("Repository indexed successfully!")

        return index_stats

    def ask_question(self, query, n_results=5):
        """
        Answer a natural-language question
        using the currently selected repository.
        """

        if not self.repository_path:
            raise ValueError(
                "Please select or index a repository before asking questions."
            )

        print("Searching for relevant code...")

        retrieved_chunks = self.retriever.retrieve(
            query,
            n_results=n_results
        )

        if not retrieved_chunks:
            return {
                "answer": (
                    "No relevant code was found for this question."
                ),
                "sources": []
            }

        print("Generating answer using Gemini...")

        answer = self.llm_handler.generate_answer(
            query,
            retrieved_chunks
        )

        sources = []

        for chunk in retrieved_chunks:
            metadata = chunk.get("metadata", {})

            sources.append({
                "file_path": metadata.get("file_path"),
                "name": metadata.get("name"),
                "start_line": metadata.get("start_line"),
                "end_line": metadata.get("end_line")
            })

        return {
            "answer": answer,
            "sources": sources
        }

    def clear_database(self):
        """
        Clear only the currently selected repository's collection.
        Other repositories remain untouched.
        """

        if not self.repository_id:
            raise ValueError(
                "No repository is currently selected."
            )

        self.vector_store.clear_collection()

        self.repository_history.mark_unindexed(
            self.repository_id
        )

        self.repository_path = None
        self.repository_id = None

        print("Current repository database cleared.")
