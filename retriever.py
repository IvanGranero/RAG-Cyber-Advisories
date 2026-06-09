import re
import chromadb
from chromadb.utils import embedding_functions
from config import CHROMA_COLLECTION, CHROMA_PATH, EMBEDDING_MODEL, N_RESULTS

# Embedding function and ChromaDB client are initialized once at module load.
_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=EMBEDDING_MODEL
)
_client = chromadb.PersistentClient(path=CHROMA_PATH)
_collection = _client.get_or_create_collection(
    name=CHROMA_COLLECTION,
    embedding_function=_ef,
    metadata={"hnsw:space": "cosine"},
)


def get_collection():
    """Return the ChromaDB collection. Used by app.py during ingestion."""
    return _collection


def embed_and_store(chunks, batch_size=5000):
    """
    Embed CVE/NVD chunks and store them in ChromaDB.
    Each chunk has:
      - "chunk_id": CVE ID or UUID
      - "text": vulnerability description
      - "metadata": dict with vendor, product, severity, cvss, cwe
    """
    total = len(chunks)
    for i in range(0, total, batch_size):
        batch = chunks[i:i+batch_size]

        documents = [c["text"] for c in batch]
        ids = [c["chunk_id"] for c in batch]

        # Flatten metadata into primitives for ChromaDB
        metadatas = []
        for c in batch:
            meta = c.get("metadata", {})
            flat_meta = {
                "vendor": str(meta.get("vendor") or ""),
                "product": str(meta.get("product") or ""),
                "severity": str(meta.get("severity") or ""),
                "cvss": float(meta.get("cvss")) if meta.get("cvss") is not None else -1.0,
                "cwe": str(meta.get("cwe") or ""),
            }
            metadatas.append(flat_meta)

        _collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )
        print(f"Stored batch {i//batch_size+1} ({len(batch)} chunks).")

    print(f"Stored {_collection.count()} total chunks in the vector database.")


def retrieve(query, n_results=N_RESULTS):
    if _collection.count() == 0:
        return []

    # Try to extract CVE ID from query
    match = re.search(r"CVE-\d{4}-\d+", query, re.IGNORECASE)
    if match:
        cve_id = match.group(0)
        print("Matched CVE ID:", cve_id)
        result = _collection.get(ids=[cve_id], include=["documents","metadatas"])
        print(result)
        if result and result["ids"]:
            return [{
                "text": result["documents"][0],
                "metadata": result["metadatas"][0],
                "distance": 0.0  # exact match
            }]
        else:
            return []

    # Otherwise, semantic search
    results = _collection.query(
        query_texts=[query],
        n_results=n_results,
        include=["documents","metadatas","distances"],
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    output = []
    for text, meta, dist in zip(documents, metadatas, distances):
        output.append({
            "text": text,
            "metadata": meta,
            "distance": dist,
        })

    return output

