from ..state import State
from react_agent.infrastructure import get_PtCertificateVectorIndex
import re
import asyncio

def escape_lucene_special_chars(term: str) -> str:
    """Escape special characters that have meaning in Lucene query syntax."""
    # Lucene special characters: + - && || ! ( ) { } [ ] ^ " ~ * ? : \ /
    special_chars = r'([+\-&|!(){}[\]^"~*?:\\/])'
    return re.sub(special_chars, r'\\\1', term)

async def extract_pt_certificates(state: State) -> State:
    """Extract the PT certificates related to the goal from the state."""
    if state.search_criteria.goal is None:
        return state
    
    def sync_extract():
        vector_index = get_PtCertificateVectorIndex()
        # similarity_search_with_score is sync, which is fine inside a thread
        return vector_index.similarity_search_with_score(state.search_criteria.goal, k=5)

    search_results = await asyncio.to_thread(sync_extract)
    certificates_from_search = [doc.page_content for doc, score in search_results]

    if state.search_criteria.certificates is None:
        state.search_criteria.certificates = set()
    
    # Defensive check: if it came back as a list from the LangGraph checkpointer
    if isinstance(state.search_criteria.certificates, list):
        state.search_criteria.certificates = set(state.search_criteria.certificates)

    extracted_certificates = []
    raw_certificates = certificates_from_search or []
    print(raw_certificates)
    for term in raw_certificates:
        # Use regex to find "certName: " or "certName\: " (handling potential existing escapes)
        name_match = re.search(r"certName\\?:\s*(.*)", term)
        if name_match:
            # Extract name and strip any trailing newlines or extra metadata
            name = name_match.group(1).split('\n')[0].strip()
            extracted_certificates.append(name)
        else:
            extracted_certificates.append(term.strip())

    if len(extracted_certificates) > 0:
        escaped_query_terms = [escape_lucene_special_chars(name) for name in extracted_certificates]
        state.search_criteria.certificates.update(escaped_query_terms)

    return state
