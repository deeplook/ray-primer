"""Cluster inventory — inspect every live Ray node and its resources."""

from _cluster_config import init_cluster

nodes = init_cluster()

for node in sorted(nodes, key=lambda item: str(item["NodeManagerAddress"])):
    print("node id:", node["NodeID"])
    print("address:", node["NodeManagerAddress"])
    print("resources:", node["Resources"])
    print()

print("live nodes:", len(nodes))
