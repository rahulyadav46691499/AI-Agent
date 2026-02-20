from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Flight(BaseModel):
    id: str
    airline: str
    origin: str
    destination: str
    departure_time: str
    price: float
    cancellation_policy: str = "Refundable up to 24h before departure."

class Hotel(BaseModel):
    id: str
    name: str
    city: str
    price_per_night: float
    room_type: str = "Standard"
    amenities: List[str] = ["Free WiFi", "Breakfast"]
    cancellation_policy: str = "Free cancellation 48h prior to check-in."

class FlightContext(BaseModel):
    flow_state: str = "search"  # search, verify, book
    origin: Optional[str] = None
    destination: Optional[str] = None
    travel_dates: Optional[str] = None
    passengers: Optional[int] = None
    results: List[Flight] = []
    selected_flight_id: Optional[str] = None
    passenger_details: Optional[str] = None
    booking_confirmed: bool = False

class HotelContext(BaseModel):
    flow_state: str = "search"  # search, verify, book
    city: Optional[str] = None
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    guests: Optional[int] = None
    results: List[Hotel] = []
    selected_hotel_id: Optional[str] = None
    guest_details: Optional[str] = None
    booking_confirmed: bool = False

class State(BaseModel):
    messages: List[Any]
    active_service: Optional[str] = None   # "flight", "hotel"
    flight_context: FlightContext = Field(default_factory=FlightContext)
    hotel_context: HotelContext = Field(default_factory=HotelContext)
