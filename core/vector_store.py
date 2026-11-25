
import chromadb
from pathlib import Path


class VectorStore:
    """
    Stores code embeddings in separate ChromaDB collections
    and retrieves relevant code using semantic search.
    """

    def __init__(
        self,
        persist_directory="chroma_db",
        collection_name="repomind"
    ):
        self.persist_directory = str(Path(persist_directory))

        self.client = chromadb.PersistentClient(
            path=self.persist_directory
        )

        self.collection_name = collection_name

        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def set_collection(self, collection_name):
        """
        Switch to a separate collection for another repository.
        Existing collections and their data are preserved.
        """

        if not collection_name:
            raise ValueError("Collection name cannot be empty.")

        self.collection_name = collection_name

        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(self, chunks, embeddings):
        """
        Store code chunks, their embeddings, and metadata.
        """

        if not chunks:
            return

        if len(chunks) != len(embeddings):
            raise ValueError(
                "Number of chunks and embeddings must be equal."
            )

        ids = []
        documents = []
        metadatas = []

        for index, chunk in enumerate(chunks):
            chunk_id = (
                f"{chunk['file_path']}_"
                f"{chunk['name']}_"
                f"{chunk['start_line']}_{index}"
            )

            ids.append(chunk_id)
            documents.append(chunk["code"])

            metadatas.append({
                "type": chunk["type"],
                "name": chunk["name"],
                "class_name": chunk.get("class_name") or "",
                "file_path": chunk["file_path"],
                "start_line": chunk["start_line"],
                "end_line": chunk["end_line"],
                "parameters": ", ".join(
                    chunk.get("parameters", [])
                )
            })

        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=[
                embedding.tolist()
                for embedding in embeddings
            ],
            metadatas=metadatas
        )

    def search(self, query_embedding, n_results=5):
        """
        Find code chunks most relevant to a query
        in the currently selected repository collection.
        """

        if self.collection.count() == 0:
            return []

        results = self.collection.query(
            query_embeddings=[
                query_embedding.tolist()
            ],
            n_results=min(
                n_results,
                self.collection.count()
            ),
            include=["documents", "metadatas", "distances"]
        )

        search_results = []

        for index in range(len(results["ids"][0])):
            search_results.append({
                "id": results["ids"][0][index],
                "code": results["documents"][0][index],
                "metadata": results["metadatas"][0][index],
                "distance": results["distances"][0][index]
            })

        return search_results

    def clear_collection(self):
        """
        Remove all stored code chunks from the
        currently selected collection only.
        """

        self.client.delete_collection(
            name=self.collection_name
        )

        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def delete_collection(self, collection_name):
        """
        Delete a specific repository collection.
        """

        existing_collections = [
            collection.name
            for collection in self.client.list_collections()
        ]

        if collection_name not in existing_collections:
            return

        self.client.delete_collection(name=collection_name)

        if self.collection_name == collection_name:
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )

    def get_collection_count(self):
        """
        Return the number of stored code chunks
        in the currently selected collection.
        """

        return self.collection.count()
