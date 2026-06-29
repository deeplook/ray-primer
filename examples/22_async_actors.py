"""Async actors — overlap I/O-bound methods within one stateful actor."""

import asyncio

import ray

from _ray_config import init_ray

init_ray()


@ray.remote(num_cpus=1, max_concurrency=3)
class AsyncWorker:
    def __init__(self) -> None:
        self.active = 0
        self.peak = 0

    async def fetch(self, value: int) -> int:
        self.active += 1
        self.peak = max(self.peak, self.active)
        await asyncio.sleep(0.1)
        self.active -= 1
        return value * 2

    def peak_concurrency(self) -> int:
        return self.peak


worker = AsyncWorker.remote()
print("results:", ray.get([worker.fetch.remote(value) for value in range(3)]))
print("peak concurrent methods:", ray.get(worker.peak_concurrency.remote()))
