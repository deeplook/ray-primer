"""Runtime context — inspect where a task runs and identify its execution."""

import ray

from _ray_config import init_ray

init_ray()


@ray.remote
def where_am_i() -> dict[str, str]:
    context = ray.get_runtime_context()
    return {
        "job_id": context.get_job_id(),
        "node_id": context.get_node_id(),
        "task_id": context.get_task_id(),
        "worker_id": context.get_worker_id(),
    }


for key, value in ray.get(where_am_i.remote()).items():
    print(f"{key}: {value}")
