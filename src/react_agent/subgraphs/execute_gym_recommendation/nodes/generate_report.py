from react_agent.domain.entities import GymAsset, PTAsset


from ..state import State

def generate_report(state: State) -> State:
    """Synthesize candidates and distances into a final markdown report for the user."""
    if not state.candidates:
        state.final_report = "I couldn't find any gyms that match your specific goals and location criteria at the moment."
        return state

    source_list = state.final_candidates
    
    report_lines = [
        "## 🏋️ Recommended Gyms for You\n",
        "Based on your fitness goals and current location, here are the best matches:\n"
    ]

    for i, gym in enumerate[GymAsset | PTAsset](source_list[:3], 1):
        gym_id = gym.id
        name = gym.name
        address = gym.address
        distance = gym.real_distance
        duration = gym.real_duration_min
        found_equip = gym.found_equip
        rating = gym.rating
        price = gym.price

        report_lines.append(f"### {i}. {name}")
        report_lines.append(f"[//]: # (ID: {gym_id})")
        report_lines.append(f"- **Rating**: ⭐ {rating}/5")
        report_lines.append(f"- **Location**: {address}")
        report_lines.append(f"- **Minimum Price**: {price} VND")
        
        if duration is not None:
            report_lines.append(f"- **Distance (Travel Time)**: 🚗 ~{distance:.0f} meters (~{duration:.0f} mins)")
        
        if found_equip:
            report_lines.append(f"\n**Matched Equipments**: {', '.join(found_equip)}")
        
        related = gym.related_recommendations
        if related:
            report_lines.append(f"\n**Related Recommendations**: {', '.join(related[:3])}")
        
        report_lines.append("") # Spacer

    state.final_report = "\n".join(report_lines)
    return state