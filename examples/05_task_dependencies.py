"""Task dependencies — compose a dataflow graph without blocking the driver."""

import ray

from _ray_config import init_ray

init_ray()


@ray.remote
def add(left: int, right: int) -> int:
    return left + right


@ray.remote
def double(value: int) -> int:
    return value * 2


subtotal = add.remote(20, 22)
result = double.remote(subtotal)
print("subtotal ref:", subtotal)
print("result:", ray.get(result))
print("Ray resolves top-level ObjectRef arguments on the worker.")
