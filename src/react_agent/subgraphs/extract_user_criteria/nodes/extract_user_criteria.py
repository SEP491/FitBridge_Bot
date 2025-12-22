from ..state import State
from ..entities.entities import ExtractedUserCriteria
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from react_agent.infrastructure import get_model

async def extract_user_criteria(state: State) -> State:
    """Extract user criteria modifications from query for gym or PT search."""
    system_prompt = f"""Extract the user's search criteria modifications from the messages history. This can be for GYM search or PERSONAL TRAINER (PT) search. Return the criterias in english.

    ### CRITICAL DISTINCTION - SEARCH TYPE vs CRITERIA:
    These keywords indicate SEARCH TYPE only - they are NOT equipment, facilities, or certificates:
    
    GYM SEARCH TYPE KEYWORDS (DO NOT extract as equipment):
    - English: "gym", "fitness center", "workout place", "fitness studio"
    - Vietnamese: "phòng gym", "phòng tập", "trung tâm thể hình", "nơi tập"
    
    PT SEARCH TYPE KEYWORDS (DO NOT extract as certificates):
    - English: "personal trainer", "PT", "coach", "instructor", "trainer"
    - Vietnamese: "huấn luyện viên", "HLV", "PT", "người hướng dẫn"

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

    ### LIST FIELD HANDLING (equipments_and_facilities & certificates):
    Determine what the user wants to OVERWRITE, ADD or REMOVE:
    - "add a", "also want", "include", "thêm" -> add
    - "remove a", "don't need", "no more", "bỏ", "không cần" -> remove
    - "add a and remove b" -> add and remove
    - "only", "just", "only want", "chỉ cần" -> overwrite
    - First time mentioning items without current values -> overwrite

    ### GYM-SPECIFIC FIELDS:
    - equipments_and_facilities: ONLY physical items INSIDE a gym
      - VALID: "squat rack", "treadmill", "cable machine", "dumbbells", "yoga mat", "máy chạy bộ", "tạ"
      - INVALID: "gym", "phòng gym", "fitness center" (these are search type, NOT equipment)
    - rating: "better rated", "4.5 stars", "highly rated" -> extract rating (0.0-5.0)
    - open_hours/close_hours: "opens at 6am", "closes late", "24 hours" -> extract times (HH:MM:SS format)

    ### PT-SPECIFIC FIELDS:
    - gender: "female trainer", "male PT", "prefer a woman", "nữ", "nam" -> extract as "male" or "female"
    - min_experience_years: "experienced", "5+ years", "at least 3 years experience" -> extract number
    - certificates: ONLY certification/qualification names
      - VALID: "NASM", "yoga certified", "nutrition certification", "chứng chỉ yoga", "bằng dinh dưỡng"
      - INVALID: "PT", "trainer", "huấn luyện viên" (these are search type, NOT certificates)

    ### COMMON FIELDS:
    - distance_in_meters: "closer", "within 1km", "nearby", "gần", "trong vòng 1km" -> extract distance in meters
    - max_price: "cheaper", "under 500000 VND", "budget friendly", "rẻ hơn" -> extract price in VND
    - training_goal: "weight loss", "build muscle", "cardio", "giảm cân", "tăng cơ" -> extract goal

    ### FLEXIBILITY RULES (Translate Vague Terms):
    - "Increase/Raise/Higher/Tăng" (Price, Distance): Add 20% to current value
    - "Decrease/Lower/Cheaper/Giảm/Rẻ hơn" (Price, Distance): Subtract 10% from current value
    - "Further/More options/Xa hơn" (Distance): Add 20%
    - "Closer/Nearby/Gần hơn" (Distance): Subtract 10%
    - "Later/Muộn hơn" (Close Time): Add 1 hour
    - "Earlier/Sớm hơn" (Open Time): Subtract 1 hour
    - "More experienced/Kinh nghiệm hơn" (min_experience_years): Add 2 years or set to 5 if not set

    Return None for fields not mentioned in the query.
    """
    
    # Filter messages to only include HumanMessages (user input)
    # Exclude AIMessages with tool_calls to avoid unresolved tool call errors
    filtered_messages = [
        msg for msg in state.messages
        if isinstance(msg, HumanMessage) or 
        (isinstance(msg, AIMessage) and not msg.tool_calls)
    ]
    
    criteria_parser = get_model().with_structured_output(ExtractedUserCriteria)
    result = await criteria_parser.ainvoke([
        SystemMessage(content=system_prompt),
        *filtered_messages
    ])

    state.extracted_criteria = result
    print("Extracted criteria:", state.extracted_criteria)
    return state