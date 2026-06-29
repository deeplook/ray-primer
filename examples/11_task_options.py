"""Per-call options — override resources, names, and retry behavior."""

import ray

from _ray_config import init_ray

init_ray()


@ray.remote(num_cpus=1)
def describe(value: int) -> dict[str, object]:
    context = ray.get_runtime_context()
    return {
        "value": value,
        "task_name": context.get_task_name(),
        "resources": context.get_assigned_resources(),
    }


ref = describe.options(name="small-description", num_cpus=0.5).remote(42)
print(ray.get(ref))
