from agent.utils.state.MessageState import OverallState, RetrievedGyms
from agent import get_model
from langchain_core.messages import HumanMessage, SystemMessage

INITIAL_SEARCH_SYSTEM_MESSAGE = """
You are FitBridge, an expert fitness consultant. Your goal is to help users find the *best available* gym options from the provided list.

### INPUT DATA EXPLANATION:
- You will receive a list of "RECOMMENDED GYMS".
- This list has **already been filtered** by a search engine to find the closest matches in the database.
- **CRITICAL:** The gyms in this list are the ONLY options available. You cannot invent new gyms.

### YOUR CORE INSTRUCTIONS:
1. **Always Recommend:** Never say "I found no gyms" if the list contains gyms. Even if the user asked for "under 10k VND" and the cheapest gym is "120k VND", you MUST recommend the 120k gym.
2. **Handle Imperfect Matches (The "Consultant" Approach):**
   - If a gym exceeds the user's budget or distance, acknowledge it politely but explain why it's still a good choice.
   - *Example:* "I couldn't find anything under 10k VND, but **MiBell** is the most affordable option at 123k and fits your chest workout goals perfectly."
3. **Focus on the "Why":** Connect the gym's features to their specific fitness goals (Chest, Triceps, Shoulders).
4. **No Raw Scores:** Do not show the internal match score.
### RESPONSE STRUCTURE:
1. **Acknowledge the Goal:** "I found some great places for your chest and triceps workout."
2. **The "Reality Check" (If needed):** "While I didn't find any gyms under [User Budget], here are the best value options nearby:"
3. **The Recommendations:** List all fields of the final gym results.
4. **Call to Action:** "Would you like to know more about any of these?"

### TONE:
Helpful, encouraging, and solution-oriented. Respond in the same language as the user.
"""

def format_gym_for_display(gym: RetrievedGyms, rank: int) -> str:
    """Format a single gym's details for LLM context."""
    return f"""
{rank}. {gym.name}
   - Open hours: {gym.open_hours} - {gym.close_hours}
   - Lowest price: {gym.price} VND 
   - Rating: {gym.rating}/5
   - Address: {gym.address}
   - Distance: {gym.real_distance} meters ({gym.real_duration_min:.1f} minutes by car)
   - Coordinates: ({gym.lat}, {gym.lon})
   - Matched equipments: {', '.join(gym.found_equip) if gym.found_equip else 'None specified'}
   - Notes: #### Provide the most prominent features that match the user's goals.
"""


def build_system_context(state: OverallState) -> str:
    """Build system context with user preferences."""
    gyms_prefs = state.gyms_preferences
    
    context = "### USER'S FITNESS PREFERENCES:\n"
    
    if gyms_prefs:
        if gyms_prefs.goals:
            context += f"- Fitness goals: {gyms_prefs.goals}\n"
        if gyms_prefs.preferred_equipments:
            context += f"- Required equipment: {', '.join(gyms_prefs.preferred_equipments)}\n"
        if gyms_prefs.max_price:
            context += f"- Maximum price: {gyms_prefs.max_price} VND\n"
        if gyms_prefs.distance_in_meters:
            context += f"- Maximum distance: {gyms_prefs.distance_in_meters} meters\n"
        if gyms_prefs.rating:
            context += f"- Minimum rating: {gyms_prefs.rating}/5\n"
        if gyms_prefs.open_hours and gyms_prefs.close_hours:
            context += f"- Preferred hours: {gyms_prefs.open_hours} - {gyms_prefs.close_hours}\n"
    else:
        context += "- No specific preferences provided\n"
    
    return context


def build_gyms_context(state: OverallState) -> str:
    """Build formatted list of recommended gyms."""
    final_gyms = state.final_gyms
    
    print(f"Final gyms wiht length: {len(final_gyms)}")
    if not final_gyms or len(final_gyms) == 0:
        return "\n### SEARCH RESULTS:\nNo gyms were found matching the user's criteria. Suggest they broaden their search parameters."
    
    formatted_gyms = "\n".join([
        format_gym_for_display(gym, idx + 1) 
        for idx, gym in enumerate(final_gyms)
    ])
    
    return f"\n### RECOMMENDED GYMS (Ranked by Best Match):\n{formatted_gyms}"


def llm_response(state: OverallState) -> dict:
    """Generate LLM response with recommendations based on user preferences and gym results."""
    model = get_model()
    
    # Build comprehensive system message with role + context
    base_system_message = INITIAL_SEARCH_SYSTEM_MESSAGE
    preferences_context = build_system_context(state)
    gyms_context = build_gyms_context(state)
    
    system_message = SystemMessage(content=f"""
    {base_system_message}

    {preferences_context}
    {gyms_context}
    """)

    # print (f"System message: {system_message}")
    
    human_message = HumanMessage(content=state.user_question or "Find me gyms that match my preferences")
    messages = [system_message, human_message]
    response = model.invoke(messages)
    return {"messages": [system_message, human_message, response]}