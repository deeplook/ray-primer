"""Multiple returns — expose independent results as separate object refs."""

import ray

from _ray_config import init_ray

init_ray()


@ray.remote(num_returns=2)
def min_and_max(values: list[int]) -> tuple[int, int]:
    return min(values), max(values)


minimum_ref, maximum_ref = min_and_max.remote([8, 3, 13, 5, 2])
print("minimum:", ray.get(minimum_ref))
print("maximum:", ray.get(maximum_ref))
