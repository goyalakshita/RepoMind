
import numpy as np
import pytest

from core.embeddings import EmbeddingGenerator


@pytest.fixture(scope="module")
def embedding_generator():
    return EmbeddingGenerator()


def test_embedding_dimension(embedding_generator):

    dimension = embedding_generator.get_embedding_dimension()

    assert dimension == 384


def test_single_embedding(embedding_generator):

    embedding = embedding_generator.generate_single_embedding(
        "authenticate user using password"
    )

    assert embedding.shape == (384,)
    assert np.isfinite(embedding).all()


def test_multiple_embeddings(embedding_generator):

    texts = [
        "authenticate user",
        "connect to database",
        "generate authentication token"
    ]

    embeddings = embedding_generator.generate_embeddings(texts)

    assert embeddings.shape == (3, 384)
    assert np.isfinite(embeddings).all()


def test_empty_input(embedding_generator):

    embeddings = embedding_generator.generate_embeddings([])

    assert embeddings == []


def test_invalid_single_input(embedding_generator):

    with pytest.raises(ValueError):
        embedding_generator.generate_single_embedding("")
