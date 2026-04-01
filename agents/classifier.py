"""Agent 1: Intake Classifier — classifies incoming service requests."""

from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from ._base import get_llm


class ClassificationOutput(BaseModel):
    classification: str = Field(
        description=(
            "Exactly one of: billing, technical, account, general, urgent"
        )
    )
    confidence: float = Field(
        description="Confidence score between 0.0 and 1.0",
        ge=0.0,
        le=1.0,
    )


_parser = PydanticOutputParser(pydantic_object=ClassificationOutput)

_SYSTEM = """\
You are an intake classifier for a customer support system.

Classify the customer request into exactly one category:
- billing:   payment issues, invoices, charges, refunds, subscriptions
- technical: bugs, errors, performance problems, API or integration issues
- account:   login, password reset, profile settings, access permissions
- general:   general inquiries, how-to questions, feature requests, feedback
- urgent:    critical business impact, data loss, security incidents, outages

{format_instructions}
"""

_prompt = ChatPromptTemplate.from_messages(
    [("system", _SYSTEM), ("human", "{input}")]
).partial(format_instructions=_parser.get_format_instructions())


def run_classifier(input_text: str) -> tuple[ClassificationOutput, int, int]:
    """
    Classify a service request.

    Returns:
        (ClassificationOutput, input_tokens, output_tokens)
    """
    llm = get_llm()
    messages = _prompt.format_messages(input=input_text)
    ai_msg = llm.invoke(messages)

    usage = ai_msg.usage_metadata or {}
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)

    result = _parser.parse(ai_msg.content)
    return result, input_tokens, output_tokens
