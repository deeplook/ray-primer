"""Logical resources — express scheduling requirements for tasks."""

import ray

from _ray_config import init_ray

init_ray(resources={"accelerator": 1})


@ray.remote(num_cpus=0.5, resources={"accelerator": 1})
def inspect_resources() -> dict[str, float]:
    return ray.get_runtime_context().get_assigned_resources()


print("cluster:", ray.cluster_resources())
print("assigned to task:", ray.get(inspect_resources.remote()))
print("Resources are logical scheduling capacity, not physical isolation.")
