from typing import List, Annotated
from pydantic import BaseModel
from langgraph.graph.message import add_messages

class GraphContext(BaseModel):
    messages: Annotated[List, add_messages] = []
    current_task: str = ""
    summary: dict = {}