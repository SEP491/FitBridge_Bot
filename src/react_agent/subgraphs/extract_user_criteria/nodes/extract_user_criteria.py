from ..state import State
from ..entities.entities import ExtractedUserCriteria
from langchain_core.messages import SystemMessage, HumanMessage
from react_agent.infrastructure import get_model

async def extract_user_criteria(state: State) -> State:
    """Extract user criteria modifications from query for gym or PT search."""
    system_prompt = f"""Extract the user's search criteria modifications from their message. This can be for GYM search or PERSONAL TRAINER (PT) search.

    ### CURRENT VALUES:
    - distance_in_meters: {state.search_criteria.distance_in_meters}
    - max_price: {state.search_criteria.max_price}
    - training_goal: {state.search_criteria.goal}
    
    GYM-SPECIFIC:
    - rating: {state.search_criteria.rating}
    - open_hours: {state.search_criteria.open_hours}
    - close_hours: {state.search_criteria.close_hours}
    - equipments_and_facilities: {state.search_criteria.equipments_and_facilities}
    
    PT-SPECIFIC:
    - gender: {state.search_criteria.gender}
    - min_experience_years: {state.search_criteria.min_experience_years}
    - certificates: {state.search_criteria.certificates}

    ### SEARCH TYPE DETECTION:
    - GYM SEARCH: Keywords like "gym", "fitness center", "workout place", "equipment", "machines", "squat rack", "treadmill"
    - PT SEARCH: Keywords like "personal trainer", "PT", "coach", "instructor", "trainer", "certificates", "certification"

    ### LIST FIELD HANDLING (equipments_and_facilities & certificates):
    Determine what the user wants to OVERWRITE, ADD or REMOVE:
    - "add a", "also want", "include" -> add
    - "remove a", "don't need", "no more" -> remove
    - "add a and remove b" -> add and remove
    - "only", "just", "only want" -> overwrite
    - First time mentioning items without current values -> overwrite

    ### GYM-SPECIFIC FIELDS:
    - equipments_and_facilities: "has squat rack", "with treadmills", "cable machines" -> extract equipment names
    - rating: "better rated", "4.5 stars", "highly rated" -> extract rating (0.0-5.0)
    - open_hours/close_hours: "opens at 6am", "closes late", "24 hours" -> extract times (HH:MM:SS format)

    ### PT-SPECIFIC FIELDS:
    - gender: "female trainer", "male PT", "prefer a woman" -> extract as "male" or "female"
    - min_experience_years: "experienced", "5+ years", "at least 3 years experience" -> extract number
    - certificates: "yoga certified", "has NASM", "with nutrition certification" -> extract certificate names

    ### COMMON FIELDS:
    - distance_in_meters: "closer", "within 1km", "nearby" -> extract distance in meters
    - max_price: "cheaper", "under 500000 VND", "budget friendly" -> extract price in VND
    - training_goal: "weight loss", "build muscle", "cardio", "flexibility", "strength training" -> extract goal

    ### FLEXIBILITY RULES (Translate Vague Terms):
    - "Increase/Raise/Higher" (Price, Distance): Add 20% to current value
    - "Decrease/Lower/Cheaper" (Price, Distance): Subtract 10% from current value
    - "Further/More options/Bigger area" (Distance): Add 20%
    - "Closer/Nearby" (Distance): Subtract 10%
    - "Later" (Close Time): Add 1 hour
    - "Earlier" (Open Time): Subtract 1 hour
    - "More experienced" (min_experience_years): Add 2 years or set to 5 if not set

    Return None for fields not mentioned in the query.
    """
    
    criteria_parser = get_model().with_structured_output(ExtractedUserCriteria)
    result = await criteria_parser.ainvoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=state.user_query)
    ])

    state.extracted_criteria = result
    print("Extracted criteria:", state.extracted_criteria)
    return state