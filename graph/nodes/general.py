from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage

from graph.state import GraphContext
from utils.load_config import CONFIG

GENERAL_MODEL = CONFIG.agents.orchestrator_agent.model

SYSTEM_PROMPT = """\
## Role:
You are a friendly travel assistant. Respond conversationally to greetings and general questions.
If the user mentions a travel destination or trip, acknowledge it warmly and let them know you can
help with hotels, flights, restaurants, weather, and local transport.

## Guidelines:
- Be friendly, conversational, but precise.
- Never exceed 2-3 points in your response.
- Don't use hyphens that make it look like AI generated response.

"""

llm = ChatOpenAI(model=GENERAL_MODEL, temperature=0.7)


def general_node(state: GraphContext) -> dict:
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state.messages
    response = llm.invoke(messages)
    return {"messages": [response]}
