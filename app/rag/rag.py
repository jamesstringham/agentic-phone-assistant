import os
import uuid
from pathlib import Path
from typing import Any

import chromadb
from openai import AzureOpenAI

from app.config import settings


class StringhamRAG:
    def __init__(
        self,
        docs_dir: str | Path | None = None,
        chroma_dir: str | Path | None = None,
        collection_name: str = "stringham_consulting_docs",
    ):
        if not settings.azure_openai_endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT is not set")
        if not settings.azure_openai_api_key:
            raise ValueError("AZURE_OPENAI_API_KEY is not set")
        if not settings.azure_openai_embedding_deployment:
            raise ValueError("AZURE_OPENAI_EMBEDDING_DEPLOYMENT is not set")

        base_dir = Path(__file__).resolve().parent

        self.docs_dir = Path(docs_dir) if docs_dir else base_dir / "docs"
        self.chroma_dir = Path(chroma_dir) if chroma_dir else base_dir / "chroma_db"
        self.collection_name = collection_name

        self.openai_client = AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_endpoint,
        )

        self.embedding_deployment = settings.azure_openai_embedding_deployment

        self.chroma_client = chromadb.PersistentClient(path=str(self.chroma_dir))
        self.collection = self.chroma_client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=None,
        )

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        response = self.openai_client.embeddings.create(
            model=self.embedding_deployment,
            input=texts,
        )

        return [item.embedding for item in response.data]

    def load_documents(self) -> list[dict[str, Any]]:
        docs: list[dict[str, Any]] = []

        for path in sorted(self.docs_dir.glob("*.txt")):
            text = path.read_text(encoding="utf-8").strip()
            if not text:
                continue

            docs.append({
                "source": path.name,
                "text": text,
            })

        return docs

    def chunk_text(
        self,
        text: str,
        *,
        chunk_size: int = 900,
        overlap: int = 150,
    ) -> list[str]:
        """
        Simple character-based chunking.

        Good enough for your current docs because they are short, structured,
        and paragraph-heavy.
        """
        text = " ".join(text.split())
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end].strip()

            if chunk:
                chunks.append(chunk)

            start = end - overlap
            if start < 0:
                start = 0

            if start >= len(text):
                break

        return chunks

    def rebuild_index(self) -> dict[str, Any]:
        """
        Rebuild the Chroma collection from scratch.
        Use this whenever you edit the docs.
        """
        try:
            self.chroma_client.delete_collection(self.collection_name)
        except Exception:
            pass

        self.collection = self.chroma_client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=None,
        )

        documents = []
        metadatas = []
        ids = []

        loaded_docs = self.load_documents()

        for doc in loaded_docs:
            source = doc["source"]
            chunks = self.chunk_text(doc["text"])

            for idx, chunk in enumerate(chunks):
                documents.append(chunk)
                metadatas.append({
                    "source": source,
                    "chunk_index": idx,
                })
                ids.append(f"{source}:{idx}:{uuid.uuid4().hex[:8]}")

        if not documents:
            return {
                "status": "empty",
                "message": f"No .txt documents found in {self.docs_dir}",
                "chunks_indexed": 0,
            }

        embeddings = self.embed_texts(documents)

        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )

        return {
            "status": "success",
            "docs_loaded": len(loaded_docs),
            "chunks_indexed": len(documents),
            "collection": self.collection_name,
            "chroma_dir": str(self.chroma_dir),
        }

    def search(
        self,
        query: str,
        *,
        n_results: int = 4,
    ) -> dict[str, Any]:
        if not query.strip():
            return {
                "status": "error",
                "message": "Query is empty",
                "results": [],
            }

        query_embedding = self.embed_texts([query])[0]

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

        docs = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        matches = []
        for doc, metadata, distance in zip(docs, metadatas, distances):
            matches.append({
                "text": doc,
                "source": metadata.get("source"),
                "chunk_index": metadata.get("chunk_index"),
                "distance": distance,
            })

        return {
            "status": "success",
            "query": query,
            "results": matches,
        }


_rag_instance: StringhamRAG | None = None


def get_rag() -> StringhamRAG:
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = StringhamRAG()
    return _rag_instance


def rebuild_index() -> dict[str, Any]:
    return get_rag().rebuild_index()


def search_knowledge_base(query: str) -> dict[str, Any]:
    return get_rag().search(query)