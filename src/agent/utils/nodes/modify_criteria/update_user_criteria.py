from agent.utils.state.MessageState import OverallState, NumberUpdate, TimeUpdate
from datetime import timedelta
import datetime

def apply_numeric_update(current_value, update_data: NumberUpdate):
        if update_data.absolute_change is not None:
            return update_data.absolute_change
        elif update_data.relative_change is not None:
            # Assumes current_value is a number (int/float)
            return current_value + update_data.relative_change
        return current_value 

def apply_time_update(current_time_str: str, update_data: TimeUpdate):
    if update_data.absolute_change is not None:
        return update_data.absolute_change
        
    elif update_data.relative_change is not None:
        # Note: A placeholder date is required for datetime arithmetic
        placeholder_date = datetime.now().date()
        current_dt = datetime.combine(placeholder_date, datetime.strptime(current_time_str, "%H:%M:%S").time())
        
        # 2. Parse the relative change (ASSUMES LLM gives format like "+1 hour" or "+01:00:00")
        # This is the trickiest part; assuming LLM returns simple seconds for ease:
        # If your LLM returns seconds (e.g., 3600 or -3600) for relative_change:
        delta = timedelta(seconds=update_data.relative_change) 
        
        # If your LLM returns a complex string like "+1 hour", you'll need another LLM call or complex parsing
        
        updated_dt = current_dt + delta
        return updated_dt.strftime("%H:%M:%S")
        
    return current_time_str 
def update_user_criteria(state: OverallState) -> OverallState:
    """Update existing criteria - handles list merging for equipment."""
    
    # Handle equipment list with action-based logic
    criteria = state.extracted_criteria
    current_preferences = state.gyms_preferences
    if criteria.training_goal is not None:
        current_preferences.goals = criteria.training_goal

    # Numeric Updates
    if criteria.distance_in_meters is not None:
        current_preferences.distance_in_meters = apply_numeric_update(
            current_preferences.distance_in_meters, criteria.distance_in_meters
        )
    if criteria.max_price is not None:
        current_preferences.max_price = apply_numeric_update(
            current_preferences.max_price, criteria.max_price
        )
    if criteria.rating is not None:
        current_preferences.rating = apply_numeric_update(
            current_preferences.rating, criteria.rating
        )
    
    # Time Updates (Requires the current value to be a valid time string)
    if criteria.open_hours is not None:
        current_preferences.open_hours = apply_time_update(
            current_preferences.open_hours, criteria.open_hours
        )
    if criteria.close_hours is not None:
        current_preferences.close_hours = apply_time_update(
            current_preferences.close_hours, criteria.close_hours
        )
    print("Updated user criteria:", state.gyms_preferences)
    
    return state
