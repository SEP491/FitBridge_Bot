from ..state import State

def final_scoring(state: State) -> State:
    """Calculate final scores for PT candidates based on travel time."""
    pts = state.candidates
    final_results = []

    max_travel_time_minutes = 15
    for pt in pts:
        score = pt.partial_score
        travel_time = pt.real_duration_min
        
        if travel_time is not None:
            if travel_time > max_travel_time_minutes:
                penalty = (travel_time - max_travel_time_minutes) * 2
                score -= int(penalty)
            else:
                # Bonus for being super close
                score += 10
            
        pt.score_breakdown.distance = score - pt.partial_score  # Store distance contribution
        pt.final_score = score
        final_results.append(pt)
    
    # Sort by final score and take Top 5
    final_results.sort(key=lambda x: x.final_score or 0, reverse=True)
    state.final_candidates = final_results[:5]
    return state