from react_agent.domain.criterias import SearchCriteria
from ..state import State
from ..entities.entities import NumberUpdate, TimeUpdate
from datetime import timedelta, datetime
from ..utils import apply_list_update, apply_numeric_update, apply_time_update
from typing import Optional, List
from pydantic import BaseModel, Field

class SanitizeEquipmentCriteria(BaseModel):
    equipment: Optional[List[str]] = Field(default=None, description="List of preferred gym equipments")


def update_training_goal(current_criterias, extracted_criteria):
    """Update training goal if provided."""
    if extracted_criteria.training_goal is not None:
        current_criterias.goal = extracted_criteria.training_goal

def update_gender(current_criterias, extracted_criteria):
    """Update gender preference if provided."""
    if extracted_criteria.gender is not None:
        current_criterias.gender = extracted_criteria.gender

def update_experience_years(current_criterias, extracted_criteria):
    """Update minimum experience years if provided."""
    if extracted_criteria.min_experience_years is not None:
        new_exp = apply_numeric_update(
            current_criterias.min_experience_years, extracted_criteria.min_experience_years
        )
        current_criterias.min_experience_years = int(new_exp) if new_exp is not None else None

def update_certificates(current_criterias, extracted_criteria):
    """Update certificates list if provided."""
    if extracted_criteria.certificates is not None:
        current_certs = current_criterias.certificates
        if isinstance(current_certs, list):
            current_certs = set(current_certs)
            
        updated_list = apply_list_update(
            list(current_certs) if current_certs else [], 
            extracted_criteria.certificates
        )
        current_criterias.certificates = set(updated_list)

def update_equipments_and_facilities(current_criterias, extracted_criteria):
    """Update equipment and facilities list if provided."""
    if extracted_criteria.equipments_and_facilities is not None:
        ops = extracted_criteria.equipments_and_facilities
        current_equip = current_criterias.equipments_and_facilities
        if isinstance(current_equip, list):
            current_equip = set(current_equip)

        updated_list = apply_list_update(
            list(current_equip) if current_equip else [], 
            ops
        )
        current_criterias.equipments_and_facilities = set(updated_list)

def update_distance(current_criterias, extracted_criteria):
    """Update distance in meters if provided."""
    if extracted_criteria.distance_in_meters is not None:
        new_dist = apply_numeric_update(
            current_criterias.distance_in_meters, extracted_criteria.distance_in_meters
        )
        current_criterias.distance_in_meters = int(new_dist) if new_dist is not None else 5000

def update_max_price(current_criterias, extracted_criteria):
    """Update maximum price if provided."""
    if extracted_criteria.max_price is not None:
        new_price = apply_numeric_update(
            current_criterias.max_price, extracted_criteria.max_price
        )
        current_criterias.max_price = int(new_price) if new_price is not None else None

def update_rating(current_criterias, extracted_criteria):
    """Update rating if provided."""
    if extracted_criteria.rating is not None:
        new_rating = apply_numeric_update(
            current_criterias.rating, extracted_criteria.rating
        )
        current_criterias.rating = float(new_rating) if new_rating is not None else None

def update_open_hours(current_criterias, extracted_criteria):
    """Update open hours if provided."""
    if extracted_criteria.open_hours is not None:
        current_criterias.open_hours = apply_time_update(
            current_criterias.open_hours, extracted_criteria.open_hours
        )

def update_close_hours(current_criterias, extracted_criteria):
    """Update close hours if provided."""
    if extracted_criteria.close_hours is not None:
        current_criterias.close_hours = apply_time_update(
            current_criterias.close_hours, extracted_criteria.close_hours
        )

def update_user_criteria(state: State) -> SearchCriteria:
    """Update existing criteria - handles list merging for equipment."""
    
    extracted_criteria = state.extracted_criteria
    current_criterias = state.search_criteria
    
    update_training_goal(current_criterias, extracted_criteria)
    update_gender(current_criterias, extracted_criteria)
    update_experience_years(current_criterias, extracted_criteria)
    update_certificates(current_criterias, extracted_criteria)
    update_equipments_and_facilities(current_criterias, extracted_criteria)
    update_distance(current_criterias, extracted_criteria)
    update_max_price(current_criterias, extracted_criteria)
    update_rating(current_criterias, extracted_criteria)
    update_open_hours(current_criterias, extracted_criteria)
    update_close_hours(current_criterias, extracted_criteria)
    
    return current_criterias
