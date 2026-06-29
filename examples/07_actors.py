"""Actors — keep mutable state in a dedicated worker process."""

import ray

from _ray_config import init_ray

init_ray()


@ray.remote(num_cpus=1)
class Counter:
    def __init__(self) -> None:
        self.value = 0

    def increment(self, amount: int = 1) -> int:
        self.value += amount
        return self.value

    def get(self) -> int:
        return self.value


counter = Counter.remote()
print("successive values:", ray.get([counter.increment.remote() for _ in range(3)]))
print("final value:", ray.get(counter.get.remote()))
