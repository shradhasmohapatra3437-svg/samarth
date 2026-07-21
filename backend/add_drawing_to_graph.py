import pickle
from ingestion.pid_parser import extract_labels_from_drawing
from knowledge_graph.entity_extractor import extract_entities_from_chunk
from knowledge_graph.graph_builder import add_entities_to_graph, GRAPH_PATH

with open(GRAPH_PATH, 'rb') as f:
    graph = pickle.load(f)

print(f"Graph loaded. Current nodes: {len(graph.nodes)}")

filepath = "../data/regulatory/test_pid.svg"
chunk_id = "test_pid_drawing"

labels = extract_labels_from_drawing(filepath)
text = "\n".join(labels)

print(f"Extracting entities from {chunk_id}...")
entities = extract_entities_from_chunk(text, {"source": chunk_id})
print("Extracted:", entities)

extraction_result = {
    "entities": entities,
    "source": chunk_id,
    "chunk_id": chunk_id
}

graph = add_entities_to_graph(graph, extraction_result)

print(f"New total nodes: {len(graph.nodes)}")

with open(GRAPH_PATH, 'wb') as f:
    pickle.dump(graph, f)
print("Graph saved.")
