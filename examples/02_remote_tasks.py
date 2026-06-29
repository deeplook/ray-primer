"""Remote tasks — turn ordinary functions into distributed work."""

import os

import ray

from _ray_config import init_ray

init_ray()


@ray.remote
def square(value: int) -> tuple[int, int]:
    return value * value, os.getpid()


refs = [square.remote(value) for value in range(6)]
print("object refs:", refs)
print("(square, worker pid):", ray.get(refs))
