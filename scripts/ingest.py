"""
RAG Ingestion Script
====================
Scans a directory for documents, chunks them, and stores embeddings in ChromaDB.
All behavior is configurable via environment variables.
"""

import os
import sys
import time
import glob
import chromadb
from chromadb.utils import embedding_functions


# ── Configuration (env vars) ─────────────────────────────────────────────────
CHROMA_HOST = os.getenv("CHROMA_HOST", "chromadb")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "18484"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "rag_knowledge")
RAG_DIR = os.getenv("RAG_DIR", "/data/rag")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "120"))
FILE_EXTENSIONS = os.getenv("FILE_EXTENSIONS", ".md,.txt").split(",")
MAX_RETRIES = int(os.getenv("INGEST_MAX_RETRIES", "15"))
RETRY_DELAY = int(os.getenv("INGEST_RETRY_DELAY", "3"))


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    step = max(size - overlap, 1)
    for i in range(0, len(text), step):
        chunk = text[i : i + size]
        if chunk.strip():
            chunks.append(chunk)
    return chunks


def discover_files(directory: str, extensions: list[str]) -> list[str]:
    """Find all files in directory matching the given extensions."""
    files = []
    for ext in extensions:
        ext = ext.strip().lstrip(".")
        pattern = os.path.join(directory, f"**/*.{ext}")
        files.extend(glob.glob(pattern, recursive=True))
    return sorted(set(files))


def wait_for_chroma(host: str, port: int, retries: int, delay: int):
    """Block until ChromaDB is reachable."""
    client = None
    for attempt in range(1, retries + 1):
        try:
            client = chromadb.HttpClient(host=host, port=port)
            client.heartbeat()
            print(f"✓ ChromaDB is ready (attempt {attempt})")
            return client
        except Exception as e:
            print(f"  Waiting for ChromaDB ({attempt}/{retries}): {e}")
            time.sleep(delay)
    print("✗ ChromaDB never became available. Exiting.")
    sys.exit(1)


def ingest():
    """Main ingestion pipeline."""
    print("=" * 60)
    print("RAG Ingestion")
    print("=" * 60)
    print(f"  CHROMA_HOST      = {CHROMA_HOST}")
    print(f"  CHROMA_PORT      = {CHROMA_PORT}")
    print(f"  COLLECTION_NAME  = {COLLECTION_NAME}")
    print(f"  RAG_DIR          = {RAG_DIR}")
    print(f"  CHUNK_SIZE       = {CHUNK_SIZE}")
    print(f"  CHUNK_OVERLAP    = {CHUNK_OVERLAP}")
    print(f"  FILE_EXTENSIONS  = {FILE_EXTENSIONS}")
    print("=" * 60)

    # Connect
    client = wait_for_chroma(CHROMA_HOST, CHROMA_PORT, MAX_RETRIES, RETRY_DELAY)

    # Embedding function (all-MiniLM-L6-v2 by default via sentence-transformers)
    ef = embedding_functions.DefaultEmbeddingFunction()

    # Reset collection for a clean re-index
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"  Deleted existing collection '{COLLECTION_NAME}'")
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
    )

    # Discover files
    files = discover_files(RAG_DIR, FILE_EXTENSIONS)
    if not files:
        print(f"⚠ No files found in {RAG_DIR} with extensions {FILE_EXTENSIONS}")
        return

    print(f"\n  Found {len(files)} file(s) to ingest:")
    for f in files:
        print(f"    • {os.path.basename(f)}")

    # Ingest
    total_chunks = 0
    for filepath in files:
        filename = os.path.basename(filepath)
        with open(filepath, "r", encoding="utf-8") as fh:
            content = fh.read()

        chunks = chunk_text(content, CHUNK_SIZE, CHUNK_OVERLAP)
        if not chunks:
            print(f"  ⚠ {filename}: empty or whitespace-only, skipping")
            continue

        ids = [f"{filename}__chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {"source": filename, "chunk_index": i, "total_chunks": len(chunks)}
            for i in range(len(chunks))
        ]

        collection.add(documents=chunks, ids=ids, metadatas=metadatas)
        total_chunks += len(chunks)
        print(f"  ✓ {filename}: {len(chunks)} chunks indexed")

    print(f"\n{'=' * 60}")
    print(f"  Total: {total_chunks} chunks from {len(files)} files")
    print(f"  Collection: {COLLECTION_NAME}")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    ingest()
