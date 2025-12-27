from ..state import State

def _format_experience(months: int) -> str:
    """Format experience months as 'X years Y months' or 'X months'."""
    if months is None or months == 0:
        return "N/A"
    years = months // 12
    remaining_months = months % 12
    if years > 0 and remaining_months > 0:
        return f"{years} year{'s' if years > 1 else ''} {remaining_months} month{'s' if remaining_months > 1 else ''}"
    elif years > 0:
        return f"{years} year{'s' if years > 1 else ''}"
    else:
        return f"{remaining_months} month{'s' if remaining_months > 1 else ''}"

def generate_report(state: State) -> State:
    """Synthesize PT candidates into a final markdown report for the user."""
    if not state.candidates:
        state.final_report = "I couldn't find any personal trainers that match your specific goals and location criteria at the moment."
        return state

    source_list = state.final_candidates or state.candidates
    
    report_lines = [
        "## Recommended Personal Trainers for You\n",
        "Based on your fitness goals and current location, here are the best matches:\n"
    ]

    for i, pt in enumerate(source_list[:3], 1):
        pt_id = pt.id
        name = pt.name
        address = pt.address
        distance = pt.real_distance
        duration = pt.real_duration_min
        experience_months = pt.experience_months
        gender = pt.gender
        price = pt.price
        found_certs = pt.found_certificates
        all_certs = pt.certificates

        report_lines.append(f"### {i}. {name}")
        report_lines.append(f"[//]: # (ID: {pt_id})")
        report_lines.append(f"- **Gender**: {gender.capitalize() if gender else 'N/A'}")
        report_lines.append(f"- **Experience**: {_format_experience(experience_months)}")
        report_lines.append(f"- **Location**: {address}")
        report_lines.append(f"- **Minimum Price**: {price:,} VND" if price else "- **Price**: Contact for pricing")
        
        if duration is not None:
            report_lines.append(f"- **Distance (Travel Time)**: ~{distance:,} meters (~{duration:.0f} mins by car)")
        elif distance is not None:
            report_lines.append(f"- **Distance**: ~{distance:,} meters")
        
        if found_certs:
            report_lines.append(f"\n**Matched Certificates**: {', '.join(found_certs)}")
        
        if all_certs:
            other_certs = [c for c in all_certs if c not in (found_certs or [])]
            if other_certs:
                report_lines.append(f"\n**Other Certifications**: {', '.join(other_certs[:5])}")
        
        report_lines.append("")  # Spacer

    state.final_report = "\n".join(report_lines)
    return state