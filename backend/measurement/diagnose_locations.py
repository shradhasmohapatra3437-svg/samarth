import sys
import os
import pickle
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config import DATA_DIR, GENERATED_DIR

# Load graph
graph_path = os.path.join(DATA_DIR, "processed", "knowledge_graph.pkl")
with open(graph_path, "rb") as f:
    graph = pickle.load(f)

# All location nodes currently in graph
location_nodes = [n for n, d in graph.nodes(data=True) if d.get("node_type") == "location"]
print(f"=== LOCATION NODES IN GRAPH ({len(location_nodes)}) ===")
for n in location_nodes:
    print(f"  '{n}'")

# All location values in incident_reports.json
incident_path = os.path.join(GENERATED_DIR, "incident_reports.json")
with open(incident_path) as f:
    incidents = json.load(f)

locations_in_json = list(set(r.get("location", "") for r in incidents if r.get("location")))
print(f"\n=== LOCATION VALUES IN incident_reports.json ({len(locations_in_json)}) ===")
for loc in sorted(locations_in_json):
    in_graph = loc in graph.nodes
    status = "OK " if in_graph else "MISS"
    print(f"  [{status}] '{loc}'")

# Overall graph stats
print(f"\n=== GRAPH STATS ===")
print(f"Total nodes: {graph.number_of_nodes()}")
print(f"Total edges: {graph.number_of_edges()}")
node_types = {}
for n, d in graph.nodes(data=True):
    t = d.get("node_type", "unknown")
    node_types[t] = node_types.get(t, 0) + 1
for t, c in sorted(node_types.items()):
    print(f"  {t}: {c}")
