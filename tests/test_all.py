"""Run every tutorial module in a fresh Python process."""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
MODULES = sorted((ROOT_DIR / "examples").glob("[0-9][0-9]_*.py"))


@pytest.mark.parametrize("module", MODULES, ids=lambda path: path.name)
def test_module_runs(module: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(module)],
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, (
        f"{module.name} exited with code {result.returncode}\n"
        f"--- stdout ---\n{result.stdout[-3000:]}\n"
        f"--- stderr ---\n{result.stderr[-3000:]}"
    )
