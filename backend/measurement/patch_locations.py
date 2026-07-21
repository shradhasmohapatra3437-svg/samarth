"""
Patch script: adds compound location nodes (e.g. "Zone 1 - Furnace Area")
to the knowledge graph, alongside the existing split nodes.
These compound names come directly from incident_reports.json 'location' field.
This does NOT remove existing nodes — it adds aliases so both forms work.
"""
import sys
import os
import pickle
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config import DATA_DIR, GENERATED_DIR

GRAPH_PATH = os.path.join(DATA_DIR, "processed", "knowledge_graph.pkl")

# Load graph
with open(GRAPH_PATH, "rb") as f:
    graph = pickle.load(f)

print(f"Before patch: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")

# Load incident reports to get all compound location strings
incident_path = os.path.join(GENERATED_DIR, "incident_reports.json")
with open(incident_path) as f:
    incidents = json.load(f)

compound_locations = list(set(r.get("location", "") for r in incidents if r.get("location")))

added = 0
already_present = 0
for loc in compound_locations:
    if loc in graph.nodes:
        already_present += 1
        continue
    # Add compound node with location type
    graph.add_node(loc, node_type="location", mentions=1, source="incident_reports_patch")

    # Also link it: if "Zone X" and "Area Name" both exist as nodes,
    # add PART_OF edges from compound to its parts (informational only)
    parts = [p.strip() for p in loc.split(" - ") if p.strip()]
    for part in parts:
        if part in graph.nodes and part != loc:
            if not graph.has_edge(loc, part):
                graph.add_edge(loc, part, relationship="INCLUDES_ZONE", weight=1, sources=["incident_reports_patch"])

    added += 1
    print(f"  Added: '{loc}'")

print(f"\nPatch complete: added {added} compound location nodes ({already_present} already present)")
print(f"After patch: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")

# Save patched graph
with open(GRAPH_PATH, "wb") as f:
    pickle.dump(graph, f)
print(f"Graph saved to {GRAPH_PATH}")
