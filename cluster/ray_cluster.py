#!/usr/bin/env python3
"""Manage a two-node Ray learning cluster over Tailscale and SSH."""

from __future__ import annotations

import argparse
import ipaddress
import os
import re
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "cluster" / "cluster.env"
SSH_TARGET_RE = re.compile(r"^[A-Za-z0-9._-]+@[A-Za-z0-9._:-]+$")
REMOTE_DIR_RE = re.compile(r"^[A-Za-z0-9._/+-]+$")


class ClusterError(RuntimeError):
    """A user-actionable cluster configuration or command failure."""


def parse_env_file(path: Path) -> dict[str, str]:
    """Parse a small KEY=VALUE file without modifying os.environ."""
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for line_number, raw_line in enumerate(path.read_text().splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            raise ClusterError(f"{path}:{line_number}: expected KEY=VALUE")
        key, value = line.split("=", 1)
        key = key.strip()
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", key):
            raise ClusterError(f"{path}:{line_number}: invalid variable name {key!r}")
        value = value.strip()
        if value[:1] in {"'", '"'}:
            parsed = shlex.split(value, comments=False, posix=True)
            if len(parsed) != 1:
                raise ClusterError(f"{path}:{line_number}: expected one quoted value")
            value = parsed[0]
        values[key] = value
    return values


def setting(name: str, file_values: Mapping[str, str], default: str = "") -> str:
    return os.environ.get(name, file_values.get(name, default)).strip()


def optional_positive_int(name: str, value: str) -> int | None:
    if not value:
        return None
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ClusterError(f"{name} must be an integer, got {value!r}") from exc
    if parsed <= 0:
        raise ClusterError(f"{name} must be greater than zero")
    return parsed


@dataclass(frozen=True)
class ClusterConfig:
    worker_ssh: str
    remote_dir: str
    head_ip: str | None
    head_port: int
    ssh_port: int | None
    ssh_identity: Path | None
    head_cpus: int | None
    worker_cpus: int | None

    @classmethod
    def load(cls, path: Path) -> "ClusterConfig":
        values = parse_env_file(path)
        worker_ssh = setting("RAY_WORKER_SSH", values)
        remote_dir = setting("RAY_REMOTE_DIR", values, "ray_primer")
        head_ip = setting("RAY_HEAD_IP", values) or None
        head_port = optional_positive_int(
            "RAY_HEAD_PORT", setting("RAY_HEAD_PORT", values, "6379")
        )
        assert head_port is not None
        ssh_port = optional_positive_int(
            "RAY_SSH_PORT", setting("RAY_SSH_PORT", values)
        )
        identity_value = setting("RAY_SSH_IDENTITY", values)
        ssh_identity = Path(identity_value).expanduser() if identity_value else None
        config = cls(
            worker_ssh=worker_ssh,
            remote_dir=remote_dir,
            head_ip=head_ip,
            head_port=head_port,
            ssh_port=ssh_port,
            ssh_identity=ssh_identity,
            head_cpus=optional_positive_int(
                "RAY_HEAD_CPUS", setting("RAY_HEAD_CPUS", values)
            ),
            worker_cpus=optional_positive_int(
                "RAY_WORKER_CPUS", setting("RAY_WORKER_CPUS", values)
            ),
        )
        config.validate(path)
        return config

    def validate(self, path: Path) -> None:
        if not self.worker_ssh:
            raise ClusterError(
                f"RAY_WORKER_SSH is missing. Copy cluster.env.example to {path}."
            )
        if not SSH_TARGET_RE.fullmatch(self.worker_ssh):
            raise ClusterError("RAY_WORKER_SSH must look like user@host")
        if not REMOTE_DIR_RE.fullmatch(self.remote_dir) or self.remote_dir.startswith(
            "~"
        ):
            raise ClusterError(
                "RAY_REMOTE_DIR must be an absolute or home-relative path without '~' or spaces"
            )
        if self.head_ip:
            validate_ipv4(self.head_ip, "RAY_HEAD_IP")
        if self.ssh_identity and not self.ssh_identity.is_file():
            raise ClusterError(f"SSH identity does not exist: {self.ssh_identity}")

    @property
    def ssh_args(self) -> list[str]:
        args = ["-o", "ConnectTimeout=10"]
        if self.ssh_port:
            args += ["-p", str(self.ssh_port)]
        if self.ssh_identity:
            args += ["-i", str(self.ssh_identity)]
        return args


def validate_ipv4(value: str, name: str) -> str:
    try:
        address = ipaddress.ip_address(value)
    except ValueError as exc:
        raise ClusterError(f"{name} is not a valid IP address: {value!r}") from exc
    if address.version != 4:
        raise ClusterError(f"{name} must be an IPv4 address")
    return str(address)


class Runner:
    def __init__(self, *, dry_run: bool = False, verbose: bool = False) -> None:
        self.dry_run = dry_run
        self.verbose = verbose

    def run(
        self,
        command: Sequence[str],
        *,
        capture: bool = False,
        check: bool = True,
        mutate: bool = False,
        env: Mapping[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        if self.verbose or mutate:
            prefix = "would run" if self.dry_run and mutate else "run"
            print(f"{prefix}: {shlex.join(command)}", file=sys.stderr)
        if self.dry_run and mutate:
            return subprocess.CompletedProcess(command, 0, "", "")
        return subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=capture,
            check=check,
        )


class ClusterManager:
    def __init__(self, config: ClusterConfig, runner: Runner) -> None:
        self.config = config
        self.runner = runner

    def require_commands(self) -> None:
        missing = [
            name
            for name in ("ssh", "rsync", "tailscale", "uv")
            if not shutil.which(name)
        ]
        if missing:
            raise ClusterError(f"Missing local commands: {', '.join(missing)}")

    def local_tailscale_ip(self) -> str:
        if self.config.head_ip:
            return self.config.head_ip
        result = self.runner.run(["tailscale", "ip", "-4"], capture=True)
        candidates = [
            line.strip() for line in result.stdout.splitlines() if line.strip()
        ]
        if not candidates:
            raise ClusterError("Tailscale returned no IPv4 address on the main machine")
        return validate_ipv4(candidates[0], "local Tailscale IP")

    def ssh(
        self,
        script: str,
        *,
        capture: bool = False,
        check: bool = True,
        mutate: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        command = [
            "ssh",
            *self.config.ssh_args,
            self.config.worker_ssh,
            f"sh -lc {shlex.quote(script)}",
        ]
        return self.runner.run(command, capture=capture, check=check, mutate=mutate)

    def remote_tailscale_ip(self) -> str:
        result = self.ssh("tailscale ip -4", capture=True)
        candidates = [
            line.strip() for line in result.stdout.splitlines() if line.strip()
        ]
        if not candidates:
            raise ClusterError("Tailscale returned no IPv4 address on the worker")
        return validate_ipv4(candidates[0], "worker Tailscale IP")

    def check(self) -> tuple[str, str]:
        self.require_commands()
        head_ip = self.local_tailscale_ip()
        self.ssh(
            "command -v tailscale >/dev/null && "
            "command -v uv >/dev/null && "
            "command -v rsync >/dev/null"
        )
        worker_ip = self.remote_tailscale_ip()
        if head_ip == worker_ip:
            raise ClusterError("Head and worker resolved to the same Tailscale IP")
        print(f"head:   {head_ip}")
        print(f"worker: {worker_ip} ({self.config.worker_ssh})")
        print("SSH, Tailscale, uv, and rsync prerequisites are available.")
        return head_ip, worker_ip

    def sync(self) -> None:
        self.require_commands()
        remote_dir = shlex.quote(self.config.remote_dir)
        self.ssh(f"mkdir -p {remote_dir}", mutate=True)
        ssh_transport = shlex.join(["ssh", *self.config.ssh_args])
        command = [
            "rsync",
            "-az",
            "--exclude=.git/",
            "--exclude=.venv/",
            "--exclude=out/",
            "--exclude=__pycache__/",
            "--exclude=cluster/cluster.env",
            "-e",
            ssh_transport,
            f"{ROOT}/",
            f"{self.config.worker_ssh}:{self.config.remote_dir.rstrip('/')}/",
        ]
        self.runner.run(command, mutate=True)

    def stop(self, *, check: bool = False) -> None:
        remote_dir = shlex.quote(self.config.remote_dir)
        self.ssh(
            f"cd {remote_dir} && uv run ray stop --force",
            check=check,
            mutate=True,
        )
        self.runner.run(
            ["uv", "run", "ray", "stop", "--force"], check=check, mutate=True
        )

    def up(self, *, restart: bool = False) -> None:
        head_ip, worker_ip = self.check()
        if restart:
            self.stop(check=False)
        self.runner.run(["uv", "sync", "--frozen"], mutate=True)
        self.sync()

        head_command = [
            "uv",
            "run",
            "ray",
            "start",
            "--head",
            f"--node-ip-address={head_ip}",
            f"--port={self.config.head_port}",
            "--dashboard-host=127.0.0.1",
        ]
        if self.config.head_cpus:
            head_command.append(f"--num-cpus={self.config.head_cpus}")
        self.runner.run(head_command, mutate=True)

        remote_dir = shlex.quote(self.config.remote_dir)
        worker_command = (
            f"cd {remote_dir} && uv sync --frozen && "
            "uv run ray start "
            f"--node-ip-address={shlex.quote(worker_ip)} "
            f"--address={shlex.quote(f'{head_ip}:{self.config.head_port}')}"
        )
        if self.config.worker_cpus:
            worker_command += f" --num-cpus={self.config.worker_cpus}"
        self.ssh(worker_command, mutate=True)
        print(f"Cluster started. RAY_ADDRESS={head_ip}:{self.config.head_port}")

    def status(self) -> None:
        head_ip = self.local_tailscale_ip()
        self.runner.run(
            [
                "uv",
                "run",
                "ray",
                "status",
                f"--address={head_ip}:{self.config.head_port}",
            ]
        )

    def run_example(self, script: str, script_args: Sequence[str]) -> None:
        path = (ROOT / script).resolve()
        try:
            path.relative_to(ROOT)
        except ValueError as exc:
            raise ClusterError("Script must be inside the repository") from exc
        if not path.is_file():
            raise ClusterError(f"Script does not exist: {script}")
        head_ip = self.local_tailscale_ip()
        env = {
            **os.environ,
            "RAY_ADDRESS": f"{head_ip}:{self.config.head_port}",
        }
        self.runner.run(
            ["uv", "run", "python", str(path), *script_args],
            env=env,
            mutate=True,
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage a two-node Ray cluster over Tailscale and SSH."
    )
    parser.add_argument(
        "--config", type=Path, default=DEFAULT_CONFIG, help="cluster.env path"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="print mutations without running them"
    )
    parser.add_argument("--verbose", action="store_true", help="print every command")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("check", help="validate local and remote prerequisites")
    subparsers.add_parser("sync", help="copy the project to the worker with rsync")
    up = subparsers.add_parser("up", help="synchronize and start both Ray nodes")
    up.add_argument(
        "--restart", action="store_true", help="stop existing Ray processes first"
    )
    subparsers.add_parser("status", help="show Ray cluster status")
    subparsers.add_parser("down", help="stop Ray on the worker and main machine")
    run = subparsers.add_parser("run", help="run a repository script on the cluster")
    run.add_argument("script", help="path relative to the repository root")
    run.add_argument(
        "args", nargs=argparse.REMAINDER, help="arguments passed to the script"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = ClusterConfig.load(args.config.resolve())
        manager = ClusterManager(
            config,
            Runner(dry_run=args.dry_run, verbose=args.verbose),
        )
        if args.command == "check":
            manager.check()
        elif args.command == "sync":
            manager.sync()
        elif args.command == "up":
            manager.up(restart=args.restart)
        elif args.command == "status":
            manager.status()
        elif args.command == "down":
            manager.stop(check=False)
        elif args.command == "run":
            manager.run_example(args.script, args.args)
        return 0
    except (ClusterError, subprocess.CalledProcessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
