import json
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from utils.load_config import CONFIG

search_model = CONFIG.agents.hotel_search_agent.model


class HotelSearch(BaseModel):
    city: str = Field(..., description="City where user wants to search hotels")
    hotel_name: Optional[str] = Field(None, description="Specific hotel name the user is looking for")
    check_in: Optional[date] = Field(None, description="Check-in date")
    check_out: Optional[date] = Field(None, description="Check-out date")
    guests: Optional[int] = Field(None, description="Number of guests", gt=0)
    budget: Optional[float] = Field(None, description="Maximum budget per night in USD", gt=0)
    currency: Optional[str] = Field(None, description="Budget currency depending on location and user query (USD, Euro, PKR, etc)")

class HotelSummary(BaseModel):
    hotel_name: str
    city: str
    rating: float
    starting_price: float
    currency: str
    location: str
    amenities: list[str]


class HotelSummaryResults(BaseModel):
    hotels: list[HotelSummary]


class HotelAvailabilitySearch(BaseModel):
    hotel_name: str = Field(..., description="Name of the hotel to check availability for")
    city: str = Field(..., description="City where the hotel is located")
    check_in: Optional[date] = Field(None, description="Check-in date")
    check_out: Optional[date] = Field(None, description="Check-out date")
    guests: Optional[int] = Field(None, description="Number of guests", gt=0)


class HotelRoom(BaseModel):
    room_type: str
    description: str
    price_per_night: float
    currency: str
    is_available: bool


class HotelAvailabilityResult(BaseModel):
    hotel_name: str
    city: str
    rating: float
    is_fully_booked: bool
    rooms: list[HotelRoom]


@tool
def search_hotels(hotel_search: HotelSearch) -> HotelSummaryResults:
    """
    Search for hotels in a city. Use this when the user wants to discover or compare hotels.
    Works with partial information — city is the only required field.
    Returns a list of hotels with summary details, starting prices, amenities and availability.
    """
    
    filters = []
    if hotel_search.hotel_name:
        filters.append(f"hotel name: {hotel_search.hotel_name}")
    if hotel_search.budget:
        filters.append(f"budget under ${hotel_search.budget} per night")
    if hotel_search.guests:
        filters.append(f"for {hotel_search.guests} guests")
    if hotel_search.check_in and hotel_search.check_out:
        filters.append(f"checking in {hotel_search.check_in} checking out {hotel_search.check_out}")

    filter_str = ", ".join(filters) if filters else "general search"

    prompt = f"""Search for hotels in {hotel_search.city} ({filter_str}).
Return a JSON object matching this exact schema, with no extra text or markdown:
{json.dumps(HotelSummaryResults.model_json_schema(), indent=2)}

Use real hotel names, and provide accurate ratings (1.0 to 5.0), actual prices, and accurate amenities.
Set is_available to true for hotels with available bookings."""

    llm = ChatOpenAI(
        model=search_model,
    ).bind_tools([{"type": "web_search_preview"}])
    
    response = llm.invoke(prompt)
    hotels = [
        json.loads(t['text']) 
        for t in response.content if 'text' in t
    ][0]
    return HotelSummaryResults(**hotels)


@tool
def check_availability(availability_search: HotelAvailabilitySearch) -> HotelAvailabilityResult:
    """
    Check room availability and details for a specific hotel.
    Use this when the user has a particular hotel in mind and wants to know what rooms are available.
    """
    details = []
    if availability_search.check_in and availability_search.check_out:
        details.append(f"for dates {availability_search.check_in} to {availability_search.check_out}")
    if availability_search.guests:
        details.append(f"for {availability_search.guests} guests")

    detail_str = ", ".join(details) if details else ""

    prompt = f"""Check room availability for {availability_search.hotel_name} in {availability_search.city} {detail_str}.
Return a JSON object matching this exact schema, with no extra text or markdown:
{json.dumps(HotelAvailabilityResult.model_json_schema(), indent=2)}

Use real room types (Standard, Deluxe, Suite etc), realistic prices, and accurate descriptions."""

    llm = ChatOpenAI(
        model=search_model,
    ).bind_tools([{"type": "web_search_preview"}])
    
    response = llm.invoke(prompt)
    hotel_availability = [
        json.loads(t['text']) 
        for t in response.content if 'text' in t
    ][0]
    return HotelAvailabilityResult(**hotel_availability)


if __name__ == "__main__":
    print("--- search_hotels ---")
    result = search_hotels.invoke({"hotel_search": HotelSearch(city="Paris", budget=150.0)})
    print(result)

    print("\n--- check_availability ---")
    result = check_availability.invoke({"availability_search": HotelAvailabilitySearch(hotel_name="Crowne Plaza Paris", city="Paris")})
    print(result)
