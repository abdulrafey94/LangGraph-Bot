from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, ToolMessage

from graph.state import GraphContext
from graph.tools.hotel_tools import search_hotels, check_availability
from utils.load_config import CONFIG

HOTEL_MODEL = CONFIG.agents.hotel_search_agent.model

SYSTEM_PROMPT = """\
## Role:
You are a hotel specialist for a travel planning assistant.
Your job is to help users find and evaluate hotels.

## Guidelines:
- Search proactively with whatever information the user has provided. Do not wait for all details.
- After presenting results, naturally ask for any missing details (dates, guests) to help narrow down or proceed.
- If the user mentions a specific hotel, use check_availability to get room details.
- Be conversational and helpful, like a knowledgeable travel agent.
- Your follow-ups must be concise and to-the-point. Never exceed 2-3 points in your response.

## When NOT to call tools:
- If the user is confirming or selecting from options you already presented earlier in this conversation (e.g. "deluxe is fine", "that one works", "I'll book the standard room"), do NOT call any tool again.
- You cannot actually complete a booking. When a user confirms a choice, acknowledge their selection, tell them to book directly on the hotel's website or a booking platform, then ask what else they need for their trip (flights, restaurants, weather, local transport).
"""

tools = [search_hotels, check_availability]
tool_map = {t.name: t for t in tools}

llm = ChatOpenAI(model=HOTEL_MODEL, temperature=0).bind_tools(tools)


def hotel_node(state: GraphContext) -> dict:
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state.messages

    while True:
        response = llm.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            break

        for tool_call in response.tool_calls:
            result = tool_map[tool_call["name"]].invoke(tool_call["args"])
            messages.append(ToolMessage(content=result.model_dump_json(), tool_call_id=tool_call["id"]))

    return {"messages": [response]}