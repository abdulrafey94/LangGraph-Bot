# Travel AI

A conversational travel planning assistant built with LangGraph and FastAPI. It uses a multi-agent architecture where an orchestrator routes user requests to specialized agents — currently supporting hotel search and general travel conversation.

## Architecture

```
User → POST /chat
         ↓
    Orchestrator (intent classifier)
         ↓
    ┌────┴────┐
  hotel    general
    ↓
 search_hotels / check_availability (web search)
```

**Nodes:**

| Node | Role |
|------|------|
| `orchestrator` | Classifies the user's intent and routes to the right specialist |
| `hotel` | Searches hotels and checks room availability using live web search |
| `general` | Handles greetings, confirmations, and open-ended travel questions |

**State** (`GraphContext`) carries the message history, current task label, and a summary dict across turns. Conversation memory is persisted per `thread_id` using LangGraph's `MemorySaver`.

## Project Structure

```
.
├── main.py                   # FastAPI app + lifespan setup
├── config.yaml               # Server config and model assignments
├── api/
│   ├── routes.py             # POST /chat endpoint
│   └── schema.py             # ChatRequest / ChatResponse models
├── graph/
│   ├── builder.py            # Builds and compiles the StateGraph
│   ├── state.py              # GraphContext state schema
│   ├── routers.py            # Conditional edge: routes to hotel or general
│   ├── nodes/
│   │   ├── orchestrator.py   # Intent classification node
│   │   ├── hotel.py          # Hotel specialist node (tool-calling loop)
│   │   └── general.py        # General conversation node
│   └── tools/
│       └── hotel_tools.py    # search_hotels and check_availability tools
└── utils/
    ├── load_config.py        # Loads config.yaml
    └── logging_config.py     # Logging setup
```

## API

### `POST /chat`

```json
// Request
{
  "thread_id": "user-session-123",
  "message": "Find me hotels in Paris under $200"
}

// Response
{
  "thread_id": "user-session-123",
  "reply": "Here are some hotels in Paris under $200..."
}
```

Use the same `thread_id` across turns to maintain conversation context.

## Setup

**Prerequisites:** Python 3.11+, [uv](https://github.com/astral-sh/uv)

```bash
git clone <repo-url>
cd LangGraph-Bot

# Install dependencies
uv sync

# Configure environment
cp .env.example .env   # then add your OPENAI_API_KEY
```

**.env**
```
OPENAI_API_KEY=sk-...
```

**Run the server:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8200 --reload
```

Docs available at `http://localhost:8200/docs`.

## Configuration

Edit `config.yaml` to change server settings or swap models:

```yaml
server:
  host: "0.0.0.0"
  port: 8200

agents:
  orchestrator_agent:
    model: "gpt-5.4-nano"
  hotel_search_agent:
    model: "gpt-5.4-nano"
```

Any OpenAI-compatible model string works. The hotel agent requires a model with web search tool support (`web_search_preview`).

## Extending with New Specialists

1. Add a new node file in `graph/nodes/`.
2. Register the node in `graph/builder.py` and add an edge to `END`.
3. Add the node name to `VALID_NODES` in `graph/routers.py`.
4. Add the intent label to the `IntentClassification` literal in `graph/nodes/orchestrator.py`.
