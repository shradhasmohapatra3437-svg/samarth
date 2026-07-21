"""
Formal ontology definition for the Samarth knowledge graph.
This is the single source of truth for entity types and valid relationships.
Any code that creates graph nodes/edges should reference this file,
rather than hardcoding type strings independently.
"""

# Valid entity (node) types
ENTITY_TYPES = {
    "equipment": "Physical plant equipment (pumps, compressors, valves, tanks, etc.)",
    "person": "Named individuals (technicians, supervisors, officials)",
    "regulation": "Regulatory standards or legal references (OISD, Factory Act sections, etc.)",
    "failure_mode": "Types of equipment failure or malfunction",
    "location": "Physical locations (zones, plants, facility names)",
}

# Valid relationship types and which entity type pairs they can connect
# Format: relationship_name: (source_type, target_type, description)
RELATIONSHIP_TYPES = {
    "FAILED_WITH": ("equipment", "failure_mode", "Equipment experienced this failure mode"),
    "REPAIRED_BY": ("equipment", "person", "Person repaired/serviced this equipment"),
    "GOVERNED_BY": ("equipment", "regulation", "Equipment/procedure governed by this regulation"),
    "LOCATED_AT": ("equipment", "location", "Equipment is physically located here"),
    "WORKED_AT": ("person", "location", "Person works/worked at this location"),
    "OCCURRED_AT": ("failure_mode", "location", "This failure occurred at this location"),
}


def validate_relationship(rel_type: str, source_node_type: str, target_node_type: str) -> bool:
    """
    Check if a given relationship type is valid between two entity types,
    according to the defined ontology.
    """
    if rel_type not in RELATIONSHIP_TYPES:
        return False

    expected_source, expected_target, _ = RELATIONSHIP_TYPES[rel_type]
    return source_node_type == expected_source and target_node_type == expected_target


def is_valid_entity_type(entity_type: str) -> bool:
    return entity_type in ENTITY_TYPES