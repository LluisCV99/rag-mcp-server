"""
RAG MCP Server
==============
Exposes a semantic search tool over a ChromaDB knowledge base
via the Model Context Protocol (MCP) using FastMCP.
"""

import os
import json
import chromadb
from chromadb.utils import embedding_functions
from fastmcp import FastMCP


# ── Configuration ─────────────────────────────────────────────────────────────
CHROMA_HOST = os.getenv("CHROMA_HOST", "chromadb")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "18484"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "rag_knowledge")
MCP_PORT = int(os.getenv("MCP_PORT", "18485"))
MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
SERVER_NAME = os.getenv("MCP_SERVER_NAME", "RAG Knowledge Server")


# ── ChromaDB client ──────────────────────────────────────────────────────────
chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
ef = embedding_functions.DefaultEmbeddingFunction()
collection = chroma_client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=ef,
)


# ── MCP Server ───────────────────────────────────────────────────────────────
mcp = FastMCP(SERVER_NAME)


@mcp.tool
def search_knowledge(query: str, n_results: int = 5) -> str:
    """Search the RAG knowledge base using semantic similarity.

    Args:
        query: The search query in natural language.
        n_results: Number of results to return (default 5, max 20).

    Returns:
        JSON string with matching text chunks, their source files, and relevance scores.
    """
    n_results = min(max(n_results, 1), 20)

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
    )

    matches = []
    if results and results["documents"]:
        for i, doc in enumerate(results["documents"][0]):
            match = {
                "text": doc,
                "source": results["metadatas"][0][i].get("source", "unknown"),
                "chunk_index": results["metadatas"][0][i].get("chunk_index", -1),
                "distance": round(results["distances"][0][i], 4) if results.get("distances") else None,
            }
            matches.append(match)

    return json.dumps(matches, indent=2, ensure_ascii=False)


@mcp.tool
def list_sources() -> str:
    """List all source files that have been ingested into the knowledge base.

    Returns:
        JSON string with source file names and their chunk counts.
    """
    all_meta = collection.get(include=["metadatas"])
    sources: dict[str, int] = {}
    if all_meta and all_meta["metadatas"]:
        for meta in all_meta["metadatas"]:
            src = meta.get("source", "unknown")
            sources[src] = sources.get(src, 0) + 1

    result = [
        {"source": name, "chunks": count}
        for name, count in sorted(sources.items())
    ]
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.resource("rag://info")
def rag_info() -> str:
    """Get information about the RAG knowledge base (collection stats)."""
    count = collection.count()
    all_meta = collection.get(include=["metadatas"])
    sources = set()
    if all_meta and all_meta["metadatas"]:
        for meta in all_meta["metadatas"]:
            sources.add(meta.get("source", "unknown"))

    info = {
        "collection": COLLECTION_NAME,
        "total_chunks": count,
        "total_sources": len(sources),
        "sources": sorted(sources),
    }
    return json.dumps(info, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    print(f"Starting {SERVER_NAME} on {MCP_HOST}:{MCP_PORT}")
    mcp.run(transport="sse", host=MCP_HOST, port=MCP_PORT)
