"""Shared validation for examples that require a real multi-node cluster."""

import os

import ray


def init_cluster(minimum_nodes: int = 2) -> list[dict[str, object]]:
    """Connect to RAY_ADDRESS and return the live nodes."""
    address = os.environ.get("RAY_ADDRESS")
    if not address:
        raise RuntimeError(
            "This example requires a running cluster. Use "
            "'uv run cluster/ray_cluster.py up', then run it through the "
            "cluster command."
        )
    ray.init(address=address, logging_level="ERROR", log_to_driver=False)
    nodes = [node for node in ray.nodes() if node["Alive"]]
    if len(nodes) < minimum_nodes:
        raise RuntimeError(
            f"Expected at least {minimum_nodes} live Ray nodes, found {len(nodes)}."
        )
    return nodes
