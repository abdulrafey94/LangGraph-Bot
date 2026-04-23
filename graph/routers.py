from graph.state import GraphContext

VALID_NODES = {"hotel", "general"}

# "flight", "restaurant", "weather", "transport", 

def route_to_specialist(state: GraphContext) -> str:
    task = state.current_task
    return task if task in VALID_NODES else "general"
