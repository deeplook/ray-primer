"""Unit tests for cluster configuration that require no SSH worker."""

from pathlib import Path

import pytest

from cluster.ray_cluster import (
    ClusterConfig,
    ClusterError,
    build_parser,
    parse_env_file,
)

VARIABLES = [
    "RAY_WORKER_SSH",
    "RAY_REMOTE_DIR",
    "RAY_HEAD_IP",
    "RAY_HEAD_PORT",
    "RAY_SSH_PORT",
    "RAY_SSH_IDENTITY",
    "RAY_HEAD_CPUS",
    "RAY_WORKER_CPUS",
]


@pytest.fixture(autouse=True)
def clean_cluster_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for variable in VARIABLES:
        monkeypatch.delenv(variable, raising=False)


def test_parse_env_file(tmp_path: Path) -> None:
    path = tmp_path / "cluster.env"
    path.write_text(
        "# comment\n"
        "RAY_WORKER_SSH=user@worker\n"
        "export RAY_REMOTE_DIR='projects/ray_primer'\n"
    )

    assert parse_env_file(path) == {
        "RAY_WORKER_SSH": "user@worker",
        "RAY_REMOTE_DIR": "projects/ray_primer",
    }


def test_load_config_with_defaults(tmp_path: Path) -> None:
    path = tmp_path / "cluster.env"
    path.write_text("RAY_WORKER_SSH=user@ray-worker\n")

    config = ClusterConfig.load(path)

    assert config.worker_ssh == "user@ray-worker"
    assert config.remote_dir == "ray_primer"
    assert config.head_port == 6379


def test_environment_overrides_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "cluster.env"
    path.write_text("RAY_WORKER_SSH=user@old-worker\n")
    monkeypatch.setenv("RAY_WORKER_SSH", "user@new-worker")

    assert ClusterConfig.load(path).worker_ssh == "user@new-worker"


def test_missing_worker_has_actionable_error(tmp_path: Path) -> None:
    with pytest.raises(ClusterError, match="cluster.env.example"):
        ClusterConfig.load(tmp_path / "missing.env")


def test_rejects_unsafe_remote_directory(tmp_path: Path) -> None:
    path = tmp_path / "cluster.env"
    path.write_text("RAY_WORKER_SSH=user@worker\nRAY_REMOTE_DIR=ray primer;oops\n")

    with pytest.raises(ClusterError, match="RAY_REMOTE_DIR"):
        ClusterConfig.load(path)


def test_parser_accepts_cluster_example() -> None:
    args = build_parser().parse_args(
        ["--dry-run", "run", "examples/cluster/01_nodes.py"]
    )

    assert args.command == "run"
    assert args.script == "examples/cluster/01_nodes.py"
