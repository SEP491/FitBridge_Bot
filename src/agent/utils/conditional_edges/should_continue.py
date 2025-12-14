from agent.utils.state.MessageState import OverallState

def should_continue(state: OverallState):
    if state.error_code != 200:
        print(f"Error: {state.error}")
        return False
    if state.messages and state.messages[-1].tool_calls:
        return "tool_node"
    return True