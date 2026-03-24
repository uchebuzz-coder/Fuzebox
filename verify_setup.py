#!/usr/bin/env python3
"""Verify that the Fuzebox Agent Performance Dashboard is set up correctly.

Run: python verify_setup.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def main():
    print("=" * 60)
    print("Fuzebox Agent Dashboard - Setup Verification")
    print("=" * 60)

    # Step 1: Check imports
    print("\n[1/5] Checking imports...")
    try:
        from src.dashboard import db, models, tracing, evaluators, economics, metrics
        print("  All modules imported successfully.")
    except ImportError as e:
        print(f"  FAILED: {e}")
        print("  Run: pip install -r requirements.txt")
        sys.exit(1)

    # Step 2: Initialize database
    print("\n[2/5] Initializing database...")
    db.init_db()
    print(f"  Database at: {db.DB_PATH}")

    # Step 3: Seed demo data
    print("\n[3/5] Seeding demo data...")
    result = db.seed_demo_data()
    print(f"  Agents:    {result['agents']}")
    print(f"  Tasks:     {result['tasks']}")
    print(f"  Spans:     {result['spans']}")
    print(f"  Workflows: {result['workflows']}")

    # Step 4: Verify queries
    print("\n[4/5] Verifying queries...")
    summary = metrics.performance_summary()
    print(f"  Total tasks:   {summary['total_tasks']}")
    print(f"  Success rate:  {summary['success_rate']:.1%}")
    print(f"  Total cost:    ${summary['total_cost']:.2f}")
    print(f"  Active agents: {summary['active_agents']}")
    print(f"  Avg latency:   {summary['avg_latency_ms']:.0f}ms")
    print(f"  Avg quality:   {summary['avg_quality']:.2f}")

    roi = economics.calculate_roi(50.0)
    print(f"  ROI vs $50 manual: {roi['roi_pct']:.0f}%")

    leaderboard = metrics.agent_leaderboard()
    if not leaderboard.empty:
        top = leaderboard.iloc[0]
        print(f"  Top agent: {top['Agent']} (score: {top['Score']:.3f})")

    scorecard = evaluators.get_agent_scorecard_df()
    passing = (scorecard["Status"] == "PASS").sum()
    print(f"  Scorecard: {passing}/{len(scorecard)} agents passing")

    # Step 5: Verify tracing API
    print("\n[5/5] Verifying tracing API...")
    from src.dashboard.tracing import trace_agent_task
    with trace_agent_task("agent-coder-01", "verification_test") as ctx:
        ctx.set_tokens(input_tokens=100, output_tokens=50)
        ctx.set_result("success")
        ctx.set_quality(1.0)
    print("  trace_agent_task context manager works.")

    print("\n" + "=" * 60)
    print("ALL CHECKS PASSED")
    print("=" * 60)
    print(f"\nTo launch the dashboard:")
    print(f"  streamlit run dashboard_app.py")
    print(f"\nThen click 'Load Demo Data' in the sidebar if starting fresh.")


if __name__ == "__main__":
    main()
