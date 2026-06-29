"""Run multi-node examples on two local Ray nodes without SSH."""

import os
import subprocess
import sys
from pathlib import Path

from ray.cluster_utils import Cluster

ROOT_DIR = Path(__file__).resolve().parent.parent
MODULES = sorted((ROOT_DIR / "examples" / "cluster").glob("[0-9][0-9]_*.py"))


def test_cluster_modules_run() -> None:
    cluster = Cluster(
        initialize_head=True,
        connect=False,
        head_node_args={"num_cpus": 1, "include_dashboard": False},
    )
    cluster.add_node(num_cpus=1)
    try:
        environment = {**os.environ, "RAY_ADDRESS": cluster.address}
        for module in MODULES:
            result = subprocess.run(
                [sys.executable, str(module)],
                capture_output=True,
                text=True,
                timeout=90,
                env=environment,
            )
            assert result.returncode == 0, (
                f"{module.name} exited with code {result.returncode}\n"
                f"--- stdout ---\n{result.stdout[-3000:]}\n"
                f"--- stderr ---\n{result.stderr[-3000:]}"
            )
    finally:
        cluster.shutdown()
