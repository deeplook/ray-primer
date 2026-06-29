"""Runtime environments — configure dependencies and environment per worker."""

import os

import ray
from ray.runtime_env import RuntimeEnv

from _ray_config import init_ray

init_ray()


@ray.remote
def environment() -> tuple[str, str]:
    import six

    return os.environ["PRIMER_MODE"], six.__version__


runtime_env = RuntimeEnv(
    env_vars={"PRIMER_MODE": "distributed"},
    uv=["six==1.17.0"],
)
result = ray.get(environment.options(runtime_env=runtime_env).remote())
print("worker environment:", result)
print("driver has variable:", "PRIMER_MODE" in os.environ)
