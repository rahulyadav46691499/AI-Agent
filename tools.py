from models import Flight, Hotel
import uuid
import random

def search_flights(origin: str, destination: str, travel_dates: str, passengers: int) -> list[Flight]:
    return [
        Flight(
            id=str(uuid.uuid4())[:8],
            airline="Air India",
            origin=origin,
            destination=destination,
            departure_time="08:00 AM",
            price=round(5500.0 + random.uniform(500, 1500), 2)
        ),
        Flight(
            id=str(uuid.uuid4())[:8],
            airline="IndiGo",
            origin=origin,
            destination=destination,
            departure_time="11:30 AM",
            price=round(3500.0 + random.uniform(200, 800), 2),
            cancellation_policy="Non-refundable"
        ),
        Flight(
            id=str(uuid.uuid4())[:8],
            airline="Vistara",
            origin=origin,
            destination=destination,
            departure_time="06:00 PM",
            price=round(7000.0 + random.uniform(1000, 2500), 2)
        )
    ]

def search_hotels(city: str, check_in: str, check_out: str, guests: int) -> list[Hotel]:
    return [
        Hotel(
            id=str(uuid.uuid4())[:8],
            name="Taj Palace Hotel",
            city=city,
            price_per_night=15500.0,
            room_type="Luxury Suite",
            amenities=["Free WiFi", "Breakfast", "Pool", "Gym", "Spa"]
        ),
        Hotel(
            id=str(uuid.uuid4())[:8],
            name="Lemon Tree Hotel",
            city=city,
            price_per_night=4500.0,
            room_type="Standard Room",
            amenities=["Free WiFi"]
        ),
        Hotel(
            id=str(uuid.uuid4())[:8],
            name="The Leela Palace",
            city=city,
            price_per_night=22000.0,
            room_type="Royal Club Parlour",
            amenities=["Free WiFi", "Spa", "Pool", "Breakfast", "Butler Service"],
            cancellation_policy="Non-refundable within 7 days of check-in."
        )
    ]

def book_flight(flight_id: str, passenger_details: str) -> bool:
    # Simulate payment processing successfully
    return True

def book_hotel(hotel_id: str, guest_details: str) -> bool:
    # Simulate payment processing successfully
    return True
