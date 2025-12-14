from agent.utils.state.MessageState import OverallState, UpdateOperations
from agent import get_model
from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage

class SanitizeEquipmentCriteria(BaseModel):
    preferred_equipments: Optional[list[str]] = Field(default=None, description="List of preferred gym equipments")

def update_equipment_criteria(state: OverallState) -> OverallState:
    """
    Update equipment criteria based on UpdateOperations from extracted criteria.
    
    Applies add/remove operations to state.gyms_preferences.preferred_equipments:
    - criteria.equipments_and_facilities.add -> append to existing list
    - criteria.equipments_and_facilities.remove -> remove from existing list
    
    Returns dict with updated gyms_preferences to merge into state.
    """
    
    criteria = state.extracted_criteria
    # Skip if no equipment updates requested
    if criteria.equipments_and_facilities is None:
        return state
    
    ops: UpdateOperations = criteria.equipments_and_facilities
    
    # Get current equipment list (default to empty if None)
    current_equipments = []
    if state.gyms_preferences and state.gyms_preferences.preferred_equipments:
        current_equipments = list(state.gyms_preferences.preferred_equipments)
    
    if ops.remove:
        remove_lower = {item.lower() for item in ops.remove}
        current_equipments = [
            equip for equip in current_equipments 
            if equip.lower() not in remove_lower
        ]
    
    if ops.add:
        existing_lower = {equip.lower() for equip in current_equipments}
        for item in ops.add:
            if item.lower() not in existing_lower:
                current_equipments.append(item)
                existing_lower.add(item.lower())
    
    if ops.overwrite:
        current_equipments = ops.overwrite
    
    updated_preferences = state.gyms_preferences.model_copy() if state.gyms_preferences else None

    equipment_string = ", ".join(current_equipments)
    sanitize_model = get_model().with_structured_output(SanitizeEquipmentCriteria)
    result = sanitize_model.invoke([
        SystemMessage(content="""
        You are a gym equipment expert. Your task is to sanitize and standardize a list of gym equipment names.

        INSTRUCTIONS:
        1. Remove exact duplicates and case-insensitive duplicates
        2. Standardize equipment names to their most common/proper form
        3. Remove any invalid or non-existent gym equipment
        4. Merge similar equipment types (e.g., "treadmill" and "running machine" -> "treadmill")
        5. Use proper capitalization and spelling

        EXAMPLES:
        - "treadmill", "Treadmill", "TREADMILL" -> ["treadmill"]
        - "dumbell", "dumbbell" -> ["dumbbell"] 
        - "bench press", "bench" -> ["bench press"]
        - "pool", "swimming pool" -> ["swimming pool"]

        Return only valid, standardized gym equipment names without duplicates."""),
        HumanMessage(content=equipment_string)
    ])
    print("Sanitized equipment criteria:", result)

    if updated_preferences:
        updated_preferences.preferred_equipments = result.preferred_equipments
    

    state.gyms_preferences = updated_preferences
    print("Updated equipment criteria:", state.gyms_preferences)
    return state