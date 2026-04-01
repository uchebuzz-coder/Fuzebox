"""Agent 3: Response Drafter — drafts a customer-facing response."""

from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from ._base import get_llm


class ResponderOutput(BaseModel):
    response: str = Field(
        description="The full customer-facing response text"
    )
    sentiment: str = Field(
        description="Tone used: positive, neutral, or empathetic"
    )


_parser = PydanticOutputParser(pydantic_object=ResponderOutput)

_SYSTEM = """\
You are a response drafting agent for a customer support system.

Draft a professional, helpful response to the customer request below.
Context:
  - Classification: {classification}
  - Priority: {priority}/5
  - Priority rationale: {rationale}

Guidelines:
- If priority >= 4, use an empathetic tone and acknowledge urgency.
- If classification is "billing", be precise and reassuring.
- If classification is "technical", be clear and step-by-step.
- Otherwise, use a positive, friendly tone.
- Keep the response concise but complete (2–4 sentences).

{format_instructions}
"""

_prompt = ChatPromptTemplate.from_messages(
    [("system", _SYSTEM), ("human", "{input}")]
).partial(format_instructions=_parser.get_format_instructions())


def run_responder(
    input_text: str,
    classification: str,
    priority: int,
    rationale: str,
) -> tuple[ResponderOutput, int, int]:
    """
    Draft a response for a triaged request.

    Returns:
        (ResponderOutput, input_tokens, output_tokens)
    """
    llm = get_llm()
    messages = _prompt.format_messages(
        input=input_text,
        classification=classification,
        priority=priority,
        rationale=rationale,
    )
    ai_msg = llm.invoke(messages)

    usage = ai_msg.usage_metadata or {}
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)

    result = _parser.parse(ai_msg.content)
    return result, input_tokens, output_tokens
