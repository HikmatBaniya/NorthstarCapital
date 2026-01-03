# NorthstarCapital Application Guide

This guide explains how to run the application, what it does, and how to use its major features.

## What This App Does
NorthstarCapital is a backend platform for finance analysis and agent-driven workflows. It provides:
- A FastAPI server with tool-calling LLM endpoints.
- A structured research pipeline (bundles + reports).
- A company research workspace (Citadel) with persistent storage.
- A Tkinter client for interactive chat/testing.

## Quick Start
1) Create `.env` using `.env.example`.
2) Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
3) Start the backend:
   ```bash
   python -m server.main
   ```
4) (Optional) Start the Tkinter client:
   ```bash
   python -m client.app
   ```

## Environment Variables (Required)
- `GROQ_API_KEY`
- `POSTGRES_DSN`

## Environment Variables (Optional)
- `GROQ_MODEL`, `GROQ_MODEL1`, `GROQ_MODEL2`
- `GROQ_TEMPERATURE`
- `CORS_ORIGINS`
- `CACHE_TTL_SECONDS`
- `HTTP_TIMEOUT_SECONDS`
- `LOCAL_EXTENSION_MODULE` (path to a local-only extension module)

## Core API Endpoints

### Health
- `GET /health` → `{ "status": "ok" }`

### Tool Invocation
- `GET /tools` → list available tools
- `POST /invoke` → call a tool
  - Request: `{ "name": "tool.name", "arguments": { ... } }`
  - Response: `{ "name": "tool.name", "result": { ... } }`

### Chat
- `POST /chat`
  - Request: `{ "message": "...", "history": [], "use_memory": true, "store_memory": false }`
  - Response: `{ "reply": "...", "conversation_id": "uuid" }`

### Research + Reports
- `POST /research`
- `POST /report`
- `POST /research/latest`
- `POST /report/latest`
- `GET /research`
- `GET /reports`

### Compare + Portfolio
- `POST /compare`
- `POST /compare/latest`
- `GET /comparisons`
- `POST /portfolio`
- `GET /portfolios`

### Watchlist
- `GET /watchlist`
- `POST /watchlist`
- `DELETE /watchlist/{symbol}`

### Citadel (Research Workspace)
- `POST /citadel/agent`
- `POST /citadel/agent/apply`
- `GET /citadel/agent/models`

### Companies
- `POST /companies`
- `GET /companies`
- `GET /companies/{id}`
- `PUT /companies/{id}`
- `GET /companies/{id}/profile`
- `POST /companies/{id}/profile`
- `GET /companies/{id}/workspace`
- `PUT /companies/{id}/workspace`
- `GET /companies/{id}/people`
- `POST /companies/{id}/people`
- `GET /companies/{id}/documents`
- `POST /companies/{id}/documents`
- `GET /companies/{id}/financials`
- `POST /companies/{id}/financials`
- `GET /companies/{id}/subsidiaries`
- `POST /companies/{id}/subsidiaries`
- `GET /companies/{id}/ownership`
- `POST /companies/{id}/ownership`
- `POST /companies/{id}/enrich`

### Shelves
- `POST /shelves`
- `GET /shelves`
- `POST /shelves/{shelf_id}/items`
- `GET /shelves/{shelf_id}/items`

## Local Extensions
If you want local-only features, place them under `local_extensions/`.
The module `local_extensions/extension.py` can register extra routes and tools.

## Project Layout
- `server/`: API, tools, DB logic
- `client/`: Tkinter test UI
- `docs/`: documentation and schema
