# Two-node Ray cluster over Tailscale

This directory contains an optional orchestration command for learning how Ray
behaves across two real machines. The main machine is both the control machine
and Ray head. A second machine joins as a worker over Tailscale. All commands
are issued from the main machine.

```text
main machine                                  worker machine
┌──────────────────────────┐                  ┌──────────────────────┐
│ driver + Ray head        │  Tailscale VPN  │ Ray worker           │
│ cluster/ray_cluster.py   │◀───────────────▶│ managed through SSH  │
│ examples/cluster/*.py    │                  │ synchronized by rsync│
└──────────────────────────┘                  └──────────────────────┘
```

The normal examples remain local by default. Nothing in this directory runs
unless you explicitly invoke the cluster command.

The orchestration command targets macOS and Linux hosts with a POSIX shell.
Windows can run Ray, but this SSH/rsync workflow does not currently support a
Windows worker.

The automated test suite exercises the cluster examples against two Ray nodes
on one machine. That verifies their scheduling APIs without contacting SSH or
Tailscale; the runbook is still needed to demonstrate physical network and
cross-machine object transfer.

## What can be prepared before the worker exists?

The command, configuration template, examples, and tests are ready now. When a
worker becomes available, it needs:

- Tailscale, signed into the same tailnet as the main machine;
- an existing operating-system user reachable through SSH;
- `uv` on the non-interactive SSH `PATH`;
- `rsync` on both machines;
- enough free disk space for the project and uv environment;
- sleep disabled while the worker is participating in the cluster;
- a firewall and Tailscale policy allowing bidirectional traffic between the
  two Tailscale addresses.

Python and Ray do not need to be installed manually. `uv sync --frozen`
installs the locked Python version and dependencies on the worker.

Before configuring the project, this remote bootstrap check should print four
paths and a Tailscale IPv4 address:

```bash
ssh user@ray-worker '
  command -v sh
  command -v tailscale
  command -v uv
  command -v rsync
  tailscale ip -4
'
```

Install missing tools using the worker operating system's normal package
manager. For uv and Tailscale, use their official installation instructions:

- [Install uv](https://docs.astral.sh/uv/getting-started/installation/)
- [Install Tailscale](https://tailscale.com/download)

## 1. Verify Tailscale and SSH

On the main machine, list the tailnet and find the future worker's MagicDNS
name:

```bash
tailscale status
tailscale ping ray-worker
ssh user@ray-worker hostname
```

`tailscale ping` should ideally report a direct connection. A DERP-relayed
connection works, but large Ray object transfers may be much slower.

Regular OpenSSH over Tailscale is sufficient. Tailscale SSH is optional. When
using Tailscale SSH, enable it on the worker and ensure the tailnet SSH policy
allows the intended local user.

## 2. Configure this project

From the repository root:

```bash
cp cluster/cluster.env.example cluster/cluster.env
```

Edit `cluster/cluster.env`:

```bash
RAY_WORKER_SSH=user@ray-worker
RAY_REMOTE_DIR=ray_primer
```

`cluster/cluster.env` is ignored by Git. Environment variables override values
from the file, which is useful for temporary changes:

```bash
RAY_WORKER_SSH=user@another-worker \
  uv run cluster/ray_cluster.py check
```

The head address is discovered with `tailscale ip -4`. Set `RAY_HEAD_IP`
only if the main machine has multiple Tailscale addresses or discovery is not
appropriate. Optional CPU overrides control the logical resources advertised
to Ray:

```bash
RAY_HEAD_CPUS=4
RAY_WORKER_CPUS=8
```

## 3. Validate prerequisites

```bash
uv run cluster/ray_cluster.py check
```

This is read-only. It verifies local `ssh`, `rsync`, `tailscale`, and `uv`,
connects to the worker, checks remote Tailscale, uv, and rsync availability,
and prints both Tailscale IPv4 addresses.

To inspect commands without changing either machine:

```bash
uv run cluster/ray_cluster.py --dry-run --verbose up
```

Global options such as `--dry-run`, `--verbose`, and `--config` must appear
before the subcommand.

## 4. Start the cluster

```bash
uv run cluster/ray_cluster.py up
```

`up` performs these operations:

1. validates both machines;
2. runs `uv sync --frozen` locally;
3. creates the remote project directory;
4. synchronizes the repository with `rsync` while excluding `.git`, `.venv`,
   generated output, caches, and the private `cluster.env`;
5. starts the head bound to the main machine's Tailscale IPv4;
6. runs `uv sync --frozen` remotely;
7. starts the worker using its Tailscale IPv4.

It does not stop existing Ray processes automatically. If a previous tutorial
cluster is still running, explicitly restart it:

```bash
uv run cluster/ray_cluster.py up --restart
```

`--restart` and `down` run `ray stop --force` on both machines. They can stop
unrelated Ray work owned by the same user, so use them deliberately.

If `up` fails after the head starts but before the worker joins, it leaves the
head running for inspection. Correct the reported worker error, then use
`up --restart`; or clean up with `down`.

## 5. Inspect and exercise the cluster

```bash
uv run cluster/ray_cluster.py status

uv run cluster/ray_cluster.py run examples/cluster/01_nodes.py
uv run cluster/ray_cluster.py run examples/cluster/02_one_task_per_node.py
uv run cluster/ray_cluster.py run examples/cluster/03_cross_node_objects.py
uv run cluster/ray_cluster.py run examples/cluster/04_strict_spread.py
```

The examples intentionally require at least two live nodes:

| File | Demonstration |
|------|---------------|
| `01_nodes.py` | Live node inventory and logical resources |
| `02_one_task_per_node.py` | Hard node affinity, with one task on each node |
| `03_cross_node_objects.py` | A 4 MiB object produced and consumed on different nodes |
| `04_strict_spread.py` | Atomic resource reservation across distinct nodes |

The `run` command sets `RAY_ADDRESS` only for the child process. Existing
top-level examples that do not configure local cluster resources can also be
tried through it, although their small workloads might use only one node.

### Dashboard and logs

While the cluster is running, the dashboard is available only on the main
machine:

```text
http://127.0.0.1:8265
```

Ray keeps the current session logs under `/tmp/ray/session_latest/logs` on each
machine. Inspect the worker logs remotely:

```bash
ssh user@ray-worker 'ls -lt /tmp/ray/session_latest/logs | head'
```

The cluster command intentionally does not expose the dashboard through
Tailscale. If browser access from another device is needed, use an SSH tunnel
instead of changing the dashboard bind address.

## 6. Synchronize changes

After editing code on the main machine:

```bash
uv run cluster/ray_cluster.py sync
```

Synchronization does not use `--delete`, so files created independently on the
worker are not removed. The main machine remains the source of truth for files
with matching paths.

## 7. Stop the cluster

```bash
uv run cluster/ray_cluster.py down
```

The command attempts the worker shutdown first and then always attempts the
local shutdown. If the worker is unreachable, reconnect it and run `down`
again, or execute this on the worker:

```bash
cd ray_primer
uv run ray stop --force
```

## Network and security

Ray assumes all code and machines inside a cluster are trusted. Do not expose
the GCS port, dashboard, Ray Client, or worker ports to the public internet.
The head advertises only its Tailscale address, and the dashboard listens only
on `127.0.0.1` on the main machine.

Ray uses the GCS port plus dynamically selected ports for node managers, object
managers, runtime-environment agents, dashboard agents, metrics, and workers.
The simplest tailnet policy is bidirectional connectivity between only the two
Ray machines. If the tailnet uses restrictive grants, allow all IP protocols
between their device IPs or dedicated Ray device tags. SSH permission alone is
not enough for Ray's direct node-to-node communication.

## Files and shared storage

Core tasks, actors, object references, node affinity, and placement groups need
no shared filesystem. Code in remote functions is serialized by Ray.

File-based examples need additional care:

- A path without `local://` must be accessible at the same path on every node
  that may execute a read.
- `local://` deliberately reads only from the local node and does not provide a
  distributed read.
- Ray Data output, Ray Train storage, and Ray Tune storage should use a shared
  NFS mount or object storage such as S3 for real multi-node workloads.
- The existing CSV, Parquet, Train, and Tune tutorial modules use local paths
  and are therefore not claimed as multi-node examples.

## Troubleshooting

### `uv` is not found over SSH

Interactive and non-interactive SSH sessions may have different `PATH` values.
Ensure the uv installation directory is initialized from the worker user's
login profile, then verify:

```bash
ssh user@ray-worker 'sh -lc "command -v uv && uv --version"'
```

### The worker cannot connect to GCS

Check the advertised addresses and connectivity from both directions:

```bash
tailscale ip -4
tailscale ping ray-worker
ssh user@ray-worker 'tailscale ping MAIN_MACHINE_NAME'
```

Confirm the tailnet policy permits non-SSH traffic between the machines and
that the host firewall does not block traffic arriving on the Tailscale
interface.

### The cluster has only one node

Run `status`, then inspect Ray on the worker:

```bash
uv run cluster/ray_cluster.py status
ssh user@ray-worker 'cd ray_primer && uv run ray status'
```

Ray and Python versions must match. Re-run `sync`, `uv sync --frozen`, and
`up --restart` if the environments diverged.

### A node disappears after initially joining

Check whether the machine slept, rebooted, changed tailnet authorization, or
fell back to an unstable network connection. Ray processes started by this
tutorial are not operating-system services and do not restart after reboot.
Wake or repair the node, verify `tailscale ping`, then run `up --restart`.

### Strict-spread placement remains pending

Both nodes must be alive and advertise at least `0.1` logical CPU. Remove CPU
overrides that set a node below that requirement, or restart with suitable
`RAY_HEAD_CPUS` and `RAY_WORKER_CPUS` values.

## Deliberate limitations

This is a learning setup, not a production cluster manager:

- exactly one main/head machine and one SSH worker are supported;
- there is no autoscaling, health daemon, reboot persistence, or automatic
  recovery of the worker process;
- synchronization is one-way from the main machine and does not delete remote
  files;
- secrets and datasets are not distributed automatically;
- shared storage is not provisioned;
- dynamic Ray ports require broad connectivity between these two trusted
  tailnet devices;
- physical Tailscale and SSH behavior cannot be validated until a worker is
  available.

For more nodes, long-running services, or untrusted workloads, move to Ray's
cluster launcher, KubeRay, or a managed Ray platform rather than extending this
script into an infrastructure manager.

## References

- [Ray on-premises cluster guide](https://docs.ray.io/en/latest/cluster/vms/user-guides/launching-clusters/on-premises.html)
- [Ray network port configuration](https://docs.ray.io/en/latest/ray-core/configure.html#ports-configurations)
- [Ray security guidance](https://docs.ray.io/en/latest/ray-security/index.html)
- [Tailscale MagicDNS](https://tailscale.com/docs/features/magicdns)
- [Tailscale SSH](https://tailscale.com/docs/features/tailscale-ssh)
- [Tailscale connection types](https://tailscale.com/docs/reference/connection-types)
