"""Session-scoped Ray cluster shared across all example tests."""

import logging
import os
from collections.abc import Generator

import pytest
import ray


@pytest.fixture(scope="session")
def ray_cluster() -> Generator[str, None, None]:
    ctx = ray.init(
        num_cpus=4,
        include_dashboard=False,
        logging_level=logging.ERROR,
        log_to_driver=False,
    )
    address = ctx.address_info["address"]  # type: ignore[attr-defined]
    os.environ["RAY_ADDRESS"] = address
    yield address
    ray.shutdown()
    os.environ.pop("RAY_ADDRESS", None)
