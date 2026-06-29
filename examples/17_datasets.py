"""Ray Datasets — create a distributed collection from Python objects."""

import ray

from _ray_config import init_ray

init_ray()

records = [
    {"name": "Alice", "age": 25},
    {"name": "Bob", "age": 30},
    {"name": "Carol", "age": 35},
]
dataset = ray.data.from_items(records, override_num_blocks=2)

print("schema:", dataset.schema())
print("rows:", dataset.take_all())
print("blocks:", dataset.num_blocks())
