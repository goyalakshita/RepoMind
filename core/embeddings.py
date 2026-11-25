
from sentence_transformers import SentenceTransformer


class EmbeddingGenerator:
    """
    Generates numerical embeddings for code chunks
    using Sentence Transformers.
    """

    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model_name = model_name

        print(f"Loading embedding model: {model_name}")

        self.model = SentenceTransformer(model_name)

        print("Embedding model loaded successfully!")

    def generate_embeddings(self, texts):
        """
        Convert a list of text/code chunks into embeddings.
        """

        if not texts:
            return []

        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=True,
            normalize_embeddings=True
        )

        return embeddings

    def generate_single_embedding(self, text):
        """
        Generate an embedding for a single text.
        """

        if not text or not text.strip():
            raise ValueError("Input text cannot be empty.")

        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        return embedding

    def get_embedding_dimension(self):
        """
        Return the dimension of the embedding vectors.
        """

        return self.model.get_embedding_dimension()
