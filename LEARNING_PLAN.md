# LangGraph Travel Booking Agent — Learning Guide

## Mental Model Mapping

| What You Know | LangGraph Equivalent | Key Difference |
|---|---|---|
| Pydantic AI `RunContext` / deps | `TypedDict` / `BaseModel` State | Explicit dict passed between nodes; no DI magic |
| Pydantic AI agent / OpenAI Agent | Node (Python function) | Nodes are stateless; state carries everything |
| Tool call sequence | Edge / Conditional Edge | Control flow is explicit graph wiring |
| OpenAI Agents SDK `handoff` | `conditional_edge` routing fn | You write the router logic |
| `Runner.run()` | `graph.invoke()` / `graph.astream()` | Same idea, different API |
| In-memory history | `MemorySaver` checkpointer | Persists full graph state per `thread_id` |

> **Biggest mindset shift**: You are not configuring an agent, you are wiring a graph. The LLM is just a node.

> **State note**: LangGraph supports both `TypedDict` and Pydantic `BaseModel` as state schemas. Nodes always return a plain `dict` (partial patch) — LangGraph merges it into the model and re-validates.

---

## Target File Structure

```
lang-graph-bot/
├── main.py                    # FastAPI entry point
├── config.py                  # Model client factory
├── graph/
│   ├── state.py               # State schema (BaseModel or TypedDict)
│   ├── builder.py             # Graph assembly + compile
│   ├── routers.py             # Conditional edge functions
│   ├── nodes/
│   │   ├── orchestrator.py
│   │   ├── hotel.py
│   │   ├── flight.py
│   │   ├── restaurant.py
│   │   ├── weather.py
│   │   └── transport.py
│   └── tools/
│       ├── hotel_tools.py
│       ├── flight_tools.py
│       ├── restaurant_tools.py
│       ├── weather_tools.py
│       └── transport_tools.py
└── api/
    ├── routes.py
    └── schemas.py
```

---

## Phase 1 — The Minimum Viable Graph

**Deps**: `uv add langgraph langchain-core`

**Concepts**: `StateGraph`, state schema, nodes, edges, `START`/`END`, `compile()`, `invoke()`

**Implement**:
1. `graph/state.py` — `TravelState(BaseModel)` with `messages: Annotated[list, add_messages]`, `user_request: str = ""`, `current_task: str = ""`
2. `graph/nodes/orchestrator.py` — function that prints state and returns `{"current_task": "thinking"}`
3. `graph/builder.py` — wire `START -> orchestrator -> END`, `compile()`, `invoke({"user_request": "..."})`
4. Add a `logger` node, wire `orchestrator -> logger -> END`, observe state flow

**Checkpoint**: If two nodes both return `{"messages": [...]}` and `messages` has no reducer, what happens to the final list? Why does `add_messages` change that?

---

## Phase 2 — LLM as a Node + Manual Tool Calling

**Deps**: `uv add langchain-openai`
- OpenAI: default endpoint
- DeepSeek: `base_url="https://api.deepseek.com/v1"`
- Grok: `base_url="https://api.x.ai/v1"`

**Concepts**: `bind_tools`, `AIMessage`/`ToolMessage`/`HumanMessage`, tool calls are just data

**Implement**:
1. `config.py` — `get_llm()` using `ChatOpenAI` with your chosen provider
2. `graph/tools/hotel_tools.py` — `@tool` decorated `search_hotels(city, check_in, check_out, guests) -> str` returning hardcoded JSON
3. Update `orchestrator.py` — `llm.bind_tools([...])`, invoke with messages, print `tool_calls`
4. `tool_executor` node — manually dispatch tool calls by name lookup, return `ToolMessage`
5. Wire fixed loop: `START -> orchestrator -> tool_executor -> orchestrator -> END`

**Checkpoint**: Why must `ToolMessage.tool_call_id` exactly match the id from the `AIMessage`'s tool call?

---

## Phase 3 — ToolNode + Conditional Edges (Real Orchestrator)

**Concepts**: `ToolNode`, `tools_condition`, custom routing functions, orchestrator pattern

**Implement**:
1. Replace manual executor with `ToolNode([...])` from `langgraph.prebuilt`
2. Replace fixed edge with `add_conditional_edges("orchestrator", tools_condition)`
3. `graph/routers.py` — `route_to_specialist(state) -> str` reading `state.current_task`, returning node names
4. Stub specialist nodes (hotel, flight, restaurant, weather, transport) — print + return `{"current_task": "done"}`
5. Wire full graph with conditional edges from orchestrator to specialists
6. Test routing with different user inputs

**Checkpoint**: What is the difference between `add_edge` and `add_conditional_edges`? Why can't a fixed edge handle routing?

---

## Phase 4 — Specialist Nodes with Real Tools

**Concepts**: Per-node LLM + tools, mini ReAct loop inside a node, shared state for results

**Implement**:
1. Tool files for all domains with stub JSON returns (flight, restaurant, weather, transport)
2. Each specialist node: bind its own tools, run invoke -> check tool_calls -> execute -> invoke loop, write result to state
3. Add `summary: dict = {}` to `TravelState`
4. `synthesizer` node — reads `summary`, calls LLM for polished final answer
5. Route each specialist -> `synthesizer` -> `END`

**Checkpoint**: If a user asks for "hotels AND flights", what needs to change in your routing logic? Sketch it on paper first.

---

## Phase 5 — Checkpointing and Conversational Memory

**Deps**: use `MemorySaver` first (built-in), then `uv add langgraph-checkpoint-sqlite`

**Concepts**: `MemorySaver`, `SqliteSaver`, `thread_id`, `get_state`, `get_state_history`

**Implement**:
1. `MemorySaver()` passed into `compile(checkpointer=...)`
2. All `invoke()` calls get `config={"configurable": {"thread_id": "user-123"}}`
3. Multi-turn test: two requests with same `thread_id` — observe context persists
4. Explore `graph.get_state(config)` and `graph.get_state_history(config)`
5. Upgrade to `SqliteSaver`, restart process, verify state survives

**Checkpoint**: Two users hit your API simultaneously. What must each have to keep their state isolated?

---

## Phase 6 — Streaming

**Concepts**: `stream()` modes (`"values"`, `"updates"`, `"messages"`), `astream_events()` for production

**Implement**:
1. `graph.astream(mode="updates")` — print node name + what changed per chunk
2. Switch to `mode="messages"` — observe token-level streaming
3. `graph.astream_events(version="v2")` — filter `on_chat_model_stream` for tokens, `on_chain_end` for node completions
4. `graph/streaming.py` — async generator `stream_graph_events(graph, input, config)` yielding `{"type": "token"|"node_complete", ...}`

**Checkpoint**: What is the difference between `"values"` and `"updates"` streaming mode? When would you choose each?

---

## Phase 7 — FastAPI Integration

**Deps**: `uv add fastapi "uvicorn[standard]" python-dotenv`

**Concepts**: Graph lifespan in FastAPI, SSE streaming, `thread_id` as session key

**Implement**:
1. `api/schemas.py` — `ChatRequest`, `ChatResponse`, `StreamEvent` Pydantic models
2. `api/routes.py` — `POST /chat` (sync invoke), `POST /chat/stream` (SSE via `StreamingResponse`), `GET /chat/history/{thread_id}`
3. `main.py` — FastAPI lifespan (compile graph on startup → `app.state.graph`), include router, CORS middleware
4. SSE event generator: each chunk → `data: {json}\n\n`, finish with `data: [DONE]\n\n`
5. Test: `curl --no-buffer -N -X POST http://localhost:8000/chat/stream`

**Checkpoint**: Why compile the graph once at startup rather than once per request?

---

## Phase 8 — Hardening

**Concepts**: Error handling in nodes, `interrupt_before` for human-in-the-loop, LangSmith tracing

**Implement**:
1. `errors: list[str] = []` in state — nodes catch exceptions, append error, never crash the graph
2. `interrupt_before=["confirm_booking"]` in `compile()` — API returns `status: "awaiting_confirmation"`, `POST /chat/confirm/{thread_id}` resumes with `graph.invoke(None, config=...)`
3. Set `LANGCHAIN_TRACING_V2=true` + `LANGCHAIN_API_KEY` env vars — observe auto-tracing in LangSmith (no code changes needed)
4. `POST /chat/reset/{thread_id}` using `graph.update_state(config, {"messages": [], "summary": {}})`

---

## Key Rules to Remember

| Rule | Detail |
|---|---|
| State updates are patches | Returning `{"current_task": "hotels"}` doesn't wipe `messages` — it only updates that key |
| Reducers control merge | No reducer = last-write-wins. `add_messages` = append. You can write custom reducers. |
| `compile()` locks the graph | Cannot add nodes after compiling. Compile once, invoke many times. |
| `thread_id` is your session key | All checkpointing keyed by `{"configurable": {"thread_id": "..."}}` |
| Conditional edges return strings | The routing function returns the **name** of the next node as a string |
| `ToolNode` requires `bind_tools` | Tool name in `AIMessage.tool_calls` must match a tool in `ToolNode`'s list |
| `astream_events` is most powerful | Gives every event — tokens, tool calls, node starts/ends — with node names attached |
