# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Package Management

This project uses `uv`. Always use `uv add <package>` to install dependencies — never `pip install`.

```bash
uv add <package>          # add a dependency
uv run python <file>      # run a script in the venv
uv run uvicorn main:app --reload  # run the FastAPI server
```

## Project Purpose

A LangGraph-based travel booking agent (hotels, flights, restaurants, weather, local transport) exposed as a FastAPI app. Orchestrator pattern: a central LLM node routes to specialist nodes based on user intent.

## Architecture

The graph is assembled in `graph/builder.py` and compiled once at FastAPI startup (stored on `app.state.graph`). Each HTTP request invokes the compiled graph with a `thread_id` for session isolation.

**Data flow**: `FastAPI route → graph.invoke(input, config={"configurable": {"thread_id": "..."}}) → orchestrator node → conditional edge → specialist node → synthesizer node → response`

**State** (`graph/state.py`): A Pydantic `BaseModel` (`TravelState`) is the sole communication channel between nodes. Nodes receive the full state and return a partial `dict` — LangGraph merges it as a patch. The `messages` field uses `Annotated[list, add_messages]` so concurrent writes append rather than overwrite.

**Nodes** (`graph/nodes/`): Plain Python functions `(state: TravelState) -> dict`. The orchestrator identifies user intent and sets `current_task`. Specialist nodes (hotel, flight, restaurant, weather, transport) each bind their own tools and run their own ReAct loop. A `synthesizer` node produces the final response from `state.summary`.

**Routing** (`graph/routers.py`): Conditional edge functions return node name strings based on `state.current_task`. `tools_condition` (from `langgraph.prebuilt`) handles the standard tool-call-or-stop decision within each node.

**Tools** (`graph/tools/`): `@tool`-decorated functions. Each specialist node binds only its own tools via `llm.bind_tools([...])`.

**Checkpointing**: `SqliteSaver` (or `MemorySaver` in tests) passed to `graph.compile(checkpointer=...)`. Enables multi-turn conversation and mid-execution resume.

**Streaming** (`graph/streaming.py`): Async generator over `graph.astream_events(version="v2")`, yielding `{"type": "token"|"node_complete", ...}` dicts consumed by the SSE endpoint.

## Model Configuration (`config.py`)

`get_llm()` returns a `ChatOpenAI` instance. Switch providers via `base_url`:
- DeepSeek: `base_url="https://api.deepseek.com/v1"`
- Grok (xAI): `base_url="https://api.x.ai/v1"`
- OpenAI: default (no `base_url` needed)
