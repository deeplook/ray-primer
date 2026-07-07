"""Ray Train — execute one training loop across data-parallel workers."""

import os
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ["RAY_TRAIN_V2_ENABLED"] = "1"

import ray
from ray import train
from ray.train import Checkpoint, RunConfig, ScalingConfig
from ray.train.v2.api.data_parallel_trainer import DataParallelTrainer

from _ray_config import init_ray

init_ray()


def train_loop() -> None:
    context = train.get_context()
    shard = train.get_dataset_shard("train")
    row_count = sum(len(batch["id"]) for batch in shard.iter_batches(batch_size=4))
    metrics = {
        "world_rank": context.get_world_rank(),
        "world_size": context.get_world_size(),
        "rows_seen": row_count,
    }
    with TemporaryDirectory() as checkpoint_dir:
        Path(checkpoint_dir, "worker.txt").write_text(str(metrics))
        train.report(metrics, checkpoint=Checkpoint.from_directory(checkpoint_dir))


dataset = ray.data.range(8, override_num_blocks=2)
with TemporaryDirectory() as storage:
    trainer = DataParallelTrainer(
        train_loop_per_worker=train_loop,
        scaling_config=ScalingConfig(
            num_workers=2,
            use_gpu=False,
            resources_per_worker={"CPU": 0.5},
        ),
        datasets={"train": dataset},
        run_config=RunConfig(name="primer-train", storage_path=storage),
    )
    result = trainer.fit()
    print("reported metrics:", result.metrics)
