from agent.utils.state.MessageState import OverallState
from agent.utils.tools.get_gym_details_by_id import get_gym_details_by_id
from agent.utils.tools.get_gym_facilities import get_gym_facilities
from agent.utils.tools.get_gym_reviews_and_ratings import get_gym_reviews_and_ratings
from agent.utils.tools.get_gym_details_by_name import get_gym_details_by_name
from agent.utils.tools.get_gym_equipments import get_gym_equipments
from agent import get_model
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage


ASSISTANT_CHAT_SYSTEM_PROMPT = """You are FitBridge Assistant, a knowledgeable gym recommendation chatbot helping users find the perfect gym.

### YOUR TOOLS:
- get_gym_details_by_id: Get the details of a gym by its ID (uuid). Call only once
- get_gym_details_by_name: Get the details of a gym by its name. Only use this tool if you have no information about the gym's ID. Call only once
- get_gym_equipments: Get the equipments of a gym by gym's ID (uuid). Call only once. If equipment_name is provided, return the equipment with the given name. The limit is the maximum number of equipments to return. If user requires getting all: assign limit = -1, or it will return 5 equipments by default.
- get_gym_facilities: Get the facilities of a gym by gym's ID (uuid). Call only once. If facility_name is provided, return the facility with the given name. The limit is the maximum number of facilities to return. If user requires getting all: assign limit = -1, or it will return 5 facilities by default.
- get_gym_reviews_and_ratings: Get the reviews and ratings of a gym by gym's ID (uuid). Call only once.

### YOUR ROLE:
You're in a conversation with a user who has already received gym recommendations. They're now asking follow-up questions about specific gyms or seeking clarifications.

### CONTEXT PROVIDED:
You will receive:
- The list of recommended gyms with their basic details (name, distance, price, rating, equipment, hours)
- The user's original search preferences
- The user's current question

### RESPONSE GUIDELINES:
1. **Answer directly** based on the gym data already available in context
2. **Mention which tool you're "using"** when fetching specific info (e.g., "Let me check that using get_gym_details...")
3. **Be specific** - reference exact data from the gyms list
4. **Clarify when info is missing** - if data isn't available, suggest the user contact the gym directly
5. **Stay in context** - only discuss the gyms that were recommended
6. **Be conversational** - use natural language, not robotic responses
7. **Compare when asked** - if user asks "which is better?", use the comparison tool
8. **Provide actionable info** - include phone numbers, addresses, or next steps when relevant

### PROHIBITED:
- Don't start a NEW gym search (that's a different workflow)
- Don't make up gym details not in the provided data
- Don't recommend gyms not in the current list
- Never use anything as gym IDs from the users by any means.

### TONE:
Friendly, helpful, and knowledgeable. Think of yourself as a personal fitness concierge."""


def format_gym_summary(gym) -> str:
    
    """Format gym data for context."""
    equipment_str = ', '.join(gym.found_equip) if gym.found_equip else 'Not specified'
    return f"""
- **{gym.name}** (ID: {gym.id})
  Distance: {gym.dist_meters}m ({gym.real_duration_min:.1f} min drive)
  Price: {gym.price if hasattr(gym, 'price') else 'N/A'} VND
  Rating: {gym.rating if hasattr(gym, 'rating') else gym.partial_score}/5
  Hours: {gym.open_hours if hasattr(gym, 'open_hours') else 'N/A'} - {gym.close_hours if hasattr(gym, 'close_hours') else 'N/A'}
  Equipments matched with user's preferences: {equipment_str}
  Location: ({gym.lat}, {gym.lon})
"""


def build_gyms_context(state: OverallState) -> str:
    """Build context of available gyms."""
    if not state.final_gyms or len(state.final_gyms) == 0:
        return "No gyms currently in context."
    
    gyms_summary = "\n".join([
        format_gym_summary(gym) for gym in state.final_gyms
    ])
    return f"### GYMS IN CONTEXT:\n{gyms_summary}"


def build_preferences_context(state: OverallState) -> str:
    """Build user preferences context."""
    if not state.gyms_preferences:
        return "### USER PREFERENCES:\nNo specific preferences set."
    
    prefs = state.gyms_preferences
    context = "### USER PREFERENCES:\n"
    if prefs.goals:
        context += f"- Goals: {prefs.goals}\n"
    if prefs.preferred_equipments:
        context += f"- Required equipment: {', '.join(prefs.preferred_equipments)}\n"
    if prefs.max_price:
        context += f"- Max price: {prefs.max_price} VND\n"
    if prefs.distance_in_meters:
        context += f"- Max distance: {prefs.distance_in_meters}m\n"
    if prefs.rating:
        context += f"- Min rating: {prefs.rating}/5\n"
    
    return context

def assistant_chat(state: OverallState) -> dict:
    """Handle follow-up questions about recommended gyms using simulated tools."""

    model = get_model()
    tools = [get_gym_details_by_id, get_gym_details_by_name, get_gym_equipments, get_gym_facilities, get_gym_reviews_and_ratings]
    agent = model.bind_tools(tools)
    
    gyms_context = build_gyms_context(state)
    prefs_context = build_preferences_context(state)
    
    system_message = SystemMessage(content=f"""
    {ASSISTANT_CHAT_SYSTEM_PROMPT}

    {prefs_context}

    {gyms_context}
    """)
    
    user_question = state.user_question or "Tell me more about these gyms"
    human_message = HumanMessage(content=user_question)

    # print (f"System message: {system_message}")
    messages = [system_message, *state.messages, human_message]

    response = agent.invoke(messages)
    return {"messages": [response]} 