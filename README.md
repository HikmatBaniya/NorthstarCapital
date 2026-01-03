# NorthstarCapital

## Financial LLM Agent (MCP + Tkinter)

This project hosts a local MCP-style tool server and a Tkinter client that can answer finance questions using free web sources and a Groq-backed LLM.

## High-level Architecture
- `server/`: MCP-compatible HTTP server exposing finance tools.
- `client/`: Tkinter UI and LLM orchestration.
- `shared/`: common configs and schemas.

## Quick Start
1) Create `.env` from `.env.example` and add your `GROQ_API_KEY`.
2) Install dependencies:
   `python -m pip install -r requirements.txt`
3) Run the server:
   `python -m server.main`
4) Run the UI:
   `python -m client.app`

## Chat Endpoint
The server exposes a chat endpoint for the frontend:
- `POST /chat`
- Request:
  ```
  {
    "message": "your question",
    "history": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}],
    "use_memory": true,
    "store_memory": false
  }
  ```
- Response:
  ```
  { "reply": "assistant response" }
  ```

## Tool Catalog
See `shared/tool_catalog.md`.
