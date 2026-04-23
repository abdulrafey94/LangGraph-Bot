from typing import Literal
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage


from graph.state import GraphContext
from utils.load_config import CONFIG

ORCHESTRATOR_MDOEL = CONFIG.agents.orchestrator_agent.model

SYSTEM_PROMPT = """\
## Role:
You are a travel assistant intent classifier.
Identify which specialist is needed to handle the user's request.
Domains: hotel, flight, restaurant, weather, transport

## Classification rules:
- Classify as the matching domain only when the user is asking for new information or a new search.
- Classify as "general" when the user is confirming, accepting, or acknowledging a result that was already presented (e.g. "that works", "sounds good", "ok book it"). These are conversation closures, not new requests.
"""

llm = ChatOpenAI(
    model=ORCHESTRATOR_MDOEL,
    temperature=0
)

class IntentClassification(BaseModel):
    current_task: Literal["hotel", "general"]

# "flight", "restaurant", "weather", "transport",

def orchestrator_node(state: GraphContext) -> dict:
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state.messages
    classifier = llm.with_structured_output(IntentClassification)
    result = classifier.invoke(messages)
    return {"current_task": result.current_task}
