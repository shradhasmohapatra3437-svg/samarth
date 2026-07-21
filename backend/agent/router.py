import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from groq import Groq
from rag.rag_engine import answer_query as general_answer_query
from rca.rca_engine import run_rca
from compliance.compliance_engine import run_compliance_check

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)


def classify_query(query: str) -> str:
    if not query or not query.strip():
        return "general"

    system_prompt = """Classify the user's question into exactly one category:
- "rca" — if asking about root causes, why equipment fails repeatedly, failure patterns
- "compliance" — if asking about regulatory requirements, compliance gaps, standard violations
- "general" — if asking a general knowledge/lookup question about equipment, personnel, or documents
- "mixed" — if the question needs both RCA and compliance reasoning

Respond with ONLY one word: rca, compliance, general, or mixed."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ],
        temperature=0,
        max_tokens=10
    )
    category = response.choices[0].message.content.strip().lower()
    if category not in ["rca", "compliance", "general", "mixed"]:
        category = "general"
    return category


def general_tool(query: str):
    result = general_answer_query(query)
    result["equipment_id"] = None
    return result


def mixed_tool(query: str):
    """
    Genuinely combines RCA and Compliance analysis for questions that need both,
    rather than falling back to plain general RAG.
    """
    rca_result = run_rca(query)
    compliance_result = run_compliance_check(query)

    synthesis_prompt = f"""You are synthesizing two separate analyses into one combined answer.

RCA ANALYSIS:
{rca_result.get('answer', 'No RCA analysis available.')}

COMPLIANCE ANALYSIS:
{compliance_result.get('answer', 'No compliance analysis available.')}

Combine these into ONE coherent answer to the original question, preserving the RCA analysis's
root-cause reasoning AND the compliance analysis's CONFIRMED/RISK_SIGNAL distinctions. Do not lose
any citations ([OEM-x], [HIST-x], [REG-x]) from either source. Be concise — avoid repeating the same
point from both analyses if they overlap."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You synthesize technical analyses concisely and accurately, preserving all citations."},
            {"role": "user", "content": f"{synthesis_prompt}\n\nOriginal question: {query}"}
        ],
        temperature=0.1,
        max_tokens=900
    )

    combined_sources = rca_result.get("sources", []) + compliance_result.get("sources", [])
    equipment_id = rca_result.get("equipment_id") or compliance_result.get("equipment_id")

    return {
        "answer": response.choices[0].message.content,
        "confidence": min(rca_result.get("confidence", 0), compliance_result.get("confidence", 0)),
        "sources": combined_sources,
        "equipment_id": equipment_id
    }


def route_query(query: str):
    category = classify_query(query)

    if category == "rca":
        result = run_rca(query)
    elif category == "compliance":
        result = run_compliance_check(query)
    elif category == "mixed":
        result = mixed_tool(query)
    else:
        result = general_tool(query)

    result["intent_classified"] = category
    return result
