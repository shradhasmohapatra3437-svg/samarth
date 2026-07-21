import pickle
from knowledge_graph.graph_builder import GRAPH_PATH

with open(GRAPH_PATH, 'rb') as f:
    graph = pickle.load(f)

canonical = 'Visakhapatnam Steel Plant'
duplicate = 'Vizag Steel Plant'

if duplicate in graph.nodes:
    canonical_mentions = graph.nodes[canonical].get('mentions', 0)
    duplicate_mentions = graph.nodes[duplicate].get('mentions', 0)
    graph.nodes[canonical]['mentions'] = canonical_mentions + duplicate_mentions

    for neighbor in list(graph.neighbors(duplicate)):
        edge_data = graph.get_edge_data(duplicate, neighbor)
        if not graph.has_edge(canonical, neighbor):
            graph.add_edge(canonical, neighbor, **edge_data)

    for predecessor in list(graph.predecessors(duplicate)):
        edge_data = graph.get_edge_data(predecessor, duplicate)
        if not graph.has_edge(predecessor, canonical):
            graph.add_edge(predecessor, canonical, **edge_data)

    graph.remove_node(duplicate)
    new_count = graph.nodes[canonical]['mentions']
    print(f"Merged '{duplicate}' into '{canonical}'. New mention count: {new_count}")
else:
    print(f"'{duplicate}' not found in graph — nothing to merge.")

with open(GRAPH_PATH, 'wb') as f:
    pickle.dump(graph, f)
print("Graph saved.")
