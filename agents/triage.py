"""Agent 2: Triage Scorer — assigns priority to classified requests."""

from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from ._base import get_llm


class TriageOutput(BaseModel):
    priority: int = Field(
        description="Priority level from 1 (lowest) to 5 (highest)",
        ge=1,
        le=5,
    )
    rationale: str = Field(
        description="Brief explanation of why this priority was assigned"
    )


_parser = PydanticOutputParser(pydantic_object=TriageOutput)

_SYSTEM = """\
You are a triage scoring agent for a customer support system.

Given a customer request and its classification, assign a priority from 1 to 5:
- 5: Critical — immediate action required (data loss, outage, security breach)
- 4: High — significant business impact, respond within 1 hour
- 3: Medium — moderate impact, respond within 4 hours
- 2: Low — minor issue, respond within 24 hours
- 1: Minimal — informational, respond within 72 hours

Classification provided: {classification} (confidence: {confidence})

{format_instructions}
"""

_prompt = ChatPromptTemplate.from_messages(
    [("system", _SYSTEM), ("human", "{input}")]
).partial(format_instructions=_parser.get_format_instructions())


def run_triage(
    input_text: str,
    classification: str,
    confidence: float,
) -> tuple[TriageOutput, int, int]:
    """
    Score triage priority for a classified request.

    Returns:
        (TriageOutput, input_tokens, output_tokens)
    """
    llm = get_llm()
    messages = _prompt.format_messages(
        input=input_text,
        classification=classification,
        confidence=confidence,
    )
    ai_msg = llm.invoke(messages)

    usage = ai_msg.usage_metadata or {}
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)

    result = _parser.parse(ai_msg.content)
    return result, input_tokens, output_tokens
