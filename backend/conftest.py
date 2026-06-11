"""Pytest bootstrap — put backend/ on sys.path so `app` and `engine` import
regardless of pytest's import mode / rootdir."""
import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))
