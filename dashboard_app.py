"""Launch the Agent Performance Dashboard.

Run with: streamlit run dashboard_app.py
"""
import sys
from pathlib import Path

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).parent))

from src.dashboard.app import main

if __name__ == "__main__":
    main()
