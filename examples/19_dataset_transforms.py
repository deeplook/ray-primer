"""Dataset transforms — lazily map and filter distributed records."""

import ray

from _ray_config import init_ray

init_ray()

dataset = ray.data.range(20, override_num_blocks=2)
transformed = (
    dataset.map(lambda row: {"id": row["id"], "square": row["id"] ** 2})
    .filter(lambda row: row["square"] % 2 == 0)
)

print("Transforms build a lazy execution plan.")
print("plan:", transformed)
print("first five:", transformed.take(5))
