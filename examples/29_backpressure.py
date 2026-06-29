"""Backpressure — bound the pending task queue with ray.wait."""

import time

import ray

from _ray_config import init_ray

init_ray()


@ray.remote
def process(value: int) -> int:
    time.sleep(0.05)
    return value * 2


limit = 3
pending: list[ray.ObjectRef] = []
results: list[int] = []
peak_pending = 0

for value in range(10):
    if len(pending) >= limit:
        ready, pending = ray.wait(pending, num_returns=1)
        results.extend(ray.get(ready))
    pending.append(process.remote(value))
    peak_pending = max(peak_pending, len(pending))

results.extend(ray.get(pending))
print("results:", sorted(results))
print("peak pending tasks:", peak_pending)
