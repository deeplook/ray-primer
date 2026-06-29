"""Parallel execution — submit work first, then collect all results."""

import time

import ray

from _ray_config import init_ray

init_ray()


@ray.remote
def slow_square(value: int) -> int:
    time.sleep(0.15)
    return value * value


started = time.perf_counter()
refs = [slow_square.remote(value) for value in range(4)]
print("results:", ray.get(refs))
print(f"elapsed with two workers: {time.perf_counter() - started:.2f}s")
print("Submitting all calls before ray.get lets Ray run them concurrently.")
