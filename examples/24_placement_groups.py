"""Placement groups — reserve resources atomically for related work."""

import ray
from ray.util.placement_group import placement_group, remove_placement_group
from ray.util.scheduling_strategies import PlacementGroupSchedulingStrategy

from _ray_config import init_ray

init_ray()


@ray.remote(num_cpus=0.5)
def bundle_info(label: str) -> tuple[str, dict[str, float]]:
    return label, ray.get_runtime_context().get_assigned_resources()


group = placement_group([{"CPU": 0.5}, {"CPU": 0.5}], strategy="PACK")
ray.get(group.ready())
try:
    refs = [
        bundle_info.options(
            scheduling_strategy=PlacementGroupSchedulingStrategy(
                placement_group=group,
                placement_group_bundle_index=index,
            )
        ).remote(f"bundle-{index}")
        for index in range(2)
    ]
    print("reserved bundles:", ray.get(refs))
finally:
    remove_placement_group(group)
