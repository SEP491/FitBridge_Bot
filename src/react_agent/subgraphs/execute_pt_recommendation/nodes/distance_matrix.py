from ..state import State
from ..entities.entities import RetrievedPtAsset
from react_agent.infrastructure import get_google_maps_client
from datetime import datetime
import asyncio

async def distance_matrix(state: State) -> State:
    """Calculate the distance matrix between the user's location and the PTs."""
    candidates = state.candidates
    if not candidates:
        return state
        
    user_loc = (state.user_origin.latitude, state.user_origin.longitude)    
    destinations = [(pt.latitude, pt.longitude) for pt in candidates if pt.latitude is not None and pt.longitude is not None]
    
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
    
    enriched_pts = []
    rows = matrix['rows'][0]['elements']
    
    for idx, row in enumerate(rows):
        if row['status'] == 'OK':
            real_distance_m = row['distance']['value']
            real_duration_s = row['duration_in_traffic']['value']  # Seconds
            
            pt = candidates[idx]
            pt.real_distance = real_distance_m
            pt.real_duration_min = real_duration_s / 60
            enriched_pts.append(pt)
            
    state.candidates = enriched_pts
    return state
