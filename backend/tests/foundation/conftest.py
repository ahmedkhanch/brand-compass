"""Isolated migrated database for F04-A HTTP integration tests."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

_DB_FILE = Path(tempfile.gettempdir()) / "radaros-f04-boundary.db"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_DB_FILE}"
os.environ["DEMO_MODE"] = "true"
os.environ["ALLOW_DEMO_AUTH"] = "true"


@pytest.fixture(scope="session", autouse=True)
def migrated_database():
    _DB_FILE.unlink(missing_ok=True)
    backend = Path(__file__).resolve().parents[2]
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=backend,
        env=os.environ.copy(),
        check=True,
    )
    yield
    _DB_FILE.unlink(missing_ok=True)
