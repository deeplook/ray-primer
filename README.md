# Ray Primer

[![CI](https://github.com/deeplook/ray-primer/actions/workflows/ci.yml/badge.svg)](https://github.com/deeplook/ray-primer/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/deeplook/ray-primer)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/downloads/release/python-3120/)
[![Ray](https://img.shields.io/badge/Ray-2.55-028CF0?logo=ray&logoColor=white)](https://www.ray.io/)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=flat&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/deeplook)

A collection of small, self-contained Ray scripts for learning distributed
Python on a local machine. The examples use the same APIs that scale to a
multi-node Ray cluster, but require no cloud account or cluster setup.

## Prerequisites

### 1. uv (Python package manager)

[uv](https://docs.astral.sh/uv/) manages Python and the virtual environment.

#### macOS

```bash
brew install uv
```

#### Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Windows

From PowerShell:

```powershell
winget install --id=astral-sh.uv -e
```

### 2. Python 3.12

The project pins Python 3.12 through `.python-version`. uv installs it with:

```bash
uv python install 3.12
```

## Installation

Clone the repository, then create the virtual environment and install Ray:

```bash
uv sync
```

No separate Ray service is needed. Each example starts a two-CPU Ray instance
inside its own process and shuts it down when the process exits.

## Multi-node cluster

An optional toolkit can run a real two-node Ray cluster from the main machine,
using Tailscale for private connectivity and SSH/rsync for worker management.
It includes prerequisite checks, synchronization, lifecycle commands, and four
examples that prove work occurred on distinct nodes.

See the [Tailscale cluster runbook](cluster/README.md) for setup, security,
shared-storage limitations, commands, and troubleshooting. No worker is needed
to run the normal local examples or unit tests.

## Docker

A container bundles Python 3.12, uv, and every Ray dependency, so the local
examples run without installing anything on the host. Build once:

```bash
docker build -t ray-primer .
```

Run an example by passing its script path:

```bash
docker run --rm ray-primer examples/02_remote_tasks.py
```

Ray keeps its object store in `/dev/shm`. All the examples here run fine on
Docker's 64 MB default — Ray simply warns and falls back to a `/tmp`-backed
store — but giving the container more shared memory silences the warning and is
closer to how you would run heavier workloads:

```bash
docker run --rm --shm-size=1g ray-primer examples/02_remote_tasks.py
```

The image installs PyTorch and Transformers (pulled in eagerly by Ray Data
LLM), so the first build is several gigabytes and takes a while. Pass secrets
such as the OpenAI key through the environment:

```bash
docker run --rm --shm-size=1g -e OPENAI_API_KEY ray-primer examples/33_llm_cloud.py
```

The multi-node cluster in `cluster/` is not containerized — it drives real
machines over Tailscale and SSH. For a containerized multi-node cluster, use
[KubeRay](https://docs.ray.io/en/latest/cluster/kubernetes/index.html) or the
Ray cluster launcher rather than this image.

## Modules

Run a script with `uv run examples/<file>`. The modules are intended to be
read in order.

| File | Topic |
|------|-------|
| `examples/01_ray_init.py` | Local initialization and cluster resources |
| `examples/02_remote_tasks.py` | Remote functions, tasks, and object references |
| `examples/03_parallel_execution.py` | Concurrent task submission |
| `examples/04_objects.py` | The distributed object store and `ray.put` |
| `examples/05_task_dependencies.py` | Dataflow dependencies between tasks |
| `examples/06_multiple_returns.py` | Tasks with multiple object references |
| `examples/07_actors.py` | Stateful actors |
| `examples/08_actor_ordering.py` | Serial method ordering within one actor |
| `examples/09_actor_pool.py` | Parallel work across multiple actors |
| `examples/10_resources.py` | CPU and custom logical resources |
| `examples/11_task_options.py` | Per-call names and resource overrides |
| `examples/12_wait.py` | Incremental result processing with `ray.wait` |
| `examples/13_cancellation.py` | Cancelling unnecessary work |
| `examples/14_fault_tolerance.py` | Retrying transient task failures |
| `examples/15_nested_tasks.py` | Tasks that submit child tasks |
| `examples/16_runtime_context.py` | Job, node, task, and worker identity |
| `examples/17_datasets.py` | Creating Ray Datasets from Python objects |
| `examples/18_reading_csv.py` | Reading CSV into a distributed Dataset |
| `examples/19_dataset_transforms.py` | Lazy `map` and `filter` transforms |
| `examples/20_batch_transforms.py` | Vectorized pandas batch transforms |
| `examples/21_aggregations_and_parquet.py` | Grouped aggregation and Parquet I/O |
| `examples/22_async_actors.py` | Concurrent asynchronous actor methods |
| `examples/23_named_actors.py` | Named and detached actor discovery |
| `examples/24_placement_groups.py` | Atomic resource reservation and gang scheduling |
| `examples/25_scheduling_strategies.py` | Spread scheduling and node affinity |
| `examples/26_streaming_generators.py` | Streaming task results with remote generators |
| `examples/27_runtime_environments.py` | Per-task dependencies and environment variables |
| `examples/28_supervisor_pattern.py` | Supervisor-owned worker actors |
| `examples/29_backpressure.py` | Bounded task submission with backpressure |
| `examples/30_serve.py` | Deploying callable services with Ray Serve |
| `examples/31_train.py` | Data-parallel workers and dataset sharding with Ray Train |
| `examples/32_tune.py` | Hyperparameter search with Ray Tune |
| `examples/33_llm_cloud.py` | Calling a cloud-hosted model with Ray Data LLM |

Run the cloud LLM example after exporting an OpenAI API key:

```bash
export OPENAI_API_KEY="your-api-key"
uv run examples/33_llm_cloud.py
```

## Running all tests

The pytest suite starts every module in a fresh subprocess and checks that it
exits successfully:

```bash
uv run python -m pytest -v
```

## Notes

- Ray's CPU, GPU, and custom resources are logical scheduling capacity. They
  do not enforce physical CPU or memory isolation.
- Remote calls return `ObjectRef` futures immediately. Use `ray.get` only when
  the driver actually needs a value, so independent work can overlap.
- Actor methods share mutable state and run serially by default; methods on
  different actors can run concurrently.
- `examples/27_runtime_environments.py` asks Ray to build a per-task `uv`
  environment, so its first run may take longer while that environment is cached.
- `examples/31_train.py` enables Ray Train V2, whose base trainer API is still
  marked as a developer API by Ray.
- `examples/33_llm_cloud.py` sends one request to OpenAI using `gpt-4o-mini`
  with an eight-token output limit. Set `OPENAI_API_KEY` to run it; without a
  key, the example exits without making a request. Ray 2.55.1 eagerly imports
  its cloud-storage and local-engine support when `ray.data.llm` is loaded, so
  `boto3`, PyTorch, and Transformers are installed even though this example
  only calls a hosted HTTP endpoint.
- `examples/18_reading_csv.py` uses the included `data/tips.csv` sample.
- `examples/21_aggregations_and_parquet.py` writes generated files under
  `out/tips_by_day/`, which is ignored by Git.

## Further reading

- [Ray Core walkthrough](https://docs.ray.io/en/latest/ray-core/walkthrough.html)
- [Ray Data quickstart](https://docs.ray.io/en/latest/data/quickstart.html)
- [Ray Data LLM guide](https://docs.ray.io/en/latest/data/working-with-llms.html)
- [Ray cluster configuration](https://docs.ray.io/en/latest/cluster/getting-started.html)
