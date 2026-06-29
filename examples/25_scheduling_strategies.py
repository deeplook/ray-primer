"""Scheduling strategies — request spreading or affinity to a known node."""

import ray
from ray.util.scheduling_strategies import NodeAffinitySchedulingStrategy

from _ray_config import init_ray

init_ray()


@ray.remote(num_cpus=0.5)
def node_id() -> str:
    return ray.get_runtime_context().get_node_id()


local_node = ray.get_runtime_context().get_node_id()
spread = node_id.options(scheduling_strategy="SPREAD").remote()
pinned = node_id.options(
    scheduling_strategy=NodeAffinitySchedulingStrategy(node_id=local_node, soft=False)
).remote()

print("SPREAD selected:", ray.get(spread))
print("hard node affinity selected:", ray.get(pinned))
print("Both are the local node in this one-node tutorial cluster.")
