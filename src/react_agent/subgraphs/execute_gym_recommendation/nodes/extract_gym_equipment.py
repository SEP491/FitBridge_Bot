from ..state import State
from react_agent.domain.entities import GymAsset, PTAsset
from react_agent.infrastructure import get_GymAssetVectorIndex
import re
import asyncio

def escape_lucene_special_chars(term: str) -> str:
    """Escape special characters that have meaning in Lucene query syntax."""
    # Lucene special characters: + - && || ! ( ) { } [ ] ^ " ~ * ? : \ /
    special_chars = r'([+\-&|!(){}[\]^"~*?:\\/])'
    return re.sub(special_chars, r'\\\1', term)

async def extract_gym_equipment(state: State) -> State:
    """Extract the gym equipments related to the goal from the state."""
    if state.search_criteria.goal is None:
        return state
    def sync_extract():
        vector_index = get_GymAssetVectorIndex()
        return vector_index.similarity_search_with_score(state.search_criteria.goal, k=5)
    search_results = await asyncio.to_thread(sync_extract)
    equipments_from_search = [doc.page_content for doc, score in search_results]

    if state.search_criteria.equipments_and_facilities is None:
        state.search_criteria.equipments_and_facilities = set()
    
    # Defensive check: if it came back as a list from the LangGraph checkpointer
    if isinstance(state.search_criteria.equipments_and_facilities, list):
        state.search_criteria.equipments_and_facilities = set(state.search_criteria.equipments_and_facilities)


    extracted_equipments = []
    raw_equipments = equipments_from_search or []
    for term in raw_equipments:
        # Use regex to find "name: " or "name\: " (handling potential existing escapes)
        name_match = re.search(r"name\\?:\s*(.*)", term)
        if name_match:
            # Extract name and strip any trailing newlines or extra metadata
            name = name_match.group(1).split('\n')[0].strip()
            extracted_equipments.append(name)
        else:
            extracted_equipments.append(term.strip())

    if len(extracted_equipments) > 0:
        escaped_query_terms = [escape_lucene_special_chars(equipment) for equipment in extracted_equipments]
        state.search_criteria.equipments_and_facilities.update(escaped_query_terms)

    return state
