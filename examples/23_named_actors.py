"""Named and detached actors — discover durable services without a handle."""

import ray

from _ray_config import init_ray

init_ray(namespace="primer")


@ray.remote(num_cpus=0.5)
class Registry:
    def lookup(self, key: str) -> str:
        return {"api": "https://api.example.test"}[key]


registry = Registry.options(name="service-registry", lifetime="detached").remote()
try:
    discovered = ray.get_actor("service-registry")
    print("discovered result:", ray.get(discovered.lookup.remote("api")))
finally:
    ray.kill(registry)
