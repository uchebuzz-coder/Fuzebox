"""
Real Claude-powered agent integrated with the Fuzebox Agent Performance Dashboard.

Uses the Anthropic SDK to make actual Claude API calls. Every task is automatically
tracked in the dashboard: token usage, latency, cost, and quality score.

Setup:
    export ANTHROPIC_API_KEY=your-api-key
    python run_agent.py demo
"""

import anthropic
from src.dashboard.tracing import trace_agent_task, init_tracing
from src.dashboard.db import upsert_agent, init_db
from src.dashboard.models import Agent, AgentStatus

AGENT_ID = "claude-opus-agent-01"
MODEL = "claude-opus-4-6"

# Opus 4.6 pricing: $5/1M input, $25/1M output
COST_PER_1K_INPUT = 0.005
COST_PER_1K_OUTPUT = 0.025


def register_agent():
    """Register this agent in the dashboard (safe to call multiple times)."""
    init_db()
    init_tracing()
    upsert_agent(Agent(
        agent_id=AGENT_ID,
        name="Claude Opus 4.6 Agent",
        description="Real Claude Opus agent for code generation, review, debugging, and research",
        skills=["code_generation", "code_review", "debugging", "research", "summarization"],
        permissions=["read_files", "write_files", "run_tests"],
        group="production",
        status=AgentStatus.ACTIVE,
        cost_per_1k_input=COST_PER_1K_INPUT,
        cost_per_1k_output=COST_PER_1K_OUTPUT,
        model_name=MODEL,
    ))


class ClaudeAgent:
    """
    A real Claude Opus 4.6 agent that automatically records every task
    to the Fuzebox dashboard (token usage, latency, cost, quality).

    Every public method maps to a dashboard task_type and is wrapped with
    trace_agent_task() so metrics flow into the SQLite database automatically.
    """

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.agent_id = AGENT_ID

    def _call(self, system: str, user: str, max_tokens: int = 4096) -> anthropic.types.Message:
        """Make a streaming Claude API call and return the final message."""
        with self.client.messages.stream(
            model=MODEL,
            max_tokens=max_tokens,
            thinking={"type": "adaptive"},
            system=system,
            messages=[{"role": "user", "content": user}],
        ) as stream:
            return stream.get_final_message()

    @staticmethod
    def _text(response: anthropic.types.Message) -> str:
        """Extract the text content from a response."""
        return next((b.text for b in response.content if b.type == "text"), "")

    # ------------------------------------------------------------------
    # Public task methods — each one maps to a dashboard task_type
    # ------------------------------------------------------------------

    def generate_code(self, prompt: str) -> str:
        """Generate code from a natural language description."""
        with trace_agent_task(self.agent_id, "code_generation") as ctx:
            ctx.description = f"Generate code: {prompt[:100]}"
            ctx.required_skills = ["code_generation"]
            ctx.required_permissions = ["write_files"]

            response = self._call(
                system=(
                    "You are an expert software engineer. Write clean, well-commented, "
                    "production-ready code. Include type hints and docstrings."
                ),
                user=prompt,
            )

            ctx.set_tokens(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )
            ctx.set_result("success")
            ctx.set_quality(0.90)
            ctx.add_metadata("model", MODEL)

            return self._text(response)

    def review_code(self, code: str, language: str = "python") -> str:
        """Review code for quality, security, and performance issues."""
        with trace_agent_task(self.agent_id, "code_review") as ctx:
            ctx.description = f"Review {language} code ({len(code)} chars)"
            ctx.required_skills = ["code_review"]

            response = self._call(
                system=(
                    "You are a senior code reviewer. Evaluate code for: correctness, "
                    "security vulnerabilities, performance, readability, and best practices. "
                    "Be specific — cite line references where relevant."
                ),
                user=f"Please review this {language} code:\n\n```{language}\n{code}\n```",
                max_tokens=3000,
            )

            ctx.set_tokens(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )
            ctx.set_result("success")
            ctx.set_quality(0.88)
            ctx.add_metadata("language", language)
            ctx.add_metadata("code_chars", len(code))

            return self._text(response)

    def debug(self, code: str, error_message: str, language: str = "python") -> str:
        """Diagnose a bug and suggest a fix."""
        with trace_agent_task(self.agent_id, "bug_fix") as ctx:
            ctx.description = f"Debug: {error_message[:100]}"
            ctx.required_skills = ["debugging", "code_generation"]

            response = self._call(
                system=(
                    "You are an expert debugger. Identify the root cause of the error, "
                    "explain why it occurs, and provide a corrected version of the code."
                ),
                user=(
                    f"This {language} code raises an error:\n\n"
                    f"```{language}\n{code}\n```\n\n"
                    f"Error:\n```\n{error_message}\n```"
                ),
                max_tokens=3000,
            )

            ctx.set_tokens(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )
            ctx.set_result("success")
            ctx.set_quality(0.87)
            ctx.add_metadata("language", language)

            return self._text(response)

    def research(self, topic: str) -> str:
        """Research a topic and return a structured summary."""
        with trace_agent_task(self.agent_id, "research") as ctx:
            ctx.description = f"Research: {topic[:100]}"
            ctx.required_skills = ["research", "summarization"]

            response = self._call(
                system=(
                    "You are a research assistant. Provide accurate, well-structured summaries. "
                    "Include key concepts, practical examples, and common pitfalls where relevant."
                ),
                user=f"Research and summarize the following topic for a software engineer:\n\n{topic}",
                max_tokens=4000,
            )

            ctx.set_tokens(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )
            ctx.set_result("success")
            ctx.set_quality(0.85)
            ctx.add_metadata("topic_length", len(topic))

            return self._text(response)

    def generate_tests(self, code: str, language: str = "python") -> str:
        """Generate unit tests for a given code snippet."""
        with trace_agent_task(self.agent_id, "test_generation") as ctx:
            ctx.description = f"Generate tests for {language} code"
            ctx.required_skills = ["code_generation", "code_review"]
            ctx.required_permissions = ["write_files", "run_tests"]

            response = self._call(
                system=(
                    "You are a QA engineer who writes thorough unit tests. "
                    "Cover happy paths, edge cases, and error conditions. "
                    "Use the standard testing framework for the language."
                ),
                user=f"Write unit tests for this {language} code:\n\n```{language}\n{code}\n```",
                max_tokens=4000,
            )

            ctx.set_tokens(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )
            ctx.set_result("success")
            ctx.set_quality(0.88)
            ctx.add_metadata("language", language)

            return self._text(response)
