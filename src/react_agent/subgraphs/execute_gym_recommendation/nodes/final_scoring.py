from typing import Dict, Any, List
from ..state import State

def final_scoring(state: State) -> State:
    gyms = state.candidates
    final_results = []

    max_travel_time_minutes = 15
    for gym in gyms:
        score = gym.partial_score
        travel_time = gym.real_duration_min
        if travel_time > max_travel_time_minutes:
            penalty = (travel_time - max_travel_time_minutes) * 2
            score -= int(penalty)
        else:
            # Bonus for being super close
            score += 10
            
        gym.score_breakdown.distance = score
        gym.final_score = score
        final_results.append(gym)
    
    # Sort by new score and take Top 5
    final_results.sort(key=lambda x: x.final_score, reverse=True)
    state.final_candidates = final_results[:5]
    return state