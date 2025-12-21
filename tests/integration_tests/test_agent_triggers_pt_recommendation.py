import pytest
from react_agent.domain.entities import UserLocation
from react_agent.domain.criterias import SearchCriteria
from react_agent.graph import graph
from react_agent.context import Context


@pytest.mark.anyio
async def test_agent_triggers_pt_recommendation():
    # 1. User message that SHOULD trigger the PT recommendation tool
    messages = [
        ("user", "I want to find a personal trainer who can help me with weight loss. I prefer a female trainer with certified personal trainer certification. ")
    ]
    
    context = Context(
        system_prompt="You are a fitness assistant. Use the 'get_pt_recommendations' tool when the user asks for personal trainers.",
        model="openai/gpt-4o-mini"
    )

    # 2. Run the agent
    res = await graph.ainvoke(
        {
            "messages": messages, 
            "user_location": UserLocation(latitude=10.875, longitude=106.800),
            "search_criteria": SearchCriteria(certificates=["Certified Personal Trainer"])
        }, 
        context=context
    )

    # 3. Verify tool usage
    print("\n--- Agent Response ---")
    print(res)
    
    # Check if final_report made it to the main state (Blackbox verification)
    assert res["final_report"] is not None, "Main state failed to capture subgraph report"
    print("\n--- Agent Report (Length: {}) ---".format(len(res["final_report"])))
    print(res["final_report"])
    
    # Verify report structure
    assert res["final_report"].startswith("##"), "Report should start with markdown header"


# @pytest.mark.anyio
# async def test_pt_recommendation_with_gender_filter():
#     """Test PT recommendation with specific gender preference."""
#     messages = [
#         ("user", "Find me a male personal trainer for strength training.")
#     ]
    
#     context = Context(
#         system_prompt="You are a fitness assistant. Use the 'get_pt_recommendations' tool when the user asks for personal trainers.",
#         model="openai/gpt-4o-mini"
#     )

#     res = await graph.ainvoke(
#         {
#             "messages": messages, 
#             "user_location": UserLocation(latitude=10.875, longitude=106.800)
#         }, 
#         context=context
#     )

#     assert res["final_report"] is not None, "Main state failed to capture subgraph report"
#     print("\n--- PT Recommendation with Gender Filter ---")
#     print(res["final_report"])


# @pytest.mark.anyio
# async def test_pt_recommendation_with_experience_requirement():
#     """Test PT recommendation with minimum experience years."""
#     messages = [
#         ("user", "I need an experienced personal trainer with at least 5 years of experience.")
#     ]
    
#     context = Context(
#         system_prompt="You are a fitness assistant. Use the 'get_pt_recommendations' tool when the user asks for personal trainers.",
#         model="openai/gpt-4o-mini"
#     )

#     res = await graph.ainvoke(
#         {
#             "messages": messages, 
#             "user_location": UserLocation(latitude=10.875, longitude=106.800)
#         }, 
#         context=context
#     )

#     assert res["final_report"] is not None, "Main state failed to capture subgraph report"
#     print("\n--- PT Recommendation with Experience Requirement ---")
#     print(res["final_report"])

