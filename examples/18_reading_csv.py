"""Reading CSV — load tabular files as a distributed Ray Dataset."""

from pathlib import Path

import ray

from _ray_config import init_ray

init_ray()

root_dir = Path(__file__).resolve().parent.parent
tips = ray.data.read_csv(root_dir / "data" / "tips.csv", override_num_blocks=2)

print("schema:", tips.schema())
print("count:", tips.count())
print("first three:")
tips.show(limit=3)
