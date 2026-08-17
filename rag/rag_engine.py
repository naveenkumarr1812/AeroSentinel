from pathlib import Path

import chromadb
from langchain_huggingface import HuggingFaceEmbeddings


class AeroSentinelRAG:

    def __init__(self):

        self.documents_dir = Path(
            "rag/documents"
        )

        self.db_dir = Path(
            "rag/vectorstore"
        )

        self.db_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        # Local embedding model.
        # This runs on CPU and is lightweight enough
        # for our prototype.
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        self.client = chromadb.PersistentClient(
            path=str(self.db_dir)
        )

        self.collection = self.client.get_or_create_collection(
            name="aerosentinel_sops"
        )

        self._index_documents()

    def _index_documents(self):

        documents = []

        for file_path in self.documents_dir.glob("*.txt"):

            text = file_path.read_text(
                encoding="utf-8"
            )

            documents.append(
                {
                    "id": file_path.stem,
                    "text": text,
                    "source": file_path.name,
                }
            )

        if not documents:
            raise RuntimeError(
                "No SOP documents found in rag/documents/"
            )

        for document in documents:

            embedding = self.embeddings.embed_query(
                document["text"]
            )

            self.collection.upsert(
                ids=[document["id"]],
                documents=[document["text"]],
                embeddings=[embedding],
                metadatas=[
                    {
                        "source": document["source"]
                    }
                ],
            )

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
    ):

        query_embedding = self.embeddings.embed_query(
            query
        )

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )

        retrieved = []

        documents = results.get(
            "documents",
            [[]]
        )[0]

        metadatas = results.get(
            "metadatas",
            [[]]
        )[0]

        for text, metadata in zip(
            documents,
            metadatas
        ):

            retrieved.append(
                {
                    "content": text,
                    "source": metadata.get(
                        "source",
                        "unknown"
                    ),
                }
            )

        return retrieved