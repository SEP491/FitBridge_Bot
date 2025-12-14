from datetime import datetime
from agent.utils.state.MessageState import OverallState, RetrievedGyms
from agent import get_google_maps_client

def calculate_distance_point(state: OverallState) -> OverallState:
    candidates = state.candidate_gyms 
    user_loc = (state.user_location.latitude, state.user_location.longitude)    
    gmaps = get_google_maps_client()
    # 1. Prepare Destinations for Batch Call
    # (Distance Matrix allows up to 25 destinations per call)
    destinations = [(gym.lat, gym.lon) for gym in candidates]
    
    # 2. Call Google API
    try:
        matrix = gmaps.distance_matrix(
            origins=[user_loc],
            destinations=destinations,
            mode="driving", # or "walking", "transit"
            departure_time=datetime.now() # Get traffic-aware time!
        )
    except Exception as e:
        print(f"Failed to calculate distance: {str(e)}")
        return {"error_code": 500, "error": f"Failed to calculate distance: {str(e)}"}
    
    # 3. Process Results
    enriched_gyms = []
    rows = matrix['rows'][0]['elements']
    
    for idx, row in enumerate(rows):
        if row['status'] == 'OK':
            real_distance_m = row['distance']['value']
            real_duration_s = row['duration_in_traffic']['value'] # Seconds
            
            # Combine with the gym object
            gym = candidates[idx]
            gym.real_distance = real_distance_m
            gym.real_duration_min = real_duration_s / 60
            enriched_gyms.append(gym)
            
    return {"candidate_gyms": enriched_gyms}