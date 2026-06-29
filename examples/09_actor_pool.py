"""Multiple actors — state is serial per actor, parallel across actors."""

import time

import ray

from _ray_config import init_ray

init_ray()


@ray.remote(num_cpus=1)
class Worker:
    def __init__(self, name: str) -> None:
        self.name = name

    def process(self, value: int) -> tuple[str, int]:
        time.sleep(0.1)
        return self.name, value * 2


workers = [Worker.remote("A"), Worker.remote("B")]
refs = [workers[index % 2].process.remote(index) for index in range(6)]
print(ray.get(refs))
