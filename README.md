# RAG MCP Server

A dockerized **RAG (Retrieval-Augmented Generation) MCP server** that ingests your knowledge files into a vector database and exposes semantic search via the [Model Context Protocol](https://modelcontextprotocol.io).

Any MCP-compatible agent (Claude Desktop, Cursor, Gemini, custom agents…) can connect and query your knowledge base.

## Architecture

```
┌───────────────┐        ┌──────────────────┐
│   MCP Client  │◄──SSE──│  RAG MCP Server  │
│ (your agent)  │        │   (port 18485)   │
└───────────────┘        └────────┬─────────┘
                                  │
                         ┌────────▼─────────┐
                         │    ChromaDB       │
                         │   (port 18484)    │
                         └──────────────────┘
```

## Quick Start

```bash
# 1. Clone and enter the repo
git clone <your-repo-url> && cd rag-mcp-server

# 2. Add your knowledge files to rag/
#    (already contains example .md files)

# 3. (Optional) Copy and edit environment config
cp .env.example .env

# 4. Build and run
docker compose up --build -d

# 5. Check logs
docker compose logs -f rag-mcp
```

The server will:
1. Wait for ChromaDB to be ready
2. Ingest all `.md` and `.txt` files from `rag/`
3. Start the MCP server on port `18485`

## MCP Tools

| Tool | Description |
|------|-------------|
| `search_knowledge(query, n_results=5)` | Semantic search over the knowledge base. Returns matching chunks with source file and distance score. |
| `list_sources()` | Lists all ingested source files with chunk counts. |

### MCP Resources

| URI | Description |
|-----|-------------|
| `rag://info` | Collection stats: total chunks, total sources, source list. |

## Configuration

All parameters are configurable via environment variables (set in `.env` or `docker-compose.yml`):

| Variable | Default | Description |
|----------|---------|-------------|
| `CHROMA_PORT` | `18484` | ChromaDB exposed port |
| `MCP_PORT` | `18485` | MCP server port |
| `COLLECTION_NAME` | `rag_knowledge` | ChromaDB collection name |
| `CHUNK_SIZE` | `800` | Characters per chunk |
| `CHUNK_OVERLAP` | `120` | Overlap between chunks |
| `FILE_EXTENSIONS` | `.md,.txt` | File types to ingest |
| `MCP_SERVER_NAME` | `RAG Knowledge Server` | Server display name |

## Connecting Your Agent

### Claude Desktop / Cursor / Windsurf

Add to your MCP config:

```json
{
  "mcpServers": {
    "rag-knowledge": {
      "url": "http://localhost:18485/sse"
    }
  }
}
```

### Gemini CLI / Other MCP Clients

Point your client to `http://localhost:18485/sse`.

## Adding Knowledge Files

1. Drop `.md` or `.txt` files into the `rag/` directory
2. Restart the container to re-ingest:
   ```bash
   docker compose restart rag-mcp
   ```

## Stopping

```bash
docker compose down       # Stop containers (keep data)
docker compose down -v    # Stop and delete vector DB data
```
