from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from agent import get_model
from langchain_openai import ChatOpenAI
from agent.utils.state.MessageState import OverallState
class PrunedQuery(BaseModel):
    pruned_query: str = Field(default=None, description="Pruned query for gym or PT")

def query_prune(state: OverallState):
    user_query = state["messages"][-1].content
    pruner = get_model().with_structured_output(PrunedQuery)
    system_message = SystemMessage(content="""
    You are a Query Sanitizer and Intent Extractor for a Gym Database.
    
    ### YOUR GOAL:
    Extract search parameters into the defined schema. You must aggressively PRUNE irrelevant information.

    ### PRUNING RULES:
    1. **Conversational Fillers:** Remove words like "Like", "So basically", "Um", "I was wondering".
    2. **Personal Identity:** Remove statements of fact about the user's life, relationships, or orientation (e.g., "I'm gay", "I broke up", "I'm sad").
    3. **Exceptions:** - If the user asks for a specific environment (e.g., "Gay-friendly gym"), KEEP that in 'social_preferences'.
       - If the user says "I am gay" (identity only), REMOVE it.

    ### INFERENCE RULES:
    1. **Implicit Goals:** If user says "my arms are twigs", map to fitness_goal: "hypertrophy" or "build muscle".
    2. **Implicit Equipment:** If user asks for "cardio", assume "Treadmill, Elliptical" in facility_requirements.
    """)
    pruned_query = pruner.invoke([
        system_message,
        HumanMessage(content=user_query)
    ])
    return {"user_query": pruned_query.pruned_query}
