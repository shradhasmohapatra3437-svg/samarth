import os
import sys
import json
import pickle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import networkx as nx
from core.config import DATA_DIR


# Path to save the graph
GRAPH_PATH = os.path.join(DATA_DIR, "processed", "knowledge_graph.pkl")


def create_graph() -> nx.DiGraph:
    """
    Create a directed graph.
    Directed means edges have direction:
    P-204 --[FAILED WITH]--> Seal Failure
    not just P-204 -- Seal Failure
    """
    return nx.DiGraph()


def add_entities_to_graph(graph: nx.DiGraph, 
                           extraction_result: dict) -> nx.DiGraph:
    """
    Add extracted entities as nodes and create
    relationships as edges.
    
    Node types:
    - equipment: P-204, C-07
    - person: Raghunath Panda
    - regulation: OISD-STD-171
    - failure_mode: Seal Failure
    - location: Zone 3
    """
    entities = extraction_result['entities']
    source = extraction_result['source']
    chunk_id = extraction_result['chunk_id']
    
    equipment_list = entities.get('equipment_tags', [])
    personnel_list = entities.get('personnel', [])
    regulations_list = entities.get('regulations', [])
    failure_modes_list = entities.get('failure_modes', [])
    locations_list = entities.get('locations', [])
    actions_list = entities.get('actions', [])
    
    # Add equipment nodes
    for equip in equipment_list:
        if equip and len(equip) > 1:
            graph.add_node(
                equip,
                node_type="equipment",
                mentions=graph.nodes[equip].get('mentions', 0) + 1
                if equip in graph.nodes else 1
            )
    
    # Add personnel nodes
    for person in personnel_list:
        if person and len(person) > 2:
            graph.add_node(
                person,
                node_type="person",
                mentions=graph.nodes[person].get('mentions', 0) + 1
                if person in graph.nodes else 1
            )
    
    # Add regulation nodes
    for reg in regulations_list:
        if reg and len(reg) > 2:
            graph.add_node(
                reg,
                node_type="regulation",
                mentions=graph.nodes[reg].get('mentions', 0) + 1
                if reg in graph.nodes else 1
            )
    
    # Add failure mode nodes
    for failure in failure_modes_list:
        if failure and len(failure) > 2:
            graph.add_node(
                failure,
                node_type="failure_mode",
                mentions=graph.nodes[failure].get('mentions', 0) + 1
                if failure in graph.nodes else 1
            )
    
    # Add location nodes
    for location in locations_list:
        if location and len(location) > 2:
            graph.add_node(
                location,
                node_type="location",
                mentions=graph.nodes[location].get('mentions', 0) + 1
                if location in graph.nodes else 1
            )
    
    # Create relationships (edges)
    
    # Equipment → Failed With → Failure Mode
    for equip in equipment_list:
        for failure in failure_modes_list:
            if equip and failure:
                if graph.has_edge(equip, failure):
                    graph[equip][failure]['weight'] += 1
                    graph[equip][failure]['sources'].append(chunk_id)
                else:
                    graph.add_edge(
                        equip, failure,
                        relationship="FAILED_WITH",
                        weight=1,
                        sources=[chunk_id]
                    )
    
    # Equipment → Repaired By → Person
    for equip in equipment_list:
        for person in personnel_list:
            if equip and person:
                if graph.has_edge(equip, person):
                    graph[equip][person]['weight'] += 1
                else:
                    graph.add_edge(
                        equip, person,
                        relationship="REPAIRED_BY",
                        weight=1,
                        sources=[chunk_id]
                    )
    
    # Equipment → Governed By → Regulation
    for equip in equipment_list:
        for reg in regulations_list:
            if equip and reg:
                if graph.has_edge(equip, reg):
                    graph[equip][reg]['weight'] += 1
                else:
                    graph.add_edge(
                        equip, reg,
                        relationship="GOVERNED_BY",
                        weight=1,
                        sources=[chunk_id]
                    )
    
    # Equipment → Located In → Location
    for equip in equipment_list:
        for location in locations_list:
            if equip and location:
                if graph.has_edge(equip, location):
                    graph[equip][location]['weight'] += 1
                else:
                    graph.add_edge(
                        equip, location,
                        relationship="LOCATED_IN",
                        weight=1,
                        sources=[chunk_id]
                    )
    
    # Person → Worked On → Equipment
    for person in personnel_list:
        for equip in equipment_list:
            if person and equip:
                if graph.has_edge(person, equip):
                    graph[person][equip]['weight'] += 1
                else:
                    graph.add_edge(
                        person, equip,
                        relationship="WORKED_ON",
                        weight=1,
                        sources=[chunk_id]
                    )
    
    return graph


def save_graph(graph: nx.DiGraph):
    """Save graph to disk using pickle."""
    os.makedirs(os.path.dirname(GRAPH_PATH), exist_ok=True)
    with open(GRAPH_PATH, 'wb') as f:
        pickle.dump(graph, f)
    print(f"[OK] Graph saved to {GRAPH_PATH}")


def load_graph() -> nx.DiGraph:
    """Load graph from disk."""
    if os.path.exists(GRAPH_PATH):
        with open(GRAPH_PATH, 'rb') as f:
            graph = pickle.load(f)
        print(f"[OK] Graph loaded: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
        return graph
    else:
        print("No existing graph found. Creating new one.")
        return create_graph()


def get_equipment_info(graph: nx.DiGraph, equipment_tag: str) -> dict:
    """
    Query the graph for everything known about an equipment.
    This is what powers the maintenance intelligence module.
    """
    if equipment_tag not in graph.nodes:
        return {"error": f"{equipment_tag} not found in knowledge graph"}
    
    info = {
        "equipment": equipment_tag,
        "failures": [],
        "technicians": [],
        "regulations": [],
        "locations": [],
        "failure_count": 0
    }
    
    # Get all edges from this equipment node
    for neighbor in graph.neighbors(equipment_tag):
        edge_data = graph[equipment_tag][neighbor]
        relationship = edge_data.get('relationship', '')
        weight = edge_data.get('weight', 1)
        
        if relationship == "FAILED_WITH":
            info["failures"].append({
                "failure_mode": neighbor,
                "occurrences": weight
            })
            info["failure_count"] += weight
            
        elif relationship == "REPAIRED_BY":
            info["technicians"].append({
                "name": neighbor,
                "times_repaired": weight
            })
            
        elif relationship == "GOVERNED_BY":
            info["regulations"].append(neighbor)
            
        elif relationship == "LOCATED_IN":
            info["locations"].append(neighbor)
    
    return info


def get_person_expertise(graph: nx.DiGraph, person_name: str) -> dict:
    """
    Query graph for a person's expertise based on what they've worked on.
    Powers the 'who knows what' feature.
    """
    if person_name not in graph.nodes:
        return {"error": f"{person_name} not found in knowledge graph"}
    
    expertise = {
        "person": person_name,
        "equipment_worked_on": [],
        "total_jobs": 0
    }
    
    for neighbor in graph.neighbors(person_name):
        edge_data = graph[person_name][neighbor]
        relationship = edge_data.get('relationship', '')
        weight = edge_data.get('weight', 1)
        
        if relationship == "WORKED_ON":
            expertise["equipment_worked_on"].append({
                "equipment": neighbor,
                "times": weight
            })
            expertise["total_jobs"] += weight
    
    return expertise


def print_graph_stats(graph: nx.DiGraph):
    """Print summary statistics about the graph."""
    print(f"\n{'='*40}")
    print(f"Knowledge Graph Statistics")
    print(f"{'='*40}")
    print(f"Total nodes: {graph.number_of_nodes()}")
    print(f"Total edges: {graph.number_of_edges()}")
    
    # Count by node type
    node_types = {}
    for node, data in graph.nodes(data=True):
        ntype = data.get('node_type', 'unknown')
        node_types[ntype] = node_types.get(ntype, 0) + 1
    
    print(f"\nNodes by type:")
    for ntype, count in node_types.items():
        print(f"  {ntype}: {count}")
    
    # Most mentioned equipment
    equipment_nodes = [
        (node, data.get('mentions', 0))
        for node, data in graph.nodes(data=True)
        if data.get('node_type') == 'equipment'
    ]
    equipment_nodes.sort(key=lambda x: x[1], reverse=True)
    
    print(f"\nTop equipment by mentions:")
    for equip, mentions in equipment_nodes[:5]:
        print(f"  {equip}: {mentions} mentions")


if __name__ == "__main__":
    from knowledge_graph.entity_extractor import extract_entities_batch
    from ingestion.json_parser import process_all_json_files
    from core.config import GENERATED_DIR
    
    print("Building Knowledge Graph...")
    
    # Load operational data chunks
    print("\nLoading operational data...")
    chunks = process_all_json_files(GENERATED_DIR)
    
    # Extract entities (limit to 30 chunks to save API calls)
    print("\nExtracting entities...")
    extraction_results = extract_entities_batch(chunks, max_chunks=len(chunks))
    # Build graph
    print("\nBuilding graph...")
    graph = create_graph()
    
    for result in extraction_results:
        graph = add_entities_to_graph(graph, result)
    
    # Print stats
    print_graph_stats(graph)
    
    # Save graph
    save_graph(graph)
    
    # Test queries
    print("\n" + "="*40)
    print("Testing Graph Queries")
    print("="*40)
    
    # Test equipment query
    print("\nEquipment info for P-204:")
    info = get_equipment_info(graph, "P-204")
    print(json.dumps(info, indent=2))
    
    # Test person query
    print("\nExpertise of Raghunath Panda:")
    expertise = get_person_expertise(graph, "Raghunath Panda")
    print(json.dumps(expertise, indent=2))
    