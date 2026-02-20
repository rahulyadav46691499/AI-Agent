from typing import TypedDict, Annotated, List, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

from models import FlightContext, HotelContext

class AppState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    active_service: Optional[str]  # "flight", "hotel", or None
    flight_context: FlightContext
    hotel_context: HotelContext
