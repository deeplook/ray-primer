"""Strict spread — reserve bundles on distinct nodes as one atomic group."""

import ray
from ray.util.placement_group import placement_group, remove_placement_group
from ray.util.scheduling_strategies import PlacementGroupSchedulingStrategy

from _cluster_config import init_cluster

init_cluster()


@ray.remote(num_cpus=0.1)
def location() -> str:
    return ray.get_runtime_context().get_node_id()


group = placement_group([{"CPU": 0.1}, {"CPU": 0.1}], strategy="STRICT_SPREAD")
ray.get(group.ready(), timeout=30)

try:
    refs = [
        location.options(
            scheduling_strategy=PlacementGroupSchedulingStrategy(
                placement_group=group,
                placement_group_bundle_index=index,
            )
        ).remote()
        for index in range(2)
    ]
    node_ids = ray.get(refs)
    print("bundle node IDs:", node_ids)
    assert len(set(node_ids)) == 2
finally:
    remove_placement_group(group)
