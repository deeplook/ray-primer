"""Incremental results — use ray.wait when results finish at different times."""

import time

import ray

from _ray_config import init_ray

init_ray()


@ray.remote
def delayed(value: int, delay: float) -> int:
    time.sleep(delay)
    return value


pending = [delayed.remote(1, 0.15), delayed.remote(2, 0.05), delayed.remote(3, 0.1)]
completion_order: list[int] = []
while pending:
    ready, pending = ray.wait(pending, num_returns=1)
    completion_order.extend(ray.get(ready))

print("completion order:", completion_order)
