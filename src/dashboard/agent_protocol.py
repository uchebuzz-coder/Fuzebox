"""Agent abstraction layer: AgentProtocol, AgentRegistry, and YAML config loader.

Adding a new agent type:
1. Drop a new YAML file in the ``agents/`` directory (see agents/claude_opus.yaml
   for the expected schema).
2. Add ``class_name: YourClass`` to the YAML.
3. Map the class name to its Python class in ``_AGENT_CLASSES`` below.
4. Call ``init_registry()`` at application startup — your agent is registered
   automatically with no further code changes needed.
"""

from __future__ import annotations

import yaml
from pathlib import Path
from typing import Protocol, runtime_checkable

from .config import settings
from .models import Agent, AgentStatus, TaskType

# ---------------------------------------------------------------------------
# Map YAML class_name -> Python class. Extend this when adding new agent types.
# Imports are deferred to avoid circular imports at module load time.
# ---------------------------------------------------------------------------
def _get_agent_classes() -> dict:
    from src.real_agent import ClaudeAgent  # noqa: PLC0415
    return {"ClaudeAgent": ClaudeAgent}


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class AgentProtocol(Protocol):
    """Structural protocol all pluggable agents must satisfy.

    Existing agent classes satisfy this automatically (structural subtyping)
    without inheriting from it.
    """

    agent_id: str

    def run_task(self, task_type: "TaskType | str", payload: dict) -> str:
        """Execute a task and return the text result."""
        ...


# ---------------------------------------------------------------------------
# YAML config helpers
# ---------------------------------------------------------------------------

def load_agent_config(name: str) -> dict:
    """Load a single agent config from ``<agents_config_dir>/<name>.yaml``.

    Args:
        name: The YAML filename without the .yaml extension.

    Raises:
        FileNotFoundError: If the config file does not exist.
    """
    config_path = settings.agents_config_dir / f"{name}.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Agent config not found: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def list_agent_configs() -> list[dict]:
    """Load and return all agent YAML configs from ``agents_config_dir``."""
    configs: list[dict] = []
    agents_dir = settings.agents_config_dir
    if not agents_dir.exists():
        return configs
    for yaml_file in sorted(agents_dir.glob("*.yaml")):
        with open(yaml_file, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
            if cfg:
                configs.append(cfg)
    return configs


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class AgentRegistry:
    """Maps task types to capable agent instances.

    Usage::

        registry = get_registry()
        agent = registry.resolve("code_generation")
        result = agent.run_task("code_generation", {"prompt": "..."})
    """

    def __init__(self) -> None:
        # task_type -> ordered list of agent_ids (first = preferred)
        self._routing: dict[str, list[str]] = {}
        # agent_id -> instance
        self._agents: dict[str, AgentProtocol] = {}

    def register(self, agent: AgentProtocol, task_types: list[str]) -> None:
        """Register *agent* as a handler for each task type in *task_types*."""
        self._agents[agent.agent_id] = agent
        for tt in task_types:
            self._routing.setdefault(tt, [])
            if agent.agent_id not in self._routing[tt]:
                self._routing[tt].append(agent.agent_id)

    def agents_for(self, task_type: str) -> list[str]:
        """Return all agent_ids that can handle *task_type*."""
        return list(self._routing.get(task_type, []))

    def resolve(self, task_type: str) -> AgentProtocol | None:
        """Return the preferred agent for *task_type*, or ``None`` if none registered."""
        agent_ids = self.agents_for(task_type)
        if not agent_ids:
            return None
        return self._agents.get(agent_ids[0])

    def get(self, agent_id: str) -> AgentProtocol | None:
        """Return agent instance by ID."""
        return self._agents.get(agent_id)

    def all_agents(self) -> list[AgentProtocol]:
        """Return all registered agent instances."""
        return list(self._agents.values())

    def routing_table(self) -> dict[str, list[str]]:
        """Return the full ``{task_type: [agent_id, ...]}`` mapping."""
        return {k: list(v) for k, v in self._routing.items()}

    def is_empty(self) -> bool:
        return len(self._agents) == 0


# Module-level singleton
_registry = AgentRegistry()


def get_registry() -> AgentRegistry:
    """Return the global AgentRegistry singleton."""
    return _registry


# ---------------------------------------------------------------------------
# Registry initialisation
# ---------------------------------------------------------------------------

def init_registry() -> AgentRegistry:
    """Load all agent YAML configs, instantiate agents, and populate the registry.

    Safe to call multiple times — uses ``INSERT OR REPLACE`` semantics in the DB
    and is idempotent in the registry itself.

    Returns:
        The populated global AgentRegistry singleton.
    """
    from src.dashboard.db import init_db, upsert_agent  # noqa: PLC0415
    from src.dashboard.tracing import init_tracing  # noqa: PLC0415

    init_db()
    init_tracing()

    agent_classes = _get_agent_classes()

    for config in list_agent_configs():
        class_name = config.get("class_name", "ClaudeAgent")
        agent_class = agent_classes.get(class_name)
        if agent_class is None:
            print(f"[AgentRegistry] Unknown class_name '{class_name}' in config — skipping.")
            continue

        agent_instance = agent_class(config=config)

        # Persist registration in the dashboard DB
        upsert_agent(Agent(
            agent_id=config["agent_id"],
            name=config["name"],
            description=config.get("description", ""),
            skills=config.get("skills", []),
            permissions=config.get("permissions", []),
            group=config.get("group", "production"),
            status=AgentStatus.ACTIVE,
            cost_per_1k_input=config.get("cost_per_1k_input", 0.003),
            cost_per_1k_output=config.get("cost_per_1k_output", 0.015),
            model_name=config.get("model", "unknown"),
        ))

        _registry.register(agent_instance, config.get("task_types", []))

    return _registry
