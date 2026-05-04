"""Pytest configuration for E-Tag Display tests."""
import sys
from pathlib import Path

# Add homeassistant/ to Python path so imports work
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "homeassistant"))
