"""Batch transforms — vectorize Dataset work with pandas batches."""

import pandas as pd
import ray

from _ray_config import init_ray

init_ray()


def add_total(batch: pd.DataFrame) -> pd.DataFrame:
    batch = batch.copy()
    batch["total"] = batch["price"] * batch["quantity"]
    return batch


orders = ray.data.from_items(
    [
        {"product": "Widget", "price": 9.99, "quantity": 3},
        {"product": "Gadget", "price": 24.99, "quantity": 2},
        {"product": "Widget", "price": 9.99, "quantity": 1},
    ],
    override_num_blocks=2,
)
totals = orders.map_batches(add_total, batch_format="pandas")
print(totals.take_all())
