import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()
from groq import Groq
from rag.embedder import search_similar
from knowledge_graph.graph_query import load_graph, get_graph_context

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

graph = load_graph()

def build_context(query, k=8):
    if not query or not query.strip():
        return "", 0.0, []

    chunks = search_similar(query, n_results=k)
    graph_facts = get_graph_context(query, graph)
    print(f"DEBUG - Graph facts found: {graph_facts}")

    context_text = "REGULATORY & OPERATIONAL CHUNKS:\n"
    for i, chunk in enumerate(chunks):
        source = chunk["metadata"].get("source", "unknown")
        context_text += f"[{i+1}] (source: {source}) {chunk['text']}\n\n"

    if graph_facts:
        context_text += "\n[GRAPH] KNOWLEDGE GRAPH FACTS (cite as [Graph] in your answer):\n"
        for fact in graph_facts:
            context_text += f"- {fact['entity']}:\n"
            for edge in fact["edges"]:
                context_text += f"    {fact['entity']} --[{edge['relationship']}]--> {edge['neighbor']} (occurred {edge['weight']} times)\n"

    avg_distance = sum(c["distance"] for c in chunks) / len(chunks) if chunks else 1.0
    confidence = max(0, round((1 - avg_distance) * 100, 1))

    return context_text, confidence, chunks

def answer_query(query):
    if not query or not query.strip():
        return {
            "answer": "Please provide a question.",
            "confidence": 0,
            "sources": []
        }

    context_text, confidence, chunks = build_context(query)

    system_prompt = """You are an industrial safety and maintenance expert copilot.
Answer ONLY using the provided context. Cite chunk sources using [1], [2] etc. matching the numbered chunks.
When citing the KNOWLEDGE GRAPH FACTS section, cite it as [Graph] — never invent a different citation format for it.

IMPORTANT: For any statistics or counts (how many times something failed, how many repairs were done), 
always use the exact numbers from the KNOWLEDGE GRAPH FACTS section if present — these are ground-truth 
counts, more reliable than counting mentions in the retrieved chunks. Do not undercount based on how many 
chunks happen to mention something; use the graph's stated occurrence count as the authoritative number.

If the context doesn't contain the answer, say so clearly. Be concise and factual."""

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

    return {
        "answer": answer,
        "confidence": confidence,
        "sources": [c["metadata"].get("source", "unknown") for c in chunks]
    }

if __name__ == "__main__":
    test_query = "Why does P-204 keep failing and who usually fixes it?"
    result = answer_query(test_query)
    print("ANSWER:\n", result["answer"])
    print("\nCONFIDENCE:", result["confidence"])
    print("SOURCES:", result["sources"])
    