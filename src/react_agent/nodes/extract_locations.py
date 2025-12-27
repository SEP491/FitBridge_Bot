"""Node for extracting and updating location information from messages.

This node processes conversation messages to automatically extract location
information, classify intent (search_center vs user_origin), geocode addresses,
and update the state accordingly.
"""

import asyncio
import json
import logging
from typing import Dict, Optional

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate

from react_agent.domain.entities import UserOrigin, SearchCenter
from react_agent.infrastructure import get_google_maps_client, get_model
from react_agent.state import State

logger = logging.getLogger(__name__)

LOCATION_EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a location extraction assistant. Analyze the user's message to extract location information.

Your task is to:
1. Identify if the user mentions a location (address, district, landmark, etc.)
2. Classify the intent:
   - "search_center": User wants to search for gyms/PTs in this location
     Keywords: "find gyms in", "look around", "show me places near", "search in", "change search area to", "find in"
   - "user_origin": User is stating their current physical location
     Keywords: "I am at", "My current location is", "I'm leaving from", "I'm currently at", "I'm at"
   - "both": User says "near me" or "around here" - set both to same location
   - "none": No location mentioned or intent unclear

3. Extract the location string (address, district name, landmark, etc.)

Return ONLY a JSON object with this structure:
{{
  "has_location": true/false,
  "location_type": "search_center" | "user_origin" | "both" | "none",
  "address": "extracted location string" or null,
  "confidence": "high" | "medium" | "low"
}}

If no location is found or intent is unclear, return:
{{
  "has_location": false,
  "location_type": "none",
  "address": null,
  "confidence": "low"
}}

Be strict - only extract if you're confident about the location and intent."""),
    ("human", "User message: {message}\n\nCurrent state:\n- Search center: {search_center_status}\n- User origin: {user_origin_status}\n\nExtract location information:")
])


async def extract_locations(state: State) -> Dict:
    """Extract location information from messages and update state.

    This node:
    1. Analyzes the latest user messages for location mentions
    2. Uses LLM to classify intent (search_center vs user_origin)
    3. Geocodes addresses using Google Maps
    4. Updates state with extracted locations

    Args:
        state: The current state containing messages and location data

    Returns:
        Dictionary with state updates (user_origin, search_center)
    """
    # Get the latest messages
    messages = [msg for msg in state.messages]
    if not messages:
        return {}

    latest_messages = messages[-10:]
    message_content = "\n".join([msg.content for msg in latest_messages])

    # Check current location status
    search_center_status = "NOT SET"
    if state.search_center and state.search_center.latitude is not None and state.search_center.longitude is not None:
        search_center_status = f"SET (lat: {state.search_center.latitude}, lon: {state.search_center.longitude})"

    user_origin_status = "NOT SET"
    if state.user_origin and state.user_origin.latitude is not None and state.user_origin.longitude is not None:
        user_origin_status = f"SET (lat: {state.user_origin.latitude}, lon: {state.user_origin.longitude})"

    # Use LLM to extract location information
    model = get_model()
    prompt = LOCATION_EXTRACTION_PROMPT.format_messages(
        message=message_content,
        search_center_status=search_center_status,
        user_origin_status=user_origin_status
    )

    try:
        response = await model.ainvoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)

        # Parse JSON response
        # Extract JSON from response (handle markdown code blocks if present)
        response_text = response_text.strip()
        if response_text.startswith("```"):
            # Remove markdown code block markers
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1]) if len(lines) > 2 else response_text

        extraction_result = json.loads(response_text)

        if not extraction_result.get("has_location") or extraction_result.get("location_type") == "none":
            logger.debug("No location found in message")
            return {}

        address = extraction_result.get("address")
        location_type = extraction_result.get("location_type")
        confidence = extraction_result.get("confidence", "low")

        if not address or confidence == "low":
            logger.debug(f"Low confidence or missing address: {extraction_result}")
            return {}

        # Geocode the address
        def _sync_geocode():
            gmaps = get_google_maps_client()
            return gmaps.geocode(address, region='vn')

        geocode_results = await asyncio.to_thread(_sync_geocode)

        if not geocode_results:
            logger.warning(f"Could not geocode address: {address}")
            return {}

        # Extract coordinates
        location_data = geocode_results[0]['geometry']['location']
        latitude = location_data['lat']
        longitude = location_data['lng']

        # Update state based on location type
        updates = {}

        if location_type == "search_center":
            updates["search_center"] = SearchCenter(latitude=latitude, longitude=longitude)
            logger.info(f"Updated search_center: {address} ({latitude}, {longitude})")

        elif location_type == "user_origin":
            updates["user_origin"] = UserOrigin(latitude=latitude, longitude=longitude)
            logger.info(f"Updated user_origin: {address} ({latitude}, {longitude})")

        elif location_type == "both":
            # Set both to the same location
            updates["search_center"] = SearchCenter(latitude=latitude, longitude=longitude)
            updates["user_origin"] = UserOrigin(latitude=latitude, longitude=longitude)
            logger.info(f"Updated both locations: {address} ({latitude}, {longitude})")

        return updates

    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse LLM response as JSON: {response_text[:200]}")
        return {}
    except Exception as e:
        logger.exception(f"Error extracting locations: {e}")
        return {}

