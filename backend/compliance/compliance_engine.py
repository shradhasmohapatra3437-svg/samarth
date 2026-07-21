import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from groq import Groq
from knowledge_graph.graph_query import load_graph
from rag.embedder import get_chroma_client, get_or_create_collection
from rca.realtime_simulator import get_simulated_conditions
from rca.priority_scorer import score_equipment_priority

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

graph = load_graph()

REAL_REGULATION_SOURCES = {
    "factories act": "factories_act_1948.pdf",
    "factory act": "factories_act_1948.pdf",
    "peso": "peso_rules.pdf",
    "cpcb": "cpcb_environmental_norms.pdf",
    "environmental norms": "cpcb_environmental_norms.pdf",
    "oisd-std-105": "oisd_std_105.pdf",
    "oisd-std-116": "oisd_std_116.pdf",
    "oisd-std-137": "oisd_std_137.pdf",
}


def extract_equipment_id(query: str) -> str:
    query_upper = query.upper()
    for node, data in graph.nodes(data=True):
        if data.get("node_type") == "equipment" and node.upper() in query_upper:
            return node
    return None


def extract_regulation_reference(query: str) -> str:
    """
    Detect if the query directly references a known REAL regulation by name,
    for cases where no equipment ID is mentioned (e.g., asking about Factory Act
    directly, rather than asking about specific equipment).
    """
    query_lower = query.lower()
    for key, filename in REAL_REGULATION_SOURCES.items():
        if key in query_lower:
            return filename
    return None


def get_governing_regulations(equipment_id: str) -> list:
    """
    Deterministic: pull the actual regulation IDs this equipment is
    GOVERNED_BY, directly from the graph edges (no guessing).
    """
    if equipment_id not in graph.nodes:
        return []
    edges = dict(graph[equipment_id])
    return [k for k, v in edges.items() if v.get("relationship") == "GOVERNED_BY"]


def get_regulation_text(regulation_id: str, topic_hint: str = "") -> list:
    """
    Guaranteed retrieval: fetch chunks whose source matches this regulation ID,
    ONLY from actual regulatory PDF sources. Uses semantic re-ranking within
    the matched document so genuinely substantive technical content is returned,
    not just whatever chunks happen to come first in document order.
    """
    client_db = get_chroma_client()
    collection = get_or_create_collection(client_db)

    all_docs = collection.get()
    matches = []
    reg_id_normalized = regulation_id.lower().replace("-", "_").replace(" ", "_")

    for doc, meta in zip(all_docs["documents"], all_docs["metadatas"]):
        source = meta.get("source", "").lower()
        if not source.endswith(".pdf"):
            continue
        source_normalized = source.replace("-", "_").replace(" ", "_")
        if reg_id_normalized in source_normalized:
            matches.append({"text": doc, "metadata": meta})

    if not matches:
        return []

    from rag.embedder import embedding_model
    import numpy as np

    query_text = topic_hint if topic_hint else "inspection requirement frequency shall be"
    query_embedding = embedding_model.encode([query_text])[0]

    scored = []
    for m in matches:
        chunk_embedding = embedding_model.encode([m["text"]])[0]
        similarity = np.dot(query_embedding, chunk_embedding) / (
            np.linalg.norm(query_embedding) * np.linalg.norm(chunk_embedding)
        )
        scored.append((similarity, m))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored[:3]]


def run_regulation_first_check(query: str, source_filename: str) -> dict:
    """
    For regulation-first questions with no equipment anchor (e.g., asking about
    Factory Act, PESO, or CPCB directly, since no equipment in the current
    graph is linked to these regulations). Retrieves the actual regulation
    text directly and reasons about it in isolation, without failure history
    or simulated conditions, since there's no specific equipment in scope.
    """
    client_db = get_chroma_client()
    collection = get_or_create_collection(client_db)
    all_docs = collection.get()

    matches = []
    for doc, meta in zip(all_docs["documents"], all_docs["metadatas"]):
        if meta.get("source", "").lower() == source_filename.lower():
            matches.append({"text": doc, "metadata": meta})

    if not matches:
        return {
            "answer": f"No content found for {source_filename} in the document corpus.",
            "confidence": 0,
            "sources": [],
            "equipment_id": None
        }

    from rag.embedder import embedding_model
    import numpy as np
    query_embedding = embedding_model.encode([query])[0]
    scored = []
    for m in matches:
        chunk_embedding = embedding_model.encode([m["text"]])[0]
        similarity = np.dot(query_embedding, chunk_embedding) / (
            np.linalg.norm(query_embedding) * np.linalg.norm(chunk_embedding)
        )
        scored.append((similarity, m))
    scored.sort(key=lambda x: x[0], reverse=True)
    top_chunks = [m for _, m in scored[:4]]

    context_text = f"REGULATION: {source_filename}\n\n"
    for i, chunk in enumerate(top_chunks):
        context_text += f"[REG-{i+1}] {chunk['text'][:900]}\n\n"

    system_prompt = """You are a Quality & Regulatory Compliance Intelligence agent.
Answer the question using ONLY the retrieved regulation text provided. Cite using [REG-1], [REG-2] etc.
If the retrieved text does not contain the answer, say so explicitly rather than guessing. Do not fabricate
requirements not present in the given text."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {query}"}
        ],
        temperature=0.1,
        max_tokens=700
    )

    return {
        "answer": response.choices[0].message.content,
        "confidence": 50,
        "sources": [source_filename] * len(top_chunks),
        "equipment_id": None
    }


def test_conflict_detection_mechanism(equipment_id: str, regulation_ids: list, query: str) -> dict:
    """
    DIAGNOSTIC/TEST FUNCTION — explicitly bypasses graph GOVERNED_BY edges to
    directly test cross-regulatory conflict detection with real regulation text,
    for cases where no real equipment in the current dataset happens to be
    governed by multiple real (downloaded) regulations simultaneously.
    This does NOT represent a real finding about actual equipment — it verifies
    the reasoning mechanism only.
    """
    priority_data = score_equipment_priority(equipment_id)
    conditions = get_simulated_conditions(equipment_id)

    context_text = f"EQUIPMENT: {equipment_id} (NOTE: regulations below are being tested together as a mechanism check, not necessarily both real GOVERNED_BY relationships for this equipment)\n\n"
    context_text += f"FAILURE HISTORY SIGNAL: {priority_data.get('total_failures', 'unknown')} recorded failures\n\n"

    all_sources = []
    reg_counter = 1
    for reg in regulation_ids:
        reg_chunks = get_regulation_text(reg, topic_hint=query)
        for chunk in reg_chunks:
            source = chunk["metadata"].get("source", "unknown")
            context_text += f"[REG-{reg_counter}] (regulation: {reg}, source: {source}) {chunk['text'][:800]}\n\n"
            all_sources.append(source)
            reg_counter += 1

    system_prompt = """You are testing cross-regulatory conflict detection. Given text from two or more
    real regulations, identify whether their stated requirements for similar equipment/processes appear
    to conflict, overlap redundantly, or are complementary. Be specific about what in each regulation's
    text supports your conclusion. If no conflict is evident, say so explicitly and explain why."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {query}"}
        ],
        temperature=0.1,
        max_tokens=700
    )

    return {"answer": response.choices[0].message.content, "sources": all_sources}


def run_compliance_check(query: str) -> dict:
    equipment_id = extract_equipment_id(query)

    if not equipment_id:
        regulation_ref = extract_regulation_reference(query)
        if regulation_ref:
            return run_regulation_first_check(query, regulation_ref)
        return {
            "answer": "I couldn't identify a specific equipment ID or known regulation in your question. Please mention an equipment tag (e.g., P-204) or a regulation name (e.g., Factory Act, PESO, CPCB).",
            "confidence": 0,
            "sources": [],
            "equipment_id": None
        }

    regulations = get_governing_regulations(equipment_id)
    priority_data = score_equipment_priority(equipment_id)
    conditions = get_simulated_conditions(equipment_id)

    context_text = f"EQUIPMENT: {equipment_id}\n\n"
    context_text += f"GOVERNING REGULATIONS (from knowledge graph): {', '.join(regulations) if regulations else 'None recorded'}\n\n"

    context_text += "FAILURE HISTORY SIGNAL (deterministic, from graph):\n"
    context_text += f"- Total recorded failures: {priority_data.get('total_failures', 'unknown')}\n"
    context_text += f"- Days since last failure: {priority_data.get('days_since_last_failure', 'unknown')}\n"
    context_text += f"- Priority/risk score: {priority_data.get('priority_score', 'unknown')}/10\n\n"

    context_text += f"SIMULATED CURRENT CONDITIONS ({conditions['note']}):\n"
    context_text += f"- Temperature: {conditions['temperature_c']}°C\n"
    context_text += f"- Vibration: {conditions['vibration_mm_s']} mm/s\n"
    context_text += f"- Pressure: {conditions['pressure_bar']} bar\n\n"

    all_sources = []
    context_text += "REGULATION TEXT (directly retrieved for the governing regulations above):\n"
    reg_counter = 1
    unsourced_regulations = []
    for reg in regulations:
        reg_chunks = get_regulation_text(reg, topic_hint=query)
        if not reg_chunks:
            unsourced_regulations.append(reg)
            continue
        for chunk in reg_chunks:
            source = chunk["metadata"].get("source", "unknown")
            context_text += f"[REG-{reg_counter}] (regulation: {reg}, source: {source}) {chunk['text'][:800]}\n\n"
            all_sources.append(source)
            reg_counter += 1

    if unsourced_regulations:
        context_text += f"NOTE: The following governing regulations are referenced in equipment records but their actual regulatory text is NOT present in this system's document corpus: {', '.join(unsourced_regulations)}. Do not fabricate their content — treat any compliance claim about these as unverifiable.\n\n"

    if reg_counter == 1:
        context_text += "No regulation text could be retrieved for the governing regulations listed.\n\n"

    system_prompt = """You are a Quality & Regulatory Compliance Intelligence agent for industrial equipment.

Using the governing regulations, their actual retrieved text, failure history signal, and simulated current
conditions provided, produce a structured compliance analysis. CRITICALLY: you must label every finding as
one of two types, and never blur them:

- [CONFIRMED]: Use ONLY when the regulation text explicitly states a specific, checkable requirement
  (e.g., "inspection shall occur every 90 days," "a written permit is required before X"), AND you can
  directly verify from the given context whether that specific requirement is met or not met.
  WRONG EXAMPLE (do not do this): "[CONFIRMED]: Equipment has undergone maintenance as evidenced by work
  orders" — this is NOT a compliance check, it is just restating that records exist. Never label a mere
  observation of activity as CONFIRMED unless it is directly checked against an explicit regulatory
  requirement stated in the retrieved text.
  If the retrieved regulation text does not contain a specific checkable requirement, you MUST say
  "[CONFIRMED]: None — retrieved text does not contain a specific checkable requirement" rather than
  inventing one.

- [RISK_SIGNAL]: Use for inferences drawn from patterns (e.g., failure recurrence, elevated simulated
  readings) that SUGGEST possible non-compliance but are not a direct, verified rule violation. Always
  state explicitly that this is an inference, not a confirmed finding.

Structure your answer as:
1. GOVERNING REGULATIONS SUMMARY
2. FINDINGS (each tagged [CONFIRMED] or [RISK_SIGNAL], with reasoning)
3. CROSS-REGULATORY CONFLICTS (if multiple regulations apply, note any apparent contradictions between their
   requirements for this equipment; if none evident from the given text, say so explicitly)
4. RECOMMENDED ACTION
5. CONFIDENCE

Cite regulation text using [REG-1], [REG-2] etc. Never present a [RISK_SIGNAL] as if it were [CONFIRMED]."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {query}"}
        ],
        temperature=0.1,
        max_tokens=900
    )

    answer = response.choices[0].message.content

    return {
        "answer": answer,
        "confidence": 55,
        "sources": all_sources,
        "equipment_id": equipment_id
    }
