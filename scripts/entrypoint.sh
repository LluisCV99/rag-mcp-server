#!/bin/bash
set -e

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║         RAG MCP Server — Entrypoint          ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── Step 1: Ingest documents ────────────────────────────────────────────────
echo "▶ Running ingestion..."
python /app/ingest.py

# ── Step 2: Start MCP server ────────────────────────────────────────────────
echo "▶ Starting MCP server..."
exec python /app/server.py
