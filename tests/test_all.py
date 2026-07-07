"""Run every tutorial module in a fresh Python process."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
MODULES = sorted((ROOT_DIR / "examples").glob("[0-9][0-9]_*.py"))

# These examples need resources declared at cluster-start time, so they cannot
# connect to the shared session cluster via RAY_ADDRESS.
STANDALONE = {"10_resources.py"}


@pytest.mark.parametrize("module", MODULES, ids=lambda path: path.name)
def test_module_runs(module: Path, ray_cluster: str) -> None:
    env = os.environ.copy()
    if module.name in STANDALONE:
        env.pop("RAY_ADDRESS", None)
    if module.name == "33_llm_cloud.py":
        env.pop("OPENAI_API_KEY", None)
    result = subprocess.run(
        [sys.executable, str(module)],
        capture_output=True,
        env=env,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, (
        f"{module.name} exited with code {result.returncode}\n"
        f"--- stdout ---\n{result.stdout[-3000:]}\n"
        f"--- stderr ---\n{result.stderr[-3000:]}"
    )
