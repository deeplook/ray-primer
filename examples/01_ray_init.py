"""Ray initialization — start a local cluster and inspect its resources."""

import ray

from _ray_config import init_ray

context = init_ray()

print("Ray version:", ray.__version__)
print("dashboard:", context.dashboard_url or "disabled")
print("cluster resources:", ray.cluster_resources())
print("available resources:", ray.available_resources())
