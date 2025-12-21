import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from react_agent.tools.update_search_state import update_search_state
from react_agent.state import State
from langchain_core.messages import AIMessage, ToolMessage
from react_agent.domain.criterias import SearchCriteria

@pytest.mark.asyncio
async def test_update_search_state_success():
    # Mock the subgraph graph
    with patch("react_agent.tools.update_search_state.extract_user_criteria_graph") as mock_graph:
        # Setup mock return value for the subgraph
        mock_criteria = SearchCriteria(goal="build muscle")
        mock_extracted = MagicMock()
        mock_extracted.model_dump_json.return_value = '{"training_goal": "build muscle"}'
        
        mock_graph.ainvoke = AsyncMock(return_value={
            "search_criteria": mock_criteria,
            "extracted_criteria": mock_extracted
        })

        # Setup input state
        mock_state = MagicMock(spec=State)
        messages = [
            AIMessage(
                content="I want to build muscle",
                tool_calls=[{"id": "call_123", "name": "update_search_state", "args": {}}]
            )
        ]
        mock_state.messages = messages
        
        mock_state.model_dump.return_value = {
            "messages": messages,
            "search_criteria": {},
            "user_location": {}
        }

        # Call the tool
        result = await update_search_state.coroutine(mock_state)
        print(result)

        # Verify Command output
        assert result.update is not None
        assert result.update["search_criteria"] == mock_criteria
        assert len(result.update["messages"]) == 1
        assert isinstance(result.update["messages"][0], ToolMessage)
        assert result.update["messages"][0].tool_call_id == "call_123"

@pytest.mark.asyncio
async def test_update_search_state_sequential():
    """Test updating state sequentially: first muscle, then adding cardio."""
    with patch("react_agent.tools.update_search_state.extract_user_criteria_graph") as mock_graph:
        # ------------------------------------------------------------------
        # TURN 1: "I want to build muscle"
        # ------------------------------------------------------------------
        
        # Mock subgraph response for turn 1
        mock_extracted_1 = MagicMock()
        mock_extracted_1.model_dump_json.return_value = '{"training_goal": "build muscle"}'
        
        # Mock subgraph response for turn 2
        mock_extracted_2 = MagicMock()
        mock_extracted_2.model_dump_json.return_value = '{"training_goal": "build muscle, cardio"}'

        # Define side effects for subgraph calls
        mock_graph.ainvoke.side_effect = [
            {
                "search_criteria": SearchCriteria(goal="build muscle"),
                "extracted_criteria": mock_extracted_1
            },
            {
                "search_criteria": SearchCriteria(goal="build muscle, cardio"),
                "extracted_criteria": mock_extracted_2
            }
        ]

        # Initial State
        state_1 = MagicMock(spec=State)
        state_1.messages = [
            AIMessage(
                content="I want to build muscle",
                tool_calls=[{"id": "call_1", "name": "update_search_state", "args": {}}]
            )
        ]
        state_1.model_dump.return_value = {
            "messages": state_1.messages,
            "search_criteria": {}, # Empty initially
            "user_location": {}
        }

        # Call Tool 1
        result_1 = await update_search_state.coroutine(state_1)
        
        # Verify result 1
        assert result_1.update["search_criteria"].goal == "build muscle"
        
        # ------------------------------------------------------------------
        # TURN 2: "Actually I also want to train cardio"
        # ------------------------------------------------------------------
        
        # Update state with result from Turn 1
        current_criteria_model = result_1.update["search_criteria"]
        # Convert model to dict for state simulation if state.model_dump() returns dicts for nested models
        # (Though SearchCriteria inside the dict is fine if consistent)
        
        state_2 = MagicMock(spec=State)
        state_2.messages = [
            AIMessage(
                content="Actually I also want to train cardio",
                tool_calls=[{"id": "call_2", "name": "update_search_state", "args": {}}]
            )
        ]
        # Simulate that the state now holds the criteria from previous step
        state_2.model_dump.return_value = {
            "messages": state_2.messages,
            "search_criteria": current_criteria_model.model_dump(),
            "user_location": {}
        }

        # Call Tool 2
        result_2 = await update_search_state.coroutine(state_2)

        # Verify interaction with subgraph
        # We want to check that ainvoke was called with the correct current_criteria
        # Call 0 was for turn 1, Call 1 was for turn 2
        args, _ = mock_graph.ainvoke.call_args_list[1] 
        subgraph_input = args[0]
        
        # Assert the input to subgraph contained the previous goal
        assert subgraph_input["search_criteria"]["goal"] == "build muscle"
        assert subgraph_input["user_query"] == "Actually I also want to train cardio"
        
        # Verify final result
        assert result_2.update["search_criteria"].goal == "build muscle, cardio"
        print(result_2)

@pytest.mark.asyncio
async def test_update_search_state_no_tool_call():
    mock_state = MagicMock(spec=State)
    mock_state.messages = [AIMessage(content="Just talking")]
    
    result = await update_search_state.coroutine(mock_state)
    print(result)
    assert result == "Error: No active tool call found to respond to."
