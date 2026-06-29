"""Node affinity — run exactly one task on every live cluster node."""

import socket

import ray
from ray.util.scheduling_strategies import NodeAffinitySchedulingStrategy

from _cluster_config import init_cluster

nodes = init_cluster()


@ray.remote(num_cpus=0.01)
def identify() -> dict[str, str]:
    context = ray.get_runtime_context()
    return {
        "node_id": context.get_node_id(),
        "hostname": socket.gethostname(),
    }


refs = [
    identify.options(
        scheduling_strategy=NodeAffinitySchedulingStrategy(
            node_id=str(node["NodeID"]),
            soft=False,
        )
    ).remote()
    for node in nodes
]
results = ray.get(refs)

for result in results:
    print(result)

assert len({result["node_id"] for result in results}) == len(nodes)
