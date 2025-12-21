from ..state import State
from react_agent.domain.entities import GymAsset, PTAsset
from react_agent.infrastructure import get_google_maps_client
from datetime import datetime
import asyncio

async def distance_matrix(state: State) -> State:
    """Calculate the distance matrix between the user's location and the gyms."""
    candidates = state.candidates
    if not candidates:
        return state
        
    user_loc = (state.user_location.latitude, state.user_location.longitude)    
    destinations = [(gym.latitude, gym.longitude) for gym in candidates if gym.latitude is not None and gym.longitude is not None]
    
    if not destinations:
        return state

    def _sync_gmaps_call():
        gmaps = get_google_maps_client()
        return gmaps.distance_matrix(
            origins=[user_loc],
            destinations=destinations,
            mode="driving",
            departure_time=datetime.now()
        )

    try:
        # Offload lazy-loading and API call to a thread
        matrix = await asyncio.to_thread(_sync_gmaps_call)
    except Exception as e:
        print(f"Failed to calculate distance: {str(e)}")
        state.error_code = 500
        state.error = f"Failed to calculate distance: {str(e)}"
        return state
    
    enriched_gyms = []
    rows = matrix['rows'][0]['elements']
    
    for idx, row in enumerate(rows):
        if row['status'] == 'OK':
            real_distance_m = row['distance']['value']
            real_duration_s = row['duration_in_traffic']['value'] # Seconds
            
            gym = candidates[idx]
            gym.real_distance = real_distance_m
            gym.real_duration_min = real_duration_s / 60
            enriched_gyms.append(gym)
            
    state.candidates = enriched_gyms
    return state
