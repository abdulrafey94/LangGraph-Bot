from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from graph.state import GraphContext
from graph.nodes.orchestrator import orchestrator_node
from graph.nodes.general import general_node
from graph.nodes.hotel import hotel_node
from graph.routers import route_to_specialist

def build_graph():
    builder = StateGraph(GraphContext)

    builder.add_node("orchestrator", orchestrator_node)
    builder.add_node("general", general_node)
    builder.add_node("hotel", hotel_node)

    builder.add_edge(START, "orchestrator")
    builder.add_conditional_edges("orchestrator", route_to_specialist)
    builder.add_edge("general", END)
    builder.add_edge("hotel", END)

    return builder.compile(checkpointer=MemorySaver())
