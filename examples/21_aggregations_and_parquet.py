"""Aggregations and Parquet — summarize data, then persist it columnarly."""

import shutil
from pathlib import Path

import ray
from ray.data.aggregate import Count, Mean, Sum

from _ray_config import init_ray

init_ray()

root_dir = Path(__file__).resolve().parent.parent
tips = ray.data.read_csv(root_dir / "data" / "tips.csv", override_num_blocks=2)

summary = tips.groupby("day").aggregate(
    Count(),
    Mean("tip"),
    Sum("total_bill"),
)
print("by day:", sorted(summary.take_all(), key=lambda row: row["day"]))

out_path = root_dir / "out" / "tips_by_day"
shutil.rmtree(out_path, ignore_errors=True)
summary.write_parquet(out_path)
print("round trip:", ray.data.read_parquet(out_path).count(), "rows")
