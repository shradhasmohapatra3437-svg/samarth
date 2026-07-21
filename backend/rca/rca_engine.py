import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from groq import Groq
from knowledge_graph.graph_query import load_graph, get_graph_context
from rag.embedder import search_similar
from rca.realtime_simulator import get_simulated_conditions

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

graph = load_graph()


def extract_equipment_id(query: str) -> str:
    """
    Simple heuristic: find an equipment-tag-like token in the query
    (e.g., P-204, C-07) by checking against known graph equipment nodes.
    """
    query_upper = query.upper()
    for node, data in graph.nodes(data=True):
        if data.get("node_type") == "equipment" and node.upper() in query_upper:
            return node
    return None


def run_rca(query: str) -> dict:
    equipment_id = extract_equipment_id(query)

    if not equipment_id:
        return {
            "answer": "I couldn't identify a specific equipment ID in your question. Please mention an equipment tag (e.g., P-204) for RCA analysis.",
            "confidence": 0,
            "sources": [],
            "equipment_id": None
        }

    # 1. Graph-based failure history
    graph_facts = get_graph_context(query, graph)

     # 2. OEM manual guidance - retrieve DIRECTLY by source filename, not via semantic search,
    # since semantic ranking is unreliable for guaranteeing a specific known document is included
    from rag.embedder import get_chroma_client, get_or_create_collection

    client_db = get_chroma_client()
    collection = get_or_create_collection(client_db)
    oem_results = collection.get(where={"source": "oem_manual_centrifugal_pump.pdf"})

    manual_chunks = []
    if oem_results and oem_results.get("documents"):
        for doc, meta in zip(oem_results["documents"], oem_results["metadatas"]):
            manual_chunks.append({"text": doc, "metadata": meta})

    # 3. Historical work-order/incident context - search WITH the equipment ID for precision
    history_candidates = search_similar(f"{equipment_id} failure history", n_results=10)
    history_chunks = [c for c in history_candidates if "oem" not in c["metadata"].get("source", "").lower()][:5]

    # 4. Simulated real-time conditions
    conditions = get_simulated_conditions(equipment_id)

    # Build context for the LLM
    context_text = f"EQUIPMENT: {equipment_id}\n\n"

    if graph_facts:
        context_text += "HISTORICAL FAILURE PATTERN (from knowledge graph):\n"
        for fact in graph_facts:
            for edge in fact.get("edges", []):
                context_text += f"- {fact['entity']} --[{edge['relationship']}]--> {edge['neighbor']} (occurred {edge['weight']} times)\n"
        context_text += "\n"

    context_text += f"SIMULATED CURRENT OPERATING CONDITIONS ({conditions['note']}):\n"
    context_text += f"- Temperature: {conditions['temperature_c']}°C\n"
    context_text += f"- Vibration: {conditions['vibration_mm_s']} mm/s\n"
    context_text += f"- Pressure: {conditions['pressure_bar']} bar\n\n"

    if manual_chunks:
        context_text += "OEM MANUAL / TECHNICAL GUIDANCE:\n"
        for i, chunk in enumerate(manual_chunks):
            source = chunk["metadata"].get("source", "unknown")
            context_text += f"[OEM-{i+1}] (source: {source}) {chunk['text']}\n\n"
    else:
        context_text += "OEM MANUAL / TECHNICAL GUIDANCE: No OEM manual available for this equipment type (only centrifugal pump guidance exists in this system; this equipment is not a pump).\n\n"

    if history_chunks:
        context_text += "RELEVANT WORK ORDER / INCIDENT HISTORY:\n"
        for i, chunk in enumerate(history_chunks):
            source = chunk["metadata"].get("source", "unknown")
            context_text += f"[HIST-{i+1}] (source: {source}) {chunk['text']}\n\n"

    system_prompt = """You are a Maintenance Intelligence & Root Cause Analysis (RCA) agent for industrial equipment.
Using the historical failure pattern, simulated current operating conditions, OEM manual guidance, and work order
history provided, produce a structured RCA analysis with these sections:

1. LIKELY ROOT CAUSE(S) — based on historical pattern and OEM manual guidance, not speculation beyond the evidence
2. CURRENT RISK ASSESSMENT — whether simulated conditions suggest elevated risk, referencing OEM manual thresholds if relevant
3. RECOMMENDED ACTION — specific, actionable next step
4. CONFIDENCE — state clearly if data is insufficient for a confident conclusion

Be clear that simulated operating conditions are illustrative, not live sensor data, when discussing them.
Cite OEM manual sources using [OEM-1], [OEM-2] etc. and work order/incident sources using [HIST-1], [HIST-2] etc.
Do not fabricate root causes not supported by the given context. If no OEM manual content is available, say so
explicitly rather than citing work orders as if they were manual guidance."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {query}"}
        ],
        temperature=0.1,
        max_tokens=800
    )

    answer = response.choices[0].message.content

    # Calculate dynamic confidence score
    confidence_score = 100
    
    # 1. Deduct if using simulated telemetry instead of live sensors
    if conditions.get("is_simulated", False):
        confidence_score -= 15
        
    # 2. Deduct for missing regulatory texts
    governed_by = [k for k, v in dict(graph[equipment_id]).items() if v.get("relationship") == "GOVERNED_BY"]
    for reg in governed_by:
        # Check if the regulation has chunks in ChromaDB
        from compliance.compliance_engine import get_regulation_text
        chunks = get_regulation_text(reg)
        if not chunks:
            confidence_score -= 20 # Deduct 20% for unverified regulations

    # Clamp confidence between 10% and 95%
    final_confidence = max(10, min(95, confidence_score))

    all_sources = (
        [c["metadata"].get("source", "unknown") for c in manual_chunks] +
        [c["metadata"].get("source", "unknown") for c in history_chunks]
    )

    return {
        "answer": answer,
        "confidence": round(final_confidence, 1),
        "sources": all_sources,
        "equipment_id": equipment_id
    }


