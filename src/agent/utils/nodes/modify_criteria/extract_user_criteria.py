from agent.utils.state.MessageState import OverallState, ExtractedUserCriteria
from agent import get_model
from langchain_core.messages import SystemMessage, HumanMessage





def extract_user_criteria(state: OverallState) -> OverallState:
    """Extract user criteria modifications from query, including add/remove operations for equipment."""
    system_prompt = f"""Extract the user's gym search criteria modifications from their message. Use the current values of the criteria in case you need to ouput a reasonable relative change.
    Current values:
    - distance_in_meters: {state.gyms_preferences.distance_in_meters}
    - max_price: {state.gyms_preferences.max_price}
    - rating: {state.gyms_preferences.rating}
    - open_hours: {state.gyms_preferences.open_hours}
    - close_hours: {state.gyms_preferences.close_hours}
    - training_goal: {state.gyms_preferences.goals}
    ### EQUIPMENT HANDLING:
    For equipments_and_facilities, determine what the user wants to OVERWRITE, ADD or REMOVE:
    Keywords:
    - "add a", "also want", "include" -> add
    - "remove a", "don't need", "no more" -> remove
    - "add a and remove a", "add a and remove b" -> add and remove
    - "only, just a/the, only want" -> overwrite

    ### OTHER FIELDS:
    - distance_in_meters: "closer", "within 1km" -> extract distance
    - max_price: "cheaper", "under 1000" -> extract price
    - rating: "better rated", "4.5 stars" -> extract rating
    - open_hours/close_hours: "opens at 6am", "closes late" -> extract times
    - training_goal: "want to do cardio", "build muscle" -> extract goal

    ### FLEXIBILITY RULES (Translate Vague Terms):
    - "Increase/Raise/A bit/Higher" (Price, Distance, Rating): Add 20% to the current value.
    - "Decrease/Lower/A bit" (Price, Distance, Rating): Subtract 10% from the current value.
    - "Further/More options/Bigger area" (Distance): Add 20% to the current value.
    - "Closer/Tighter area" (Distance): Subtract 10% from the current value.
    - "Later/More time" (Close Time): Add 3600 seconds to the current value.
    - "Earlier/Less time" (Open Time): Subtract 3600 seconds from the current value.
    Return None for fields not mentioned in the query.

    """
    criteria_parser = get_model().with_structured_output(ExtractedUserCriteria)
    result = criteria_parser.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=state.user_question)
    ])

    state.extracted_criteria = result
    print("Extracted criteria:", state.extracted_criteria)
    return state