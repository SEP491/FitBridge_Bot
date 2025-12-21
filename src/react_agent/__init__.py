"""React Agent.

This module defines a custom reasoning and action agent graph.
It invokes tools in a simple loop.
"""

# Force environment loading before anything else
from react_agent.infrastructure import load_env
load_env()

from react_agent.graph import graph

__all__ = ["graph"]
