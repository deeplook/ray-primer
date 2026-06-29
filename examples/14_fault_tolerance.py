"""Fault tolerance — retry selected application errors automatically."""

from pathlib import Path
from tempfile import TemporaryDirectory

import ray

from _ray_config import init_ray

init_ray()


@ray.remote(max_retries=1, retry_exceptions=True)
def flaky(marker: str) -> str:
    path = Path(marker)
    if not path.exists():
        path.touch()
        raise RuntimeError("transient failure")
    return "succeeded on retry"


with TemporaryDirectory() as directory:
    print(ray.get(flaky.remote(str(Path(directory) / "attempted"))))
