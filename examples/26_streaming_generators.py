"""Remote generators — consume outputs before the producing task finishes."""

import time
from collections.abc import Generator

import ray

from _ray_config import init_ray

init_ray()


@ray.remote
def stream_squares(count: int) -> Generator[int, None, None]:
    for value in range(count):
        time.sleep(0.05)
        yield value * value


generator = stream_squares.remote(5)
for object_ref in generator:
    print("received:", ray.get(object_ref))
