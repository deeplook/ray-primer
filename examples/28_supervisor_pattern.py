"""Supervisor pattern — let one actor own and coordinate worker actors."""

import ray

from _ray_config import init_ray

init_ray()


@ray.remote(num_cpus=0.5)
class Worker:
    def process(self, value: int) -> int:
        return value * value


@ray.remote(num_cpus=0)
class Supervisor:
    def __init__(self, size: int) -> None:
        self.workers = [Worker.remote() for _ in range(size)]

    def map(self, values: list[int]) -> list[int]:
        refs = [
            self.workers[index % len(self.workers)].process.remote(value)
            for index, value in enumerate(values)
        ]
        return ray.get(refs)


supervisor = Supervisor.remote(size=2)
print("supervised results:", ray.get(supervisor.map.remote(list(range(6)))))
