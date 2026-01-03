# NorthstarCapital Application Guide

This guide explains how to run the application, what it does, and how to use its major features.

## What This App Does
NorthstarCapital is a backend platform for finance analysis and agent-driven workflows. It provides:
- A FastAPI server with tool-calling LLM endpoints.
- NEPSE market analytics endpoints and tools.
- A structured analyst workflow (brief → analysis → validation).
- A NEPSE chat agent with tool access.
- A paper-trading system with proposal/approval flow.
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
- `NEPSE_API_BASE` (e.g., `http://localhost:18080`)

## Environment Variables (Optional)
- `GROQ_MODEL`, `GROQ_MODEL1`, `GROQ_MODEL2`
- `GROQ_TEMPERATURE`
- `CORS_ORIGINS`
- `CACHE_TTL_SECONDS`
- `HTTP_TIMEOUT_SECONDS`

## Core API Endpoints

### Health
- `GET /health` → `{ "status": "ok" }`

### Analyst Workflow (NEPSE only)
- `POST /analyst/brief`
  - Request: `{ "market": "NEPSE", "symbol": "NIMB", "horizon_days": 365 }`
  - Response: `{ "brief": { ... } }`
- `POST /analyst/analyze`
  - Request: `{ "market": "NEPSE", "symbol": "NIMB", "horizon_days": 365, "include_disclaimer": true, "save": true, "model": "moonshotai/kimi-k2-instruct" }`
  - Response: `{ "brief": { ... }, "analysis": { ... }, "valid": true, "validation_errors": [], "run_id": "uuid" }`
- `GET /analyst/models`
  - Response: `{ "models": ["qwen/qwen3-32b", "moonshotai/kimi-k2-instruct", "moonshotai/kimi-k2-instruct-0905"] }`
- `GET /analyst/runs/{run_id}`
  - Response: saved run data

### NEPSE Chat Agent
- `POST /nepse/chat`
  - Request: `{ "message": "...", "history": [], "model": "qwen/qwen3-32b", "allow_web": false }`
  - Response: `{ "reply": "...", "conversation_id": "uuid" }`
- `GET /nepse/chat/models`
- `GET /nepse/chat/conversations`
- `GET /nepse/chat/conversations/{conversation_id}`
- `DELETE /nepse/chat/conversations/{conversation_id}`

### Paper Trading (Proposal Based)
- `POST /paper/portfolios`
- `GET /paper/portfolios`
- `GET /paper/portfolios/{id}`
- `GET /paper/portfolios/{id}/positions`
- `GET /paper/portfolios/{id}/trades`
- `GET /paper/portfolios/{id}/proposals?status=pending`
- `POST /paper/trades/propose`
- `POST /paper/trades/{proposal_id}/approve`
- `POST /paper/trades/{proposal_id}/reject`
- `POST /paper/cash`

### Citadel (Research Workspace)
- `POST /citadel/agent`
- `POST /citadel/agent/apply`
- `GET /citadel/agent/models`

## NEPSE Tool Coverage
NEPSE tools are available via the tool registry and used by the agent:
- Market summary, indices, sub-indices, live market
- Company details, security list, sector scrips
- Price volume history
- Top gainers/losers/turnover/trades/transactions
- Supply/demand and turnover breakdown
- Daily index and scrip graphs

## Paper Trading Flow
1) Propose a trade (buy/sell) with symbol and quantity.
2) Review pending proposals.
3) Approve or reject the proposal.
4) Approved proposals create trades and update positions.

## How to Use the NEPSE Agent
The NEPSE agent can:
- Pull NEPSE data with tools.
- Produce concise analysis.
- Propose paper trades (requires approval).

Example prompt:
```
Analyze NABIL and propose a paper trade if it fits.
```

## Troubleshooting
Common issues:
- 404 on `/analyst/...` from frontend → make sure frontend uses `/analyst-api` proxy.
- Token limit errors → reduce prompt size; use symbol-specific analysis.
- NEPSE data missing → verify `NEPSE_API_BASE` and service is running.

## Project Layout
- `server/`: API, tools, DB logic
- `client/`: Tkinter test UI
- `docs/`: documentation and schema

