"""FastAPI server for the ReAct Agent with in-memory checkpointing.

This module provides a streaming endpoint for interacting with the LangGraph agent,
using MemorySaver for in-memory checkpoints across conversations.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage

from react_agent.graph import builder
from react_agent.state import InputState
from react_agent.context import Context
from react_agent.domain.entities import UserOrigin

logger = logging.getLogger(__name__)

# Global reference to the compiled graph with checkpointer
_graph = None


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""

    message: str = Field(..., description="The user's message")
    search_criteria: dict = Field(default_factory=dict, description="Optional search criteria")
    user_origin: dict = Field(default_factory=dict, description="Optional user location")


class ChatResponse(BaseModel):
    """Response body for non-streaming chat endpoint."""

    messages: list[dict] = Field(..., description="List of response messages")
    final_report: str = Field(default="", description="Final synthesized report if available")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[dict, None]:
    """Manage application lifecycle - setup MemorySaver.

    This context manager:
    1. Initializes MemorySaver for in-memory checkpointing
    2. Compiles the graph with the checkpointer
    3. Cleans up on shutdown
    """
    global _graph

    logger.info("Initializing in-memory checkpointer...")

    checkpointer = MemorySaver()

    # Compile the graph with the checkpointer
    logger.info("Compiling graph with in-memory checkpointer...")
    _graph = builder.compile(
        checkpointer=checkpointer,
        name="ReAct Agent",
    )

    logger.info("Server ready. Graph compiled with in-memory checkpointer.")

    yield {"checkpointer": checkpointer, "graph": _graph}

    logger.info("Shutting down server...")


app = FastAPI(
    title="FitBridge ReAct Agent API",
    description="Streaming API for the FitBridge recommendation agent with persistent checkpointing",
    version="1.0.0",
    lifespan=lifespan,
)


async def stream_graph_events(
    thread_id: str,
    graph_input: dict,
    context: Context,
) -> AsyncGenerator[str, None]:
    """Stream graph events as Server-Sent Events (SSE).

    Args:
        thread_id: Unique identifier for the conversation thread
        graph_input: The input dict (either full state for new thread, or just messages for existing)
        context: The agent context configuration

    Yields:
        SSE-formatted strings containing event data
    """
    global _graph

    if _graph is None:
        yield f"event: error\ndata: Graph not initialized\n\n"
        return

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    try:
        # Stream events from the graph
        async for event in _graph.astream_events(
            graph_input,
            config=config,
            context=context,
            version="v2",
        ):
            event_type = event.get("event")
            
            # Stream different event types
            if event_type == "on_chat_model_stream":
                # Token-level streaming from LLM
                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content is not None:
                    yield f"event: token\ndata: {chunk.content}\n\n"

            elif event_type == "on_chain_end":
                # Node completion
                node_name = event.get("name", "unknown")
                if node_name not in ["RunnableSequence", "ChannelWrite"]:
                    yield f"event: node_end\ndata: {node_name}\n\n"

            elif event_type == "on_tool_start":
                # Tool invocation start
                tool_name = event.get("name", "unknown")
                yield f"event: tool_start\ndata: {tool_name}\n\n"

            elif event_type == "on_tool_end":
                # Tool invocation end
                tool_name = event.get("name", "unknown")
                output = event.get("data", {}).get("output", "")
                # Truncate long outputs for SSE
                if len(str(output)) > 500:
                    output = str(output)[:500] + "..."
                yield f"event: tool_end\ndata: {tool_name}\n\n"

        # Signal completion
        yield f"event: done\ndata: stream_complete\n\n"

    except Exception as e:
        logger.exception(f"Error streaming graph events: {e}")
        yield f"event: error\ndata: {str(e)}\n\n"


@app.get("/stream")
async def stream_chat(
    thread_id: str = Query(..., description="Unique notoij thread ID for conversation persistence"),
    message: str = Query(..., description="The user's message"),
    latitude: Optional[float] = Query(None, description="Optional latitude of the user's location"),
    longitude: Optional[float] = Query(None, description="Optional longitude of the user's location"),
) -> StreamingResponse:
    """Stream a chat response from the agent.
    eat shit nigga

    This endpoint:
    1. Accepts a thread_id and message via query parameters
    2. Optionally accepts user origin (latitude/longitude)
    3. Retrieves existing state from checkpointer (if any)
    4. Appends new message to conversation history
    5. Streams the agent's response as Server-Sent Events (SSE)

    Events streamed:
    - `token`: Individual tokens from LLM response
    - `node_end`: When a graph node completes
    - `tool_start`: When a tool begins execution
    - `tool_end`: When a tool finishes execution
    - `done`: Stream completion signal
    - `error`: Error occurred during processing

    Args:
        thread_id: Client-provided unique identifier for the conversation
        message: The user's message to process
        user_origin: Optional user origin (latitude/longitude)

    Returns:
        StreamingResponse with SSE content type
    """
    global _graph

    if _graph is None:
        return StreamingResponse(
            iter(["event: error\ndata: Graph not initialized\n\n"]),
            media_type="text/event-stream",
        )

    config = {"configurable": {"thread_id": thread_id}}

    # Get existing state from checkpointer
    existing_state = await _graph.aget_state(config)

    if existing_state.values:
        # Thread exists - only pass the new message (add_messages reducer will append)
        graph_input = {"messages": [HumanMessage(content=message)]}
    else:
        # New thread - pass full initial state
        input_state = InputState(
            messages=[HumanMessage(content=message)],
        )
        # Set user_origin if latitude and longitude are provided
        if latitude is not None and longitude is not None:
            input_state.user_origin = UserOrigin(latitude=latitude, longitude=longitude)
        graph_input = input_state.model_dump()

    # Use default context
    context = Context()

    return StreamingResponse(
        stream_graph_events(thread_id, graph_input, context),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@app.post("/invoke")
async def invoke_chat(
    thread_id: str = Query(..., description="Unique thread ID for conversation persistence"),
    request: ChatRequest = ...,
) -> ChatResponse:
    """Invoke the agent and return the complete response (non-streaming).

    This endpoint is useful for clients that don't support SSE streaming.
    The full response is returned after the agent completes processing.

    Args:
        thread_id: Client-provided unique identifier for the conversation
        request: The chat request containing the message and optional context

    Returns:
        ChatResponse with the agent's messages and final report
    """
    global _graph

    if _graph is None:
        raise HTTPException(status_code=503, detail="Graph not initialized")

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    # Get existing state from checkpointer
    existing_state = await _graph.aget_state(config)

    if existing_state.values:
        # Thread exists - only pass the new message (add_messages reducer will append)
        graph_input = {"messages": [HumanMessage(content=request.message)]}
    else:
        # New thread - pass full initial state
        input_state = InputState(
            messages=[HumanMessage(content=request.message)],
        )
        # Override search_criteria and user_origin if provided
        if request.search_criteria:
            input_state.search_criteria = input_state.search_criteria.model_copy(
                update=request.search_criteria
            )
        if request.user_origin:
            input_state.user_origin = input_state.user_origin.model_copy(
                update=request.user_origin
            )
        graph_input = input_state.model_dump()

    context = Context()

    try:
        result = await _graph.ainvoke(
            graph_input,
            config=config,
            context=context,
        )

        # Extract messages from result
        messages = result.get("messages", [])
        serialized_messages = []
        for msg in messages:
            if hasattr(msg, "model_dump"):
                serialized_messages.append(msg.model_dump())
            elif hasattr(msg, "dict"):
                serialized_messages.append(msg.dict())
            else:
                serialized_messages.append({"content": str(msg)})

        return ChatResponse(
            messages=serialized_messages,
            final_report=result.get("final_report", ""),
        )

    except Exception as e:
        logger.exception(f"Error invoking graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))




@app.get("/threads/{thread_id}/state")
async def get_thread_state(
    thread_id: str,
) -> dict:
    """Get the current state of a conversation thread.

    Useful for debugging or resuming conversations.

    Args:
        thread_id: The thread ID to retrieve state for

    Returns:
        The current state snapshot for the thread
    """
    global _graph

    if _graph is None:
        raise HTTPException(status_code=503, detail="Graph not initialized")

    config = {"configurable": {"thread_id": thread_id}}

    try:
        state = await _graph.aget_state(config)
        if state.values:
            return {
                "thread_id": thread_id,
                "values": state.values,
                "next": state.next,
            }
        else:
            raise HTTPException(status_code=404, detail=f"No state found for thread: {thread_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting thread state: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    uvicorn.run(
        "react_agent.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )

