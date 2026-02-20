from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from state import AppState
from agents import route_request, flight_agent, hotel_agent

def router_node(state: AppState):
    return route_request(state)

def route_transition(state: AppState):
    active = state.get("active_service")
    if active == "flight":
        return "flight_agent"
    elif active == "hotel":
        return "hotel_agent"
    else:
        # Default to END if we don't know where to go
        return END

workflow = StateGraph(AppState)

workflow.add_node("router", router_node)
workflow.add_node("flight_agent", flight_agent)
workflow.add_node("hotel_agent", hotel_agent)

workflow.add_edge(START, "router")
workflow.add_conditional_edges(
    "router",
    route_transition,
    {"flight_agent": "flight_agent", "hotel_agent": "hotel_agent", END: END}
)

workflow.add_edge("flight_agent", END)
workflow.add_edge("hotel_agent", END)

memory = MemorySaver()
app_graph = workflow.compile(checkpointer=memory)
