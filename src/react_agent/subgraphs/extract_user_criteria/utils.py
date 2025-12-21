from react_agent.subgraphs.extract_user_criteria.entities.entities import UpdateOperations
from datetime import datetime, timedelta
from react_agent.subgraphs.extract_user_criteria.entities.entities import NumberUpdate, TimeUpdate

def apply_list_update(current_list: list[str], update_data: UpdateOperations) -> list[str]:
    """
    Applies add, remove, and overwrite operations to a list of strings.
    Case-insensitive matching is used for remove and add checks, but original casing is preserved for additions.
    """
    if update_data.overwrite is not None:
        return update_data.overwrite
    
    current = list(current_list) if current_list else []
    
    if update_data.remove:
        remove_set = {item.lower() for item in update_data.remove}
        current = [item for item in current if item.lower() not in remove_set]
        
    if update_data.add:
        existing_lower = {item.lower() for item in current}
        for item in update_data.add:
            if item.lower() not in existing_lower:
                current.append(item)
                existing_lower.add(item.lower()) # Update local set to prevent adding duplicates within the same batch
    
    return current

def apply_numeric_update(current_value, update_data: NumberUpdate):
    val = current_value if current_value is not None else 0
    if update_data.absolute_change is not None:
        return update_data.absolute_change
    elif update_data.relative_change is not None:
        # Assumes current_value is a number (int/float)
        return val + update_data.relative_change
    return current_value 

def apply_time_update(current_time_str: str, update_data: TimeUpdate):
    if update_data.absolute_change is not None:
        return update_data.absolute_change
        
    elif update_data.relative_change is not None:
        if not current_time_str:
            return None # Cannot apply relative change to None
            
        # Note: A placeholder date is required for datetime arithmetic
        placeholder_date = datetime.now().date()
        try:
            current_dt = datetime.combine(placeholder_date, datetime.strptime(current_time_str, "%H:%M:%S").time())
        except ValueError:
             # Fallback if format doesn't match or other error
             return current_time_str
        
        # 2. Parse the relative change
        # Assuming LLM returns simple seconds for ease:
        try:
            # Check if relative_change is a string that looks like an int
            seconds = float(update_data.relative_change)
            delta = timedelta(seconds=seconds)
        except (ValueError, TypeError):
             # Complex string parsing not implemented here
             return current_time_str

        updated_dt = current_dt + delta
        return updated_dt.strftime("%H:%M:%S")
        
    return current_time_str 