import pickle
import re

def load_graph(path="../data/processed/knowledge_graph.pkl"):
    with open(path, "rb") as f:
        return pickle.load(f)

def find_entities_in_query(query, graph):
    """Naive match: check query text against node names in the graph."""
    query_upper = query.upper()
    matched = []
    for node in graph.nodes:
        if str(node).upper() in query_upper:
            matched.append(node)
    return matched

def get_graph_context(query, graph):
    """Return structured facts for any equipment/person mentioned in the query,
    including relationship type and occurrence weight."""
    entities = find_entities_in_query(query, graph)
    facts = []
    for entity in entities:
        node_data = graph.nodes[entity]
        node_type = node_data.get("type", "unknown")
        edges = []
        for neighbor, edge_data in graph[entity].items():
            edges.append({
                "neighbor": neighbor,
                "relationship": edge_data.get("relationship", "RELATED_TO"),
                "weight": edge_data.get("weight", 1)
            })
        facts.append({
            "entity": entity,
            "type": node_type,
            "edges": edges
        })
    return facts
