from agent import get_graph, get_model, get_GymAssetVectorIndex
from langchain_neo4j import Neo4jVector
from langchain_core.messages import SystemMessage, HumanMessage
from agent.utils.state.MessageState import OverallState, GymsPreferences
from langchain_core.prompts import ChatPromptTemplate
from agent.utils.tools.find_gyms_by_assets import find_gyms_by_assets
from pydantic import BaseModel, Field
from typing import Optional

class ProcessUserPreferencesOutput(BaseModel):
    is_goal_fitness_related: bool = Field(
        description="True ONLY if the goal is clearly related to fitness, exercise, or working out. False for vague, unrelated, or nonsensical goals like 'hmm', 'hello', 'elgato', random words, etc."
    )
    is_equipment_valid: bool = Field(
        description="True ONLY if at least one item in the equipment list is a real gym equipment. False if the list is empty, nonsensical, or contains no fitness equipment."
    )
    rejection_reason: Optional[str] = Field( # for debugging purposes
        default=None, 
        description="If is_goal_fitness_related or is_equipment_valid is False, explain why the input was rejected. Otherwise null."
    )
    corrected_preferred_equipments: Optional[list[str]] = Field(
        default=None, 
        description="Corrected equipment names with proper spelling. Return null if is_equipment_valid is False."
    )
    related_muscles: Optional[str] = Field(
        default=None, 
        description="Muscle groups related to the fitness goal. Return null if is_goal_fitness_related is False. Format: 'muscle1, muscle2, muscle3'"
    )

def process_user_preferences(state: OverallState) -> OverallState:
    """
    Validates and processes user fitness preferences.
    
    Flow:
    1. Extract gym preferences (equipment list and fitness goals) from state
    2. Validate inputs are fitness-related using LLM with structured output
    3. For equipment: correct spelling/vocabulary if valid gym equipment found
    4. For goals: extract related muscle groups if genuine fitness goal
    5. Return error if validation fails, otherwise continue processing
    """
    gyms_prefs = state.gyms_preferences
    if gyms_prefs is not None:
        preferred_equipments = gyms_prefs.preferred_equipments
        goals = gyms_prefs.goals
        
        # Check if both values are None
        if preferred_equipments is None and goals is None:
            return { "error_code": 400 , "error": "No preferred equipments or goals provided"}
            
        # Build system message based on available data
        systemMessage = """
            You are a strict fitness expert validator. You do NOT guess or hallucinate. You MUST first validate if the inputs are genuinely fitness-related before processing.

            CRITICAL VALIDATION RULES:
            - is_goal_fitness_related = True ONLY for clear fitness goals like "build muscle", "lose weight", "improve cardio", "get stronger", "tone my arms"
            - is_goal_fitness_related = False for: vague words ("hmm", "ok", "hello"), random words ("elgato", "banana"), non-fitness topics ("learn coding")
            - is_equipment_valid = True ONLY if there's at least one recognizable gym equipment (treadmill, dumbbell, barbell, bench press, etc.)
            - is_equipment_valid = False for: nonsense words, non-equipment items, empty or invalid lists

            If validation fails, set the corresponding output fields to null and provide a rejection_reason.
            """
        
        if preferred_equipments is not None:
            systemMessage += f"""
            TASK - Equipment Validation & Correction:
            Input equipment list: {preferred_equipments}
            - First, determine if ANY items are real gym equipment
            - If yes: correct spelling/vocabulary and return the cleaned list in corrected_preferred_equipments
            - If no: set is_equipment_valid=False, corrected_preferred_equipments=null
            """
        
        if goals is not None:
            systemMessage += f"""
            TASK - Goal Validation & Muscle Mapping:
            User's stated goal: "{goals}"
            - First, determine if this is a genuine fitness-related goal
            - If yes: list the specific muscle groups that would be trained for this goal in related_muscles
            - If no: set is_goal_fitness_related=False, related_muscles=null
            """
        
        chain = ChatPromptTemplate.from_template(systemMessage) | get_model().with_structured_output(ProcessUserPreferencesOutput)

        response = chain.invoke({"preferred_equipments": preferred_equipments, "goals": goals})
        # Check goal validation
        if goals is not None and not response.is_goal_fitness_related:
            return { 
                "error_code": 400, 
                "error": f"Invalid fitness goal: {response.rejection_reason or 'Goal is not fitness-related'}"
            }
        
        # Check equipment validation - if invalid but goal is valid, use vector search to find equipment
        print(response)
        if response.is_equipment_valid is False:
            if response.is_goal_fitness_related is True and response.related_muscles is not None:
                # Use related muscles to find relevant equipment via vector search
                vector_index = get_GymAssetVectorIndex()
                search_results = vector_index.similarity_search_with_score(response.related_muscles, k=5)
                # Extract equipment names from search results
                equipment_from_search = [doc.page_content for doc, score in search_results]
                gyms_prefs.preferred_equipments = equipment_from_search
            elif response.is_goal_fitness_related is True and response.related_muscles is None:
                return { 
                    "error_code": 500, 
                    "error": f"Invalid goal: LLM did not cook"
                }
            else:
                # Equipment is invalid and goal is not fitness-related
                return { 
                    "error_code": 400, 
                    "error": f"Invalid equipment: {response.rejection_reason or 'User has not provided any valid equipment'}"
                }
        elif response.corrected_preferred_equipments is not None:
            gyms_prefs.preferred_equipments = response.corrected_preferred_equipments
        else:
            return { 
                "error_code": 400, 
                "error": f"Invalid equipment: {response.rejection_reason or 'No valid gym equipment found'}"
            }
        if response.related_muscles is not None:
            gyms_prefs.goals = response.related_muscles
        print(f"Final state: equipments={gyms_prefs.preferred_equipments}, goals={gyms_prefs.goals}")
        return {"error_code": 200, "error": None, "gyms_prefs": gyms_prefs} # updated state with validated and corrected preferences
    else:
        # handle pt here
        return state
