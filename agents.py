from typing import Literal
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field

from state import AppState
from models import FlightContext, HotelContext
from tools import search_flights, search_hotels, book_flight, book_hotel
from langchain_core.messages import AIMessage

import os

# Initialize Gemini 2.5 Flash
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    temperature=0,
    api_key=os.getenv("GOOGLE_API_KEY")
)

class RouterDecision(BaseModel):
    active_service: Literal["flight", "hotel"]
    reasoning: str

def route_request(state: AppState):
    """Router node to determine which service to invoke or resume."""
    messages = state.get("messages", [])
    current_service = state.get("active_service")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are the routing layer of a Smart Travel Companion. "
                   "Your job is to determine whether the user wants to interact with the flight booking service or the hotel booking service. "
                   "If they are asking a follow-up question, determine which service it applies to. "
                   "Current active service: {current_service}. "
                   "If context switching is detected (e.g. they were doing flights, but now ask about hotels), switch the service. "
                   "Return 'flight' or 'hotel'."),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    chain = prompt | llm.with_structured_output(RouterDecision)
    decision = chain.invoke({
        "messages": messages,
        "current_service": current_service or "None"
    })
    
    return {"active_service": decision.active_service}

class FlightExtraction(BaseModel):
    origin: str | None = Field(description="Departure city")
    destination: str | None = Field(description="Arrival city")
    travel_dates: str | None = Field(description="Dates of travel")
    passengers: int | None = Field(description="Number of passengers")
    selected_flight_id: str | None = Field(description="ID of the flight if user selected one")
    passenger_details: str | None = Field(description="Passenger details for booking")
    user_message: str = Field(description="Response to the user guiding them to next step, or answering their question based on search results.")

def flight_agent(state: AppState):
    """Handles flight booking logic and memory updates."""
    messages = state.get("messages", [])
    context = state.get("flight_context", FlightContext())
    
    system_prompt = """You are the Flight Booking Agent of a Smart Travel Companion.
Your current context state: {context_json}

Instructions:
1. Extract or update parameters from the conversation: origin, destination, travel_dates, passengers.
2. Invalidation logic: If the user changes origin, destination, or travel dates, you MUST invalidate the current `selected_flight_id` and any `results`, returning to 'search' flow state (even if currently in verify or book).
3. Context awareness: Answer questions regarding the `results` list if the user asks (e.g., 'which one is refundable?').
4. Do NOT re-ask for information you already have in the context.
5. Ask for one missing parameter at a time.
6. Provide a user-friendly response guiding them to the next step.

Currently, your outputs will update the context fields.
"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    chain = prompt | llm.with_structured_output(FlightExtraction)
    extraction = chain.invoke({"messages": messages, "context_json": context.model_dump_json()})
    
    # Invalidation check
    if extraction.origin and extraction.origin != context.origin and context.origin is not None:
        context.results = []
        context.selected_flight_id = None
        context.flow_state = "search"
    if extraction.destination and extraction.destination != context.destination and context.destination is not None:
         context.results = []
         context.selected_flight_id = None
         context.flow_state = "search"
    if extraction.travel_dates and extraction.travel_dates != context.travel_dates and context.travel_dates is not None:
         context.results = []
         context.selected_flight_id = None
         context.flow_state = "search"
    
    # Update context parameters
    context.origin = extraction.origin or context.origin
    context.destination = extraction.destination or context.destination
    context.travel_dates = extraction.travel_dates or context.travel_dates
    context.passengers = extraction.passengers or context.passengers
    
    response_message = extraction.user_message

    # Flow Management
    if context.flow_state == "search":
        if context.origin and context.destination and context.travel_dates and context.passengers:
            # We have all info, so do a search
            flights = search_flights(context.origin, context.destination, context.travel_dates, context.passengers)
            context.results = flights
            context.flow_state = "verify"
            response_message = "Here are the flights I found:\n" + "\n".join([f"- {f.id}: {f.airline}, {f.departure_time}, ₹{f.price}" for f in flights]) + "\nWhich one would you like to select?"

    elif context.flow_state == "verify":
        if extraction.selected_flight_id:
            valid_ids = [f.id for f in context.results]
            if extraction.selected_flight_id in valid_ids:
                context.selected_flight_id = extraction.selected_flight_id
                selected_flight = next(f for f in context.results if f.id == context.selected_flight_id)
                context.flow_state = "book"
                response_message = f"Great, you selected {selected_flight.airline} for ₹{selected_flight.price}. To book, please provide the passenger names."

    elif context.flow_state == "book":
        if extraction.passenger_details:
             context.passenger_details = extraction.passenger_details
             success = book_flight(context.selected_flight_id, context.passenger_details)
             if success:
                 context.booking_confirmed = True
                 context.flow_state = "completed"
                 response_message = "Booking confirmed! Simulating payment success. Your flight is booked. How else can I help?"

    return {"flight_context": context, "messages": [AIMessage(content=response_message)]}

class HotelExtraction(BaseModel):
    city: str | None = Field(description="City for hotel stay")
    check_in: str | None = Field(description="Check-in date")
    check_out: str | None = Field(description="Check-out date")
    guests: int | None = Field(description="Number of guests")
    selected_hotel_id: str | None = Field(description="ID of the hotel if user selected one")
    guest_details: str | None = Field(description="Guest details for booking")
    user_message: str = Field(description="Response to the user guiding them to next step, or answering their question based on search results.")

def hotel_agent(state: AppState):
    """Handles hotel booking logic and memory updates."""
    messages = state.get("messages", [])
    context = state.get("hotel_context", HotelContext())
    
    system_prompt = """You are the Hotel Booking Agent of a Smart Travel Companion.
Your current context state: {context_json}

Instructions:
1. Extract or update parameters from the conversation: city, check_in, check_out, guests.
2. Invalidation logic: If the user changes city, check_in, or check_out, you MUST invalidate the current `selected_hotel_id` and any `results`, returning to 'search' flow state.
3. Context awareness: Answer questions regarding the `results` list if the user asks (e.g., 'what are the amenities?').
4. Do NOT re-ask for information you already have in the context.
5. Provide a user-friendly response guiding them to the next step.

Currently, your outputs will update the context fields.
"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    chain = prompt | llm.with_structured_output(HotelExtraction)
    extraction = chain.invoke({"messages": messages, "context_json": context.model_dump_json()})
    
     # Invalidation check
    if extraction.city and extraction.city != context.city and context.city is not None:
        context.results = []
        context.selected_hotel_id = None
        context.flow_state = "search"
    if extraction.check_in and extraction.check_in != context.check_in and context.check_in is not None:
         context.results = []
         context.selected_hotel_id = None
         context.flow_state = "search"
    if extraction.check_out and extraction.check_out != context.check_out and context.check_out is not None:
         context.results = []
         context.selected_hotel_id = None
         context.flow_state = "search"
         
    # Update context
    context.city = extraction.city or context.city
    context.check_in = extraction.check_in or context.check_in
    context.check_out = extraction.check_out or context.check_out
    context.guests = extraction.guests or context.guests
    
    response_message = extraction.user_message

    # Flow Management
    if context.flow_state == "search":
        if context.city and context.check_in and context.check_out and context.guests:
            # We have all info, so do a search
            hotels = search_hotels(context.city, context.check_in, context.check_out, context.guests)
            context.results = hotels
            context.flow_state = "verify"
            response_message = "Here are the hotels I found:\n" + "\n".join([f"- {h.id}: {h.name}, {h.room_type}, ₹{h.price_per_night}/night" for h in hotels]) + "\nWhich one would you like to select?"
            
    elif context.flow_state == "verify":
         if extraction.selected_hotel_id:
            valid_ids = [h.id for h in context.results]
            if extraction.selected_hotel_id in valid_ids:
                context.selected_hotel_id = extraction.selected_hotel_id
                selected_hotel = next(h for h in context.results if h.id == context.selected_hotel_id)
                context.flow_state = "book"
                response_message = f"Great, you selected {selected_hotel.name} for ₹{selected_hotel.price_per_night}/night. To book, please provide the guest details."
                
    elif context.flow_state == "book":
        if extraction.guest_details:
             context.guest_details = extraction.guest_details
             success = book_hotel(context.selected_hotel_id, context.guest_details)
             if success:
                 context.booking_confirmed = True
                 context.flow_state = "completed"
                 response_message = "Booking confirmed! Simulating payment success. Your hotel is booked. How else can I help?"

    return {"hotel_context": context, "messages": [AIMessage(content=response_message)]}
