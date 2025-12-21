"""Define the configurable parameters for the agent."""

from __future__ import annotations

import os
from pydantic import BaseModel, Field
from typing import Annotated

from . import prompts


class Context(BaseModel):
    """The context for the agent."""

    system_prompt: str = Field(
        default=prompts.SYSTEM_PROMPT,
        description="The system prompt to use for the agent's interactions. "
        "This prompt sets the context and behavior for the agent."
    )

    model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = Field(
        default="openai/gpt-4o-mini",
        description="The name of the language model to use for the agent's main interactions. "
        "Should be in the form: provider/model-name."
    )

    max_search_results: int = Field(
        default=10,
        description="The maximum number of search results to return for each search query."
    )

    def model_post_init(self, __context) -> None:
        """Fetch env vars for attributes that were not passed as args."""
        for field_name, field_info in self.model_fields.items():
            if getattr(self, field_name) == field_info.default:
                env_val = os.environ.get(field_name.upper())
                if env_val is not None:
                    setattr(self, field_name, env_val)
