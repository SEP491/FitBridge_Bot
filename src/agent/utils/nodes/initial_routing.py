from agent import get_model
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from typing import Literal
from agent.utils.state.MessageState import OverallState
import json

class InitialRoutingDecision(BaseModel):
    decision: Literal["modify_criteria", "assistant_chat"] = Field(description="""
    Decision of the initial routing. Choose 'modify_criteria' if the user is asking to modify the criteria for the search. Choose 'assistant_chat' for greetings, clarifications, or follow-ups.
    """)

def initial_routing(state: OverallState) -> str:
    print ("User question:", state.user_question)
    if state.user_question is None:
        return "initial_search"

    router_llm = get_model().with_structured_output(InitialRoutingDecision)
    # Convert Pydantic models to dict for JSON serialization
    prefs_json = json.dumps(state.gyms_preferences.model_dump() if state.gyms_preferences else None)
    gyms_json = json.dumps([g.model_dump() for g in state.final_gyms] if state.final_gyms else None)
    
    ROUTER_SYSTEM_PROMPT = f"""
    You are a smart Assistant Router for a Gym Recommendation System.

    ### CONTEXT:
    The user has just received a list of recommended gyms based on these search criterias:
    {prefs_json}

    The gyms currently displayed to the user are:
    {gyms_json}

    ### YOUR JOB:
    Analyze the user's follow-up message and decide the next workflow step.
    
    ### KEY DISTINCTION: QUESTIONS vs STATEMENTS
    
    **QUESTIONS** (seeking information) -> assistant_chat
    - Genuine questions asking about gym details, features, comparisons
    - Examples: "Does MiBell have a pool?", "What equipment does the first gym have?", "Which one is closest?"
    - Test: Can this be answered by looking up info about the listed gyms?
    
    **STATEMENTS/COMMANDS** (wanting to change search) -> modify_criteria  
    - Declarative statements expressing desire to change parameters
    - Examples: "I want something cheaper", "Add yoga", "Remove cardio equipment", "Actually, closer to home"
    - Test: Does this require searching for DIFFERENT gyms?
    
    **RHETORICAL QUESTIONS** (actually statements) -> modify_criteria
    - Questions that imply dissatisfaction and request change
    - Examples: "Can you find something cheaper?", "Isn't there anything closer?", "What about gyms with a pool?"
    - Test: The user isn't asking for info, they're requesting a NEW search with different criteria

    ### CLASSIFICATION RULES:

    1. **modify_criteria** (Re-run Search)
    - User wants to CHANGE search constraints
    - Statements: "Cheaper", "Closer", "Add X", "Remove Y", "I want...", "Actually..."
    - Rhetorical requests: "Can you find...", "What about...", "Isn't there...", "How about..."
    - Logic: Requires querying database for *different* gyms

    2. **assistant_chat** (Answer from Context)
    - User asks genuine QUESTIONS about the gyms already shown
    - Info requests: "Tell me about...", "What are the hours?", "Does X have Y?", "Compare..."
    - Clarifications: "What does that mean?", "Can you explain..."
    - Logic: Answer lies within the metadata of gyms currently displayed
    """

    response = router_llm.invoke([
        SystemMessage(content=ROUTER_SYSTEM_PROMPT),
        HumanMessage(content=state.user_question)
    ])
    print("Initial routing decision:", response.decision)
    return response.decision