"""Nested tasks — remote functions can submit more remote work."""

import ray

from _ray_config import init_ray

init_ray()


@ray.remote(num_cpus=0)
def square(value: int) -> int:
    return value * value


@ray.remote(num_cpus=0)
def sum_of_squares(values: list[int]) -> int:
    return sum(ray.get([square.remote(value) for value in values]))


print("sum of squares:", ray.get(sum_of_squares.remote(list(range(10)))))
print("Resource requirements matter: blocking parent tasks can otherwise starve children.")
