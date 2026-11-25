
from core.embeddings import EmbeddingGenerator
from core.vector_store import VectorStore


class CodeRetriever:
    """
    Retrieves relevant code chunks based on
    a user's natural-language question.
    """

    def __init__(self, vector_store=None, embedding_generator=None):
        self.embedding_generator = (
            embedding_generator or EmbeddingGenerator()
        )

        self.vector_store = vector_store or VectorStore()

    def retrieve(self, query, n_results=5):
        """
        Convert the question into an embedding
        and retrieve relevant code chunks.
        """

        if not query or not query.strip():
            raise ValueError("Search query cannot be empty.")

        query_embedding = (
            self.embedding_generator.generate_single_embedding(query)
        )

        results = self.vector_store.search(
            query_embedding=query_embedding,
            n_results=n_results
        )

        return results
