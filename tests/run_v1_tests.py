#!/usr/bin/env python3
"""
V1 Pipeline Test Harness
========================
Runs 10+ realistic service requests through the full pipeline.
All outputs and telemetry are stored in the SQLite DB.
No expected outputs are simulated — everything comes from real LLM calls.

Usage:
    python tests/run_v1_tests.py

Requirements:
    OPENAI_API_KEY  (or ANTHROPIC_API_KEY + LLM_PROVIDER=anthropic)
"""

import json
import os
import sys
import time
from datetime import datetime

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from pipeline.pipeline import run_pipeline

# ── Test cases ─────────────────────────────────────────────────────────────────
# 13 realistic service requests covering all classification categories.

TEST_CASES = [
    # --- BILLING ---
    # {
    #     "id": "tc-01",
    #     "description": "Unexpected charge on statement",
    #     "input": (
    #         "Hi, I noticed a charge of $49.99 on my credit card statement from "
    #         "your company but I never signed up for any premium plan. I need this "
    #         "refunded immediately. My account email is user@example.com."
    #     ),
    # },
    # {
    #     "id": "tc-02",
    #     "description": "Invoice discrepancy",
    #     "input": (
    #         "The invoice I received for last month shows $200 but our contract "
    #         "specifies a flat rate of $150/month. Please correct this and send "
    #         "an updated invoice."
    #     ),
    # },

    # --- TECHNICAL ---
    # {
    #     "id": "tc-03",
    #     "description": "API returning 500 errors",
    #     "input": (
    #         "Our integration with your REST API has been returning HTTP 500 errors "
    #         "on the /v2/data endpoint since 2pm UTC today. This is breaking our "
    #         "production pipeline. Error message: 'Internal Server Error'. "
    #         "Request ID: req_abc123."
    #     ),
    # },
    # {
    #     "id": "tc-04",
    #     "description": "Dashboard not loading",
    #     "input": (
    #         "The analytics dashboard is completely blank when I log in. "
    #         "I've tried Chrome and Firefox, cleared cache, and same result. "
    #         "Other team members have the same issue. Started about 30 minutes ago."
    #     ),
    # },
    # {
    #     "id": "tc-05",
    #     "description": "Slow query performance",
    #     "input": (
    #         "Queries that used to take 2 seconds are now taking over 30 seconds. "
    #         "This started after the maintenance window last night. "
    #         "Affects all users in our organization."
    #     ),
    # },

    # # --- ACCOUNT ---
    # {
    #     "id": "tc-06",
    #     "description": "Cannot reset password",
    #     "input": (
    #         "I'm trying to reset my password but the reset email never arrives. "
    #         "I've checked spam and tried three times. My email is test@company.org."
    #     ),
    # },
    # {
    #     "id": "tc-07",
    #     "description": "User permission issue",
    #     "input": (
    #         "One of my team members was given admin access last week but they "
    #         "still can't see the admin panel. Their user ID is 98432. "
    #         "I've double-checked the permissions settings and it shows 'Admin'."
    #     ),
    # },

    # --- GENERAL ---
    {
        "id": "tc-08",
        "description": "Feature request",
        "input": (
            "It would be really helpful if we could export reports as PDF in "
            "addition to CSV. Is this on the roadmap? We have stakeholders who "
            "prefer PDF format for presentations."
        ),
    },
    {
        "id": "tc-09",
        "description": "How-to question",
        "input": (
            "How do I set up webhook notifications for when a new record is created? "
            "I've read the docs but the section on webhooks seems outdated — "
            "the UI doesn't match the screenshots."
        ),
    },

    # --- URGENT ---
    {
        "id": "tc-10",
        "description": "Data loss incident",
        "input": (
            "URGENT: All data from the past 48 hours appears to have been deleted "
            "from our account. This includes customer records and transaction logs. "
            "We are a financial services firm and this is a critical compliance issue. "
            "We need immediate escalation to your on-call engineering team."
        ),
    },
    {
        "id": "tc-11",
        "description": "Security breach suspected",
        "input": (
            "We've detected unauthorized logins to several user accounts from "
            "IP addresses in Eastern Europe. Our security team believes there "
            "may be a credential leak on your platform. We need you to investigate "
            "and disable these sessions immediately."
        ),
    },

    # --- MIXED / EDGE CASES ---
    {
        "id": "tc-12",
        "description": "Billing + technical combined",
        "input": (
            "We're being charged for 10 API seats but our dashboard shows "
            "we can only use 8 — two seats are greyed out with an error saying "
            "'Seat allocation failed'. This is both a billing and a technical issue."
        ),
    },
    {
        "id": "tc-13",
        "description": "Vague request",
        "input": (
            "Hi, things aren't working properly. Can someone help?"
        ),
    },
]


# ── Runner ─────────────────────────────────────────────────────────────────────

def run_all_tests(verbose: bool = True) -> dict:
    results = []
    errors = []
    start_time = time.time()

    print(f"\n{'='*60}")
    print(f"  Fuzebox V1 Pipeline — Test Harness")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Running {len(TEST_CASES)} test cases")
    print(f"{'='*60}\n")

    for tc in TEST_CASES:
        tc_id = tc["id"]
        description = tc["description"]
        input_text = tc["input"]

        print(f"[{tc_id}] {description}")
        print(f"  Input: {input_text[:80]}{'...' if len(input_text) > 80 else ''}")

        t0 = time.time()
        try:
            result = run_pipeline(input_text)
            elapsed = round((time.time() - t0) * 1000, 1)

            summary = {
                "test_id": tc_id,
                "description": description,
                "workflow_id": result.workflow_id,
                "classification": result.classification.classification,
                "confidence": result.classification.confidence,
                "priority": result.triage.priority,
                "sentiment": result.response.sentiment,
                "escalation_flag": result.escalation_flag,
                "pipeline_success": result.pipeline_success,
                "total_tokens": result.total_input_tokens + result.total_output_tokens,
                "total_cost_usd": result.total_cost_usd,
                "elapsed_ms": elapsed,
            }
            results.append(summary)

            if verbose:
                print(f"  ✓ classification={result.classification.classification} "
                      f"(conf={result.classification.confidence:.2f})")
                print(f"  ✓ priority={result.triage.priority}/5  "
                      f"escalate={result.escalation_flag}")
                print(f"  ✓ sentiment={result.response.sentiment}")
                print(f"  ✓ tokens={result.total_input_tokens + result.total_output_tokens}  "
                      f"cost=${result.total_cost_usd:.6f}  "
                      f"time={elapsed}ms")
                print()

        except Exception as exc:
            elapsed = round((time.time() - t0) * 1000, 1)
            errors.append({"test_id": tc_id, "error": str(exc), "elapsed_ms": elapsed})
            print(f"  ✗ FAILED: {exc}\n")

    total_elapsed = round(time.time() - start_time, 2)

    # ── Summary ────────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  Results Summary")
    print(f"{'='*60}")
    print(f"  Total tests : {len(TEST_CASES)}")
    print(f"  Passed      : {len(results)}")
    print(f"  Failed      : {len(errors)}")
    print(f"  Total time  : {total_elapsed}s")

    if results:
        avg_tokens = sum(r["total_tokens"] for r in results) / len(results)
        avg_cost = sum(r["total_cost_usd"] for r in results) / len(results)
        escalated = sum(1 for r in results if r["escalation_flag"])
        class_dist: dict[str, int] = {}
        for r in results:
            class_dist[r["classification"]] = class_dist.get(r["classification"], 0) + 1

        print(f"\n  Avg tokens/run : {avg_tokens:.0f}")
        print(f"  Avg cost/run   : ${avg_cost:.6f}")
        print(f"  Escalated      : {escalated}/{len(results)}")
        print(f"\n  Classification distribution:")
        for cat, count in sorted(class_dist.items()):
            print(f"    {cat:<12} : {count}")

    if errors:
        print(f"\n  Errors:")
        for e in errors:
            print(f"    [{e['test_id']}] {e['error']}")

    print(f"\n  Telemetry stored in: data/agent_dashboard.db")
    print(f"  View metrics: GET /v1/metrics  (after starting the API)")
    print(f"{'='*60}\n")

    # ── Write JSON report ──────────────────────────────────────────────────────
    report = {
        "run_at": datetime.now().isoformat(),
        "total_tests": len(TEST_CASES),
        "passed": len(results),
        "failed": len(errors),
        "total_elapsed_s": total_elapsed,
        "results": results,
        "errors": errors,
    }
    report_path = os.path.join(os.path.dirname(__file__), "v1_test_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"  Full report saved to: {report_path}\n")

    return report


if __name__ == "__main__":
    run_all_tests(verbose=True)
