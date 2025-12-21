from datetime import UTC, datetime
from typing import Dict, List, cast

from langchain_core.messages import AIMessage, ToolMessage
from langgraph.runtime import Runtime

from react_agent.context import Context
from react_agent.state import State
from react_agent.tools import TOOLS
from react_agent.utils import load_chat_model
from react_agent.prompts import SYSTEM_PROMPT

async def call_model(
    state: State, runtime: Runtime[Context]
) -> Dict[str, List[AIMessage]]:
    """Call the LLM powering our "agent".

    This function prepares the prompt, initializes the model, and processes the response.

    Args:
        state (State): The current state of the conversation.
        runtime (Runtime[Context]): Runtime context for the model run.

    Returns:
        dict: A dictionary containing the model's response message.
    """
    # Initialize the model with tool binding. Change the model or add more tools here.
    model = load_chat_model(runtime.context.model).bind_tools(TOOLS)

    # Build explicit location status for LLM
    location_status = "NOT SET - Ask user for their location"
    if state.user_location and state.user_location.latitude is not None and state.user_location.longitude is not None:
        location_status = f"SET (lat: {state.user_location.latitude}, lon: {state.user_location.longitude})"
    
    # Build explicit criteria status for LLM
    criteria = state.search_criteria
    
    goal_status = f"SET: {criteria.goal}" if criteria.goal else "NOT SET"
    
    # Gym-related criteria
    equip_list = list(criteria.equipments_and_facilities) if criteria.equipments_and_facilities else []
    equipment_status = f"SET: {', '.join(equip_list)}" if equip_list else "NOT SET"
    
    # PT-related criteria  
    cert_list = list(criteria.certificates) if criteria.certificates else []
    certificates_status = f"SET: {', '.join(cert_list)}" if cert_list else "NOT SET"
    
    gender_status = f"SET: {criteria.gender}" if criteria.gender else "NOT SET"
    experience_status = f"SET: {criteria.min_experience_years} years" if criteria.min_experience_years else "NOT SET"
    price_status = f"SET: {criteria.max_price} VND" if criteria.max_price else "NOT SET"
    
    # Check if minimum criteria for search is met
    can_search_gym = bool(criteria.goal or equip_list)
    can_search_pt = bool(criteria.goal or cert_list)
    
    # Track last tool call to prevent repetition
    last_tool_called = None
    has_recommendation_results = bool(state.final_report)
    
    # Find the last AI message with tool calls
    for msg in reversed(state.messages):
        if isinstance(msg, AIMessage) and msg.tool_calls:
            last_tool_called = msg.tool_calls[0].get("name", "unknown")
            break
    
    tool_status = ""
    if last_tool_called:
        tool_status = f"\nLAST ACTION:\n- Last tool called: {last_tool_called}\n- DO NOT call '{last_tool_called}' again unless user explicitly requests a new search.\n"
    
    if has_recommendation_results:
        tool_status += f"- Recommendation results ALREADY GENERATED. Present them to the user instead of calling tools again.\n"
    
    state_summary = (
        f"CURRENT SEARCH STATE:\n"
        f"- User Location: {location_status}\n"
        f"- Training Goal: {goal_status}\n"
        f"- Gym Equipment/Facilities: {equipment_status}\n"
        f"- PT Certificates: {certificates_status}\n"
        f"- Gender Preference: {gender_status}\n"
        f"- Min Experience Years: {experience_status}\n"
        f"- Max Price: {price_status}\n"
        f"\n"
        f"SEARCH READINESS:\n"
        f"- Can search gyms: {'YES' if can_search_gym else 'NO - Need training goal OR equipment preferences'}\n"
        f"- Can search PTs: {'YES' if can_search_pt else 'NO - Need training goal OR certificate preferences'}\n"
        f"{tool_status}"
    )
    print(state_summary)

    current_time = datetime.now(tz=UTC).isoformat()
    full_system_content = (
        f"{SYSTEM_PROMPT.format(system_time=current_time)}\n\n"
        f"{state_summary}"
    )

    response = cast( # type: ignore[redundant-cast]
        AIMessage,
        await model.ainvoke(
            [{"role": "system", "content": full_system_content}, *state.messages]
        ),
    )

    # Handle the case when it's the last step and the model still wants to use a tool
    if state.is_last_step and response.tool_calls:
        return {
            "messages": [
                AIMessage(
                    id=response.id,
                    content="Sorry, I could not find an answer to your question in the specified number of steps.",
                )
            ]
        }

    # Return the model's response as a list to be added to existing messages
    return {"messages": [response]}