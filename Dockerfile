# ═══════════════════════════════════════════════════════════════════════════════
# RAG MCP Server — Dockerfile
# ═══════════════════════════════════════════════════════════════════════════════
FROM python:3.12-slim

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install dependencies
COPY scripts/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application scripts
COPY scripts/ingest.py .
COPY scripts/server.py .
COPY scripts/entrypoint.sh .
RUN chmod +x entrypoint.sh

# Default env vars (can be overridden in docker-compose or .env)
ENV CHROMA_HOST=chromadb
ENV CHROMA_PORT=18484
ENV COLLECTION_NAME=rag_knowledge
ENV RAG_DIR=/data/rag
ENV CHUNK_SIZE=800
ENV CHUNK_OVERLAP=120
ENV FILE_EXTENSIONS=".md,.txt"
ENV MCP_PORT=18485
ENV MCP_HOST=0.0.0.0
ENV MCP_SERVER_NAME="RAG Knowledge Server"

EXPOSE ${MCP_PORT}

ENTRYPOINT ["./entrypoint.sh"]
