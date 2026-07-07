"""Cross-node objects — produce data on one node and consume it on another."""

import hashlib

import ray
from ray.util.scheduling_strategies import NodeAffinitySchedulingStrategy

from _cluster_config import init_cluster

nodes = init_cluster()
source_id = str(nodes[0]["NodeID"])
destination_id = str(nodes[1]["NodeID"])


def pinned(node_id: str) -> NodeAffinitySchedulingStrategy:
    return NodeAffinitySchedulingStrategy(node_id=node_id, soft=False)


@ray.remote(num_cpus=0.01)
def produce(size: int) -> dict[str, object]:
    payload = bytes(index % 251 for index in range(size))
    return {
        "payload": payload,
        "source_node": ray.get_runtime_context().get_node_id(),
    }


@ray.remote(num_cpus=0.01)
def consume(item: dict[str, object]) -> dict[str, object]:
    payload = item["payload"]
    assert isinstance(payload, bytes)
    return {
        "source_node": item["source_node"],
        "destination_node": ray.get_runtime_context().get_node_id(),
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


produced = produce.options(scheduling_strategy=pinned(source_id)).remote(
    4 * 1024 * 1024
)
result = ray.get(
    consume.options(scheduling_strategy=pinned(destination_id)).remote(produced)
)

print(result)
assert result["source_node"] != result["destination_node"]
