# Covers the local single-node examples (01-33). uv manages Python 3.12 (from
# .python-version) and installs Ray with its data/serve/train/tune extras.
#
# Note: Ray's object store lives in /dev/shm. These examples all run on
# Docker's 64 MB default (Ray warns and falls back to /tmp); `--shm-size=1g`
# silences the warning and suits heavier workloads (see README).
#
# The multi-node cluster/ toolkit (Tailscale + SSH across real machines) is
# deliberately not containerized.
FROM python:3.12-slim

# uv, copied from its official distroless image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Use the locked environment as-is; never re-resolve at runtime.
ENV UV_FROZEN=1

WORKDIR /app
COPY . .
# Pulls in PyTorch and Transformers (eager deps of Ray Data LLM), so this
# layer is several gigabytes and slow on first build.
RUN uv sync

# `uv run <script>` is the same command used on the host.
ENTRYPOINT ["uv", "run"]
CMD ["examples/01_ray_init.py"]
