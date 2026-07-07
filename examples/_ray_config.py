"""Shared Ray configuration for local and existing-cluster tutorials."""

import os
import warnings

import ray


def init_ray(**overrides: object) -> object:
    """Connect through RAY_ADDRESS, or start a two-CPU local Ray instance."""
    os.environ.setdefault("RAY_ACCEL_ENV_VAR_OVERRIDE_ON_ZERO", "0")
    warnings.filterwarnings(
        "ignore",
        message="Tip: In future versions of Ray.*accelerator visible devices",
        category=FutureWarning,
    )
    common_options: dict[str, object] = {
        "logging_level": "ERROR",
        "log_to_driver": False,
    }
    address = os.environ.get("RAY_ADDRESS")
    if address:
        local_only = {"num_cpus", "num_gpus", "resources", "object_store_memory"}
        invalid = sorted(local_only.intersection(overrides))
        if invalid:
            names = ", ".join(invalid)
            raise ValueError(
                f"Cannot set {names} while connecting through RAY_ADDRESS. "
                "Configure those resources with 'ray start' on each node."
            )
        common_options.update(overrides)
        return ray.init(address=address, **common_options)  # type: ignore[arg-type]

    local_options: dict[str, object] = {
        **common_options,
        "num_cpus": 2,
        "include_dashboard": False,
        **overrides,
    }
    return ray.init(**local_options)  # type: ignore[arg-type]
