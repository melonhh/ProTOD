"""旅游领域工具"""
from typing import List
from langchain_core.tools import tool

@tool 
def search_itinerary(where: str, when: str, who: str, budget: str, demand: str) -> str:
    """
    Search for an itinerary based on user requirements
    Args:
        where (str): The destination of the itinerary.
        when (str): The date or time period for the itinerary.
        who (str): The person or group for whom the itinerary is planned.
        budget (str): The budget for the itinerary.
        demand (str): Specific demands or preferences for the itinerary.
    Returns:
        str: A itinerary.
    """
    
    return f"search itinerary: where={where}, when={when}, who={who}, budget={budget}, demand={demand}"


@tool
def search_stay(where: str, when: str, who: str, budget: str, demand: str) -> List[str]:
    """
    Search for accommodation options based on user requirements
    Args:
        where (str): The location for the stay.
        when (str): The date or time period for the stay.
        who (str): The person or group for whom the stay is planned.
        budget (str): The budget for the stay.
        demand (str): Specific demands or preferences for the stay.
    Returns:
        List[str]: A list of accommodation options.
    """
    
    return [f"{where}/{when}/{who}/{budget}/{demand}"]


@tool
def handle_booking(name: str) -> str:
    """
    Handles the booking process.
    Args:
        name (str): The name of the accommodation or service to be booked.
    Returns:
        str: A confirmation message indicating the booking has been handled.
    """
    
    return f"{name}: Booking handled successfully!"