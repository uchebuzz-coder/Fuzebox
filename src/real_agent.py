"""
Real Claude-powered agent integrated with the Fuzebox Agent Performance Dashboard.

Uses the Anthropic SDK to make actual Claude API calls. Every task is automatically
tracked in the dashboard: token usage, latency, cost, and quality score.

Agent configuration (model, pricing, skills, system prompts) is loaded from a YAML
file in the ``agents/`` directory — no hardcoded constants. To swap models or tune
prompts, edit the YAML; no Python changes required.

Setup:
    export ANTHROPIC_API_KEY=your-api-key
    python run_agent.py demo
"""

import anthropic
from src.dashboard.tracing import trace_agent_task, init_tracing
from src.dashboard.db import upsert_agent, init_db
from src.dashboard.models import Agent, AgentStatus, TaskType
from src.dashboard.agent_protocol import load_agent_config

# ---------------------------------------------------------------------------
# Default config name — matches agents/claude_opus.yaml
# ---------------------------------------------------------------------------
_DEFAULT_CONFIG_NAME = "claude_opus"

# Quality scores per task type (subjective baseline; tune per deployment)
_DEFAULT_QUALITY: dict[str, float] = {
    "code_generation": 0.90,
    "code_review": 0.88,
    "bug_fix": 0.87,
    "research": 0.85,
    "test_generation": 0.88,
}


def register_agent(config_name: str = _DEFAULT_CONFIG_NAME):
    """Register this agent in the dashboard DB (safe to call multiple times).

    Args:
        config_name: YAML filename (without .yaml) under ``agents/``.
    """
    cfg = load_agent_config(config_name)
    init_db()
    init_tracing()
    upsert_agent(Agent(
        agent_id=cfg["agent_id"],
        name=cfg["name"],
        description=cfg.get("description", ""),
        skills=cfg.get("skills", []),
        permissions=cfg.get("permissions", []),
        group=cfg.get("group", "production"),
        status=AgentStatus.ACTIVE,
        cost_per_1k_input=cfg.get("cost_per_1k_input", 0.003),
        cost_per_1k_output=cfg.get("cost_per_1k_output", 0.015),
        model_name=cfg.get("model", "unknown"),
    ))


class ClaudeAgent:
    """
    A real Claude agent that automatically records every task to the Fuzebox
    dashboard (token usage, latency, cost, quality).

    Configuration is loaded from a YAML sidecar in ``agents/``:

        agent = ClaudeAgent()                          # uses claude_opus.yaml
        agent = ClaudeAgent(config_name="claude_sonnet")
        agent = ClaudeAgent(config=my_config_dict)     # inject directly

    Every public method maps to a dashboard ``task_type`` and is a thin wrapper
    around ``run_task()``.  The single ``run_task()`` method satisfies
    ``AgentProtocol`` — the registry uses it for generic dispatch.
    """

    def __init__(
        self,
        config_name: str = _DEFAULT_CONFIG_NAME,
        config: dict | None = None,
    ):
        if config is None:
            config = load_agent_config(config_name)
        self._cfg = config
        self.agent_id: str = config["agent_id"]
        self._model: str = config["model"]
        self._thinking: dict | None = config.get("thinking")
        self._system_prompts: dict[str, str] = config.get("system_prompts", {})
        self.client = anthropic.Anthropic()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _call(self, system: str, user: str, max_tokens: int = 4096) -> anthropic.types.Message:
        """Make a Claude API call and return the final message."""
        kwargs: dict = dict(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        if self._thinking:
            kwargs["thinking"] = self._thinking
        with self.client.messages.stream(**kwargs) as stream:
            return stream.get_final_message()

    @staticmethod
    def _text(response: anthropic.types.Message) -> str:
        return next((b.text for b in response.content if b.type == "text"), "")

    def _system(self, task_type: str) -> str:
        """Return the system prompt for *task_type*, raising if missing."""
        prompt = self._system_prompts.get(task_type)
        if prompt is None:
            raise ValueError(
                f"No system prompt configured for task_type '{task_type}'. "
                f"Add it to agents/{self._cfg.get('agent_id', '?')}.yaml."
            )
        return prompt

    # ------------------------------------------------------------------
    # AgentProtocol — generic dispatch entry point
    # ------------------------------------------------------------------

    def run_task(self, task_type: "TaskType | str", payload: dict) -> str:
        """Execute a task and return the text result.

        This method satisfies ``AgentProtocol`` and is used by the
        ``AgentRegistry`` for generic dispatch.

        Supported task types and their expected payload keys:

        * ``code_generation``  — ``prompt``
        * ``code_review``      — ``code``, optionally ``language``
        * ``bug_fix``          — ``code``, ``error``, optionally ``language``
        * ``research``         — ``topic``
        * ``test_generation``  — ``code``, optionally ``language``

        Args:
            task_type: A ``TaskType`` enum member or its string value.
            payload:   Dict of inputs for the task.

        Returns:
            The text response from Claude.
        """
        tt = task_type.value if isinstance(task_type, TaskType) else task_type
        dispatch = {
            "code_generation": lambda: self._generate_code(payload["prompt"]),
            "code_review":     lambda: self._review_code(
                payload["code"], payload.get("language", "python")
            ),
            "bug_fix":         lambda: self._debug(
                payload["code"], payload["error"], payload.get("language", "python")
            ),
            "research":        lambda: self._research(payload["topic"]),
            "test_generation": lambda: self._generate_tests(
                payload["code"], payload.get("language", "python")
            ),
        }
        handler = dispatch.get(tt)
        if handler is None:
            raise ValueError(f"Unsupported task_type: '{tt}'")
        return handler()

    # ------------------------------------------------------------------
    # Private task implementations
    # ------------------------------------------------------------------

    def _generate_code(self, prompt: str) -> str:
        with trace_agent_task(self.agent_id, "code_generation") as ctx:
            ctx.description = f"Generate code: {prompt[:100]}"
            ctx.required_skills = ["code_generation"]
            ctx.required_permissions = ["write_files"]
            response = self._call(system=self._system("code_generation"), user=prompt)
            ctx.set_tokens(input_tokens=response.usage.input_tokens,
                           output_tokens=response.usage.output_tokens)
            ctx.set_result("success")
            ctx.set_quality(_DEFAULT_QUALITY["code_generation"])
            ctx.add_metadata("model", self._model)
            return self._text(response)

    def _review_code(self, code: str, language: str = "python") -> str:
        with trace_agent_task(self.agent_id, "code_review") as ctx:
            ctx.description = f"Review {language} code ({len(code)} chars)"
            ctx.required_skills = ["code_review"]
            response = self._call(
                system=self._system("code_review"),
                user=f"Please review this {language} code:\n\n```{language}\n{code}\n```",
                max_tokens=3000,
            )
            ctx.set_tokens(input_tokens=response.usage.input_tokens,
                           output_tokens=response.usage.output_tokens)
            ctx.set_result("success")
            ctx.set_quality(_DEFAULT_QUALITY["code_review"])
            ctx.add_metadata("language", language)
            ctx.add_metadata("code_chars", len(code))
            return self._text(response)

    def _debug(self, code: str, error_message: str, language: str = "python") -> str:
        with trace_agent_task(self.agent_id, "bug_fix") as ctx:
            ctx.description = f"Debug: {error_message[:100]}"
            ctx.required_skills = ["debugging", "code_generation"]
            response = self._call(
                system=self._system("bug_fix"),
                user=(
                    f"This {language} code raises an error:\n\n"
                    f"```{language}\n{code}\n```\n\n"
                    f"Error:\n```\n{error_message}\n```"
                ),
                max_tokens=3000,
            )
            ctx.set_tokens(input_tokens=response.usage.input_tokens,
                           output_tokens=response.usage.output_tokens)
            ctx.set_result("success")
            ctx.set_quality(_DEFAULT_QUALITY["bug_fix"])
            ctx.add_metadata("language", language)
            return self._text(response)

    def _research(self, topic: str) -> str:
        with trace_agent_task(self.agent_id, "research") as ctx:
            ctx.description = f"Research: {topic[:100]}"
            ctx.required_skills = ["research", "summarization"]
            response = self._call(
                system=self._system("research"),
                user=f"Research and summarize the following topic for a software engineer:\n\n{topic}",
                max_tokens=4000,
            )
            ctx.set_tokens(input_tokens=response.usage.input_tokens,
                           output_tokens=response.usage.output_tokens)
            ctx.set_result("success")
            ctx.set_quality(_DEFAULT_QUALITY["research"])
            ctx.add_metadata("topic_length", len(topic))
            return self._text(response)

    def _generate_tests(self, code: str, language: str = "python") -> str:
        with trace_agent_task(self.agent_id, "test_generation") as ctx:
            ctx.description = f"Generate tests for {language} code"
            ctx.required_skills = ["code_generation", "code_review"]
            ctx.required_permissions = ["write_files", "run_tests"]
            response = self._call(
                system=self._system("test_generation"),
                user=f"Write unit tests for this {language} code:\n\n```{language}\n{code}\n```",
                max_tokens=4000,
            )
            ctx.set_tokens(input_tokens=response.usage.input_tokens,
                           output_tokens=response.usage.output_tokens)
            ctx.set_result("success")
            ctx.set_quality(_DEFAULT_QUALITY["test_generation"])
            ctx.add_metadata("language", language)
            return self._text(response)

    # ------------------------------------------------------------------
    # Public convenience aliases (backwards-compatible with run_agent.py)
    # ------------------------------------------------------------------

    def generate_code(self, prompt: str) -> str:
        """Generate code from a natural language description."""
        return self._generate_code(prompt)

    def review_code(self, code: str, language: str = "python") -> str:
        """Review code for quality, security, and performance issues."""
        return self._review_code(code, language)

    def debug(self, code: str, error_message: str, language: str = "python") -> str:
        """Diagnose a bug and suggest a fix."""
        return self._debug(code, error_message, language)

    def research(self, topic: str) -> str:
        """Research a topic and return a structured summary."""
        return self._research(topic)

    def generate_tests(self, code: str, language: str = "python") -> str:
        """Generate unit tests for a given code snippet."""
        return self._generate_tests(code, language)
