from langgraph.types import Command
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool, InjectedToolCallId
from langgraph.prebuilt import InjectedState
from typing_extensions import Annotated
from react_agent.infrastructure import get_google_maps_client
from react_agent.domain.entities import UserLocation
from ..state import State
import asyncio


@tool
async def extract_user_location(
    address: str,
    state: Annotated[State, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
):
    """Extract and geocode user's location from an address or place name using Google Maps API.
    
    Use this tool when the user provides their location as an address, place name, or landmark
    instead of coordinates. Examples:
    - "I'm at Quận 1, Ho Chi Minh City" -> "Quận 1, Thành phố Hồ Chí Minh"
    - "Near Landmark 81" -> "Landmark 81"
    - "123 Nguyen Hue Street" -> "123 Nguyễn Huệ, Quận 1, Thành phố Hồ Chí Minh"
    Extract the address, there should be only names and nouns
    
    Args:
        address: The address, place name, or landmark to geocode into coordinates.
    """
    
    try:
        def _sync_geocode():
            gmaps = get_google_maps_client()
            return gmaps.geocode(address)
        
        # Offload blocking geocode call to thread
        geocode_results = await asyncio.to_thread(_sync_geocode)
        
        if not geocode_results:
            return Command(
                update={
                    "messages": [ToolMessage(
                        content=f"Could not find location for: '{address}'. Please provide a more specific address or coordinates.",
                        tool_call_id=tool_call_id
                    )]
                }
            )
        
        # Get the first (most relevant) result
        location = geocode_results[0]['geometry']['location']
        formatted_address = geocode_results[0].get('formatted_address', address)
        
        latitude = location['lat']
        longitude = location['lng']
        
        new_user_location = UserLocation(
            latitude=latitude,
            longitude=longitude
        )
        
        success_message = f"Location set successfully!\n- Address: {formatted_address}\n- Coordinates: ({latitude:.6f}, {longitude:.6f})"
        
        return Command(
            update={
                "user_location": new_user_location,
                "messages": [ToolMessage(content=success_message, tool_call_id=tool_call_id)]
            }
        )
        
    except Exception as e:
        error_msg = f"Failed to geocode location: {str(e)}"
        return Command(
            update={
                "messages": [ToolMessage(content=error_msg, tool_call_id=tool_call_id)]
            }
        )
