from langgraph.types import Command
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool, InjectedToolCallId
from typing_extensions import Annotated
from react_agent.infrastructure import get_google_maps_client
from react_agent.domain.entities import UserOrigin, SearchCenter
from typing import Literal
import asyncio


@tool
async def extract_locations(
    address: Annotated[str, "The location string to geocode (e.g., 'District 1', 'Home')."],
    location_type: Annotated[
        Literal["search_center", "user_origin"], 
        "The type of location: 'search_center' (where to look for gyms) or 'user_origin' (user's current physical spot)."
    ],
    tool_call_id: Annotated[str, InjectedToolCallId],
):
    """
    Geocode a location string into coordinates and update the appropriate state context.
    Use this when the user specifies a location for searching or navigation.
    """
    
    try:
        def _sync_geocode():
            gmaps = get_google_maps_client()
            return gmaps.geocode(address, region='vn')
        
        # Offload blocking geocode call to thread
        geocode_results = await asyncio.to_thread(_sync_geocode)
        
        if not geocode_results:
            return Command(
                update={
                    "messages": [ToolMessage(
                        content=f"Could not find coordinates for: '{address}'. Please try a more specific address.",
                        tool_call_id=tool_call_id
                    )]
                }
            )
        
        # Get the first (most relevant) result
        location_data = geocode_results[0]['geometry']['location']
        formatted_address = geocode_results[0].get('formatted_address', address)
        
        latitude = location_data['lat']
        longitude = location_data['lng']
        
        state_update = {}
        success_message = ""

        if location_type == "search_center":
            state_update["search_center"] = SearchCenter(latitude=latitude, longitude=longitude)
            success_message = f"Search area set to: {formatted_address}"
            
        elif location_type == "user_origin":
            state_update["user_origin"] = UserOrigin(latitude=latitude, longitude=longitude)
            success_message = f"Current user location set to: {formatted_address}"

        state_update["messages"] = [
            ToolMessage(
                content=f"{success_message} ({latitude:.4f}, {longitude:.4f})", 
                tool_call_id=tool_call_id
            )
        ]

        return Command(update=state_update)
        
    except Exception as e:
        error_msg = f"Error processing location: {str(e)}"
        return Command(
            update={
                "messages": [ToolMessage(content=error_msg, tool_call_id=tool_call_id)]
            }
        )