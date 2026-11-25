
import numpy as np
import pytest

from core.retriever import CodeRetriever


class MockEmbeddingGenerator:

    def generate_single_embedding(self, query):
        return np.array([0.1, 0.2, 0.3])


class MockVectorStore:

    def search(self, query_embedding, n_results=5):
        return [
            {
                "code": "def authenticate(username, password):",
                "metadata": {
                    "name": "authenticate",
                    "file_path": "auth.py"
                },
                "distance": 0.1
            }
        ]


@pytest.fixture
def retriever():
    return CodeRetriever(
        vector_store=MockVectorStore(),
        embedding_generator=MockEmbeddingGenerator()
    )


def test_retrieve_results(retriever):
    results = retriever.retrieve("Where is authentication handled?")

    assert len(results) == 1
    assert results[0]["metadata"]["name"] == "authenticate"


def test_retrieve_passes_query_embedding(retriever):
    results = retriever.retrieve("Find authentication code")

    assert results[0]["code"] == "def authenticate(username, password):"


def test_empty_query(retriever):
    with pytest.raises(ValueError):
        retriever.retrieve("")


def test_whitespace_query(retriever):
    with pytest.raises(ValueError):
        retriever.retrieve("   ")


def test_custom_number_of_results():
    class CustomVectorStore:
        def search(self, query_embedding, n_results=5):
            assert n_results == 3
            return []

    retriever = CodeRetriever(
        vector_store=CustomVectorStore(),
        embedding_generator=MockEmbeddingGenerator()
    )

    assert retriever.retrieve("Find login code", n_results=3) == []
