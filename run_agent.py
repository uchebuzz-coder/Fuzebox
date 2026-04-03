"""
CLI for running real Claude agent tasks and viewing results in the dashboard.

Agents are loaded automatically from YAML files in the ``agents/`` directory.
The AgentRegistry routes each task type to the appropriate agent — no hardcoding
required when new agents are added.

Usage:
    python run_agent.py generate "Write a Python class for a binary search tree"
    python run_agent.py review src/dashboard/db.py
    python run_agent.py debug src/dashboard/db.py "AttributeError: 'NoneType' has no attribute 'execute'"
    python run_agent.py research "Python async/await patterns and best practices"
    python run_agent.py tests src/dashboard/models.py
    python run_agent.py demo

Then open the dashboard to see real metrics:
    streamlit run dashboard_app.py
"""

import argparse
import os
import sys
import textwrap

from src.dashboard.agent_protocol import init_registry, get_registry
from src.real_agent import ClaudeAgent


def check_api_key():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable is not set.")
        print()
        print("Get your key at https://console.anthropic.com/")
        print("Then run:  export ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)


def print_result(label: str, result: str, max_chars: int = 2000):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    if len(result) > max_chars:
        print(result[:max_chars])
        print(f"\n... [{len(result) - max_chars} more characters]")
    else:
        print(result)
    print()


def _resolve(task_type: str) -> ClaudeAgent:
    """Return the registered agent for *task_type*, or exit with an error."""
    agent = get_registry().resolve(task_type)
    if agent is None:
        print(f"ERROR: No agent registered for task_type '{task_type}'.")
        print("Check that at least one YAML file in agents/ lists this task type.")
        sys.exit(1)
    return agent


def run_demo():
    """Run a multi-task demo showing all agent capabilities."""
    print("\nRunning real Claude agent demo — all tasks will appear in the dashboard.\n")

    sample_code = textwrap.dedent("""\
        def find_duplicates(numbers):
            seen = []
            duplicates = []
            for n in numbers:
                if n in seen:
                    duplicates.append(n)
                seen.append(n)
            return duplicates
    """)

    buggy_code = textwrap.dedent("""\
        def divide(a, b):
            return a / b

        result = divide(10, 0)
        print(result)
    """)

    tasks = [
        ("1/5  Code Generation", "code_generation", lambda a: a.generate_code(
            "Write a Python function that finds the longest common subsequence "
            "of two strings. Include a clear docstring and type hints."
        )),
        ("2/5  Code Review",     "code_review",     lambda a: a.review_code(sample_code)),
        ("3/5  Bug Fix",         "bug_fix",          lambda a: a.debug(
            buggy_code,
            "ZeroDivisionError: division by zero\n  File 'main.py', line 4"
        )),
        ("4/5  Research",        "research",         lambda a: a.research(
            "Python asyncio: event loop, coroutines, tasks, and common patterns"
        )),
        ("5/5  Test Generation", "test_generation",  lambda a: a.generate_tests(sample_code)),
    ]

    for label, task_type, fn in tasks:
        agent = _resolve(task_type)
        print(f"Running: {label} [{agent.agent_id}] ...", end="", flush=True)
        try:
            result = fn(agent)
            print(" done")
            print_result(label, result, max_chars=600)
        except Exception as e:
            print(f" ERROR: {e}")

    print("Demo complete!")
    print("Open the dashboard to view real metrics:")
    print("  streamlit run dashboard_app.py")


def main():
    check_api_key()

    # Discover and register all agents from agents/*.yaml
    registry = init_registry()
    if registry.is_empty():
        print("WARNING: No agents were loaded. Check that agents/*.yaml files exist.")

    parser = argparse.ArgumentParser(
        description="Run real Claude agent tasks tracked in the Fuzebox dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    p = sub.add_parser("generate", help="Generate code from a description")
    p.add_argument("prompt", help="Natural language description of code to generate")

    p = sub.add_parser("review", help="Review code for quality and issues")
    p.add_argument("file", help="Path to file to review")
    p.add_argument("--lang", default="python", help="Programming language (default: python)")

    p = sub.add_parser("debug", help="Debug code given an error message")
    p.add_argument("file", help="Path to file with the bug")
    p.add_argument("error", help="Error message or traceback")
    p.add_argument("--lang", default="python", help="Programming language (default: python)")

    p = sub.add_parser("research", help="Research a topic")
    p.add_argument("topic", help="Topic to research and summarize")

    p = sub.add_parser("tests", help="Generate unit tests for a file")
    p.add_argument("file", help="Path to file to generate tests for")
    p.add_argument("--lang", default="python", help="Programming language (default: python)")

    sub.add_parser("demo", help="Run a multi-task demo (all 5 task types)")

    args = parser.parse_args()

    if args.command == "generate":
        agent = _resolve("code_generation")
        result = agent.generate_code(args.prompt)
        print_result("Generated Code", result)

    elif args.command == "review":
        agent = _resolve("code_review")
        code = open(args.file).read()
        result = agent.review_code(code, language=args.lang)
        print_result(f"Code Review: {args.file}", result)

    elif args.command == "debug":
        agent = _resolve("bug_fix")
        code = open(args.file).read()
        result = agent.debug(code, args.error, language=args.lang)
        print_result(f"Bug Fix: {args.file}", result)

    elif args.command == "research":
        agent = _resolve("research")
        result = agent.research(args.topic)
        print_result(f"Research: {args.topic}", result)

    elif args.command == "tests":
        agent = _resolve("test_generation")
        code = open(args.file).read()
        result = agent.generate_tests(code, language=args.lang)
        print_result(f"Generated Tests: {args.file}", result)

    elif args.command == "demo":
        run_demo()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
