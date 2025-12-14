from agent.utils.state.MessageState import OverallState

def should_continue_gym_retrieval(state: OverallState):
    """Check if the user wants to continue the gym retrieval process."""
    if state.candidate_gyms and len(state.candidate_gyms) > 0:
        return "calculate_distance_point"
    else:
        return "llm_response"