"""Objects — share immutable values through Ray's object store."""

import ray

from _ray_config import init_ray

init_ray()


@ray.remote
def summarize(values: list[int]) -> tuple[int, int]:
    return len(values), sum(values)


values_ref = ray.put(list(range(10_000)))
print("stored as:", values_ref)
print("summary:", ray.get(summarize.remote(values_ref)))
print("round trip:", ray.get(values_ref)[:5])
