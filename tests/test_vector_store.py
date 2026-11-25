
import numpy as np
import pytest

from core.vector_store import VectorStore


@pytest.fixture
def vector_store(tmp_path):
    return VectorStore(
        persist_directory=str(tmp_path / "test_chroma_db"),
        collection_name="test_repomind"
    )


@pytest.fixture
def sample_chunks():
    return [
        {
            "type": "function",
            "name": "authenticate",
            "class_name": None,
            "file_path": "auth.py",
            "start_line": 1,
            "end_line": 5,
            "parameters": ["username", "password"],
            "code": "def authenticate(username, password):\n    return True"
        },
        {
            "type": "function",
            "name": "generate_token",
            "class_name": None,
            "file_path": "auth.py",
            "start_line": 7,
            "end_line": 10,
            "parameters": ["user_id"],
            "code": "def generate_token(user_id):\n    return 'token'"
        }
    ]


@pytest.fixture
def sample_embeddings():
    return np.array([
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6]
    ])


def test_initialization(vector_store):
    assert vector_store.get_collection_count() == 0


def test_add_chunks(vector_store, sample_chunks, sample_embeddings):
    vector_store.add_chunks(sample_chunks, sample_embeddings)

    assert vector_store.get_collection_count() == 2


def test_search(vector_store, sample_chunks, sample_embeddings):
    vector_store.add_chunks(sample_chunks, sample_embeddings)

    results = vector_store.search(
        query_embedding=sample_embeddings[0],
        n_results=2
    )

    assert len(results) == 2
    assert "code" in results[0]
    assert "metadata" in results[0]
    assert "distance" in results[0]


def test_empty_search(vector_store):
    results = vector_store.search(
        query_embedding=np.array([0.1, 0.2, 0.3])
    )

    assert results == []


def test_clear_collection(vector_store, sample_chunks, sample_embeddings):
    vector_store.add_chunks(sample_chunks, sample_embeddings)

    vector_store.clear_collection()

    assert vector_store.get_collection_count() == 0


def test_mismatched_chunks_and_embeddings(
    vector_store, sample_chunks, sample_embeddings
):
    with pytest.raises(ValueError):
        vector_store.add_chunks(
            sample_chunks,
            sample_embeddings[:1]
        )
