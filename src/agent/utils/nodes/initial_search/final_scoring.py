from typing import Dict, Any, List
from agent.utils.state.MessageState import OverallState

def final_scoring(state: OverallState) -> OverallState:
    gyms = state.candidate_gyms
    final_results = []

    max_travel_time_minutes = 15
    for gym in gyms:
        # 1. Start with the Neo4j Score (Equipment + Price + Rating)
        score = gym.partial_score
        
        # 2. Apply "Real World" Penalty
        # Example: Lose 2 points for every minute over 15 mins
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
    print(final_results)
    return {"final_gyms": final_results[:5]}