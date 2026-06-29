"""Cancellation — stop work that is no longer needed."""

import time

import ray
from ray.exceptions import TaskCancelledError

from _ray_config import init_ray

init_ray()


@ray.remote
def slow_operation() -> str:
    time.sleep(30)
    return "finished"


ref = slow_operation.remote()
ray.cancel(ref)
try:
    ray.get(ref)
except TaskCancelledError:
    print("task cancelled")
