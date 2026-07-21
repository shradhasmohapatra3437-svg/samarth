import os
import sys
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from groq import Groq
from core.config import GROQ_API_KEY, GROQ_MODEL_FAST

client = Groq(api_key=GROQ_API_KEY)


def extract_entities_from_chunk(text: str, metadata: dict) -> dict:
    """
    Use LLM to extract named entities from a text chunk.
    
    We use GROQ_MODEL_FAST (llama3-8b) here instead of 70b
    because we're calling this for every chunk — speed matters.
    The 8b model is fast enough for structured extraction.
    """
    
    prompt = f"""Extract entities from this industrial document chunk.

Text:
{text[:1000]}

Extract and return ONLY a JSON object with these fields:
{{
  "equipment_tags": ["list of equipment IDs like P-204, C-07, HX-02"],
  "personnel": ["list of person names mentioned"],
  "regulations": ["list of regulatory references like OISD-STD-105, Section 36A"],
  "failure_modes": ["list of failure types mentioned"],
  "locations": ["list of zones, areas, departments mentioned"],
  "dates": ["list of dates mentioned"],
  "actions": ["list of actions taken like replaced, inspected, repaired"]
}}

If nothing found for a field return empty list [].
Return ONLY the JSON object. No explanation."""

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL_FAST,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=500
        )
        
        raw = response.choices[0].message.content.strip()
        
        # Clean JSON
        if "```" in raw:
            parts = raw.split("```")
            for part in parts:
                if part.startswith("json"):
                    raw = part[4:].strip()
                    break
                elif "{" in part:
                    raw = part.strip()
                    break
        
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1:
            raw = raw[start:end+1]
        
        entities = json.loads(raw)
        return entities
        
    except Exception as e:
        print(f"Entity extraction error: {e}")
        return {
            "equipment_tags": [],
            "personnel": [],
            "regulations": [],
            "failure_modes": [],
            "locations": [],
            "dates": [],
            "actions": []
        }


def extract_entities_batch(chunks: list, max_chunks: int = 50) -> list:
    """
    Extract entities from multiple chunks.
    max_chunks limits API calls to avoid rate limits.
    """
    results = []
    
    # Process limited chunks to avoid rate limiting
    chunks_to_process = chunks[:max_chunks]
    
    print(f"Extracting entities from {len(chunks_to_process)} chunks...")
    
    for i, chunk in enumerate(chunks_to_process):
        if i % 10 == 0:
            print(f"Processing chunk {i+1}/{len(chunks_to_process)}...")
        
        entities = extract_entities_from_chunk(
            chunk['text'], 
            chunk['metadata']
        )
        
        results.append({
            "chunk_id": chunk['metadata'].get('chunk_id', f'chunk_{i}'),
            "source": chunk['metadata'].get('source', ''),
            "doc_type": chunk['metadata'].get('doc_type', ''),
            "entities": entities
        })
    
    return results


if __name__ == "__main__":
    # Test with a few work order chunks
    test_chunks = [
        {
            "text": """Work Order: WO-2022-001
Equipment: P-204
Date: 2022-01-05
Failure: Seal failure detected, pump vibrating abnormally
Technician: Raghunath Panda
Resolution: Replaced mechanical seal as per OISD-STD-171 Section 4.2
OISD Reference: OISD-STD-171
Downtime: 8 hours
Status: completed""",
            "metadata": {
                "chunk_id": "wo_WO-2022-001",
                "source": "work_orders.json",
                "doc_type": "operational"
            }
        },
        {
            "text": """Incident Report: INC-2023-002
Date: 2023-06-15
Location: Zone 3 - Compressor House
Type: equipment failure
Severity: high
Description: Compressor C-07 showing excessive vibration during peak summer operations
Immediate Action: Shutdown initiated, area cleared
Root Cause: Thermal expansion due to high ambient temperature exceeding 42 degrees
Corrective Action: Valve V-33 adjusted, cooling enhanced per OISD-STD-116
Regulatory Reference: OISD-STD-116, Factories Act Section 7A""",
            "metadata": {
                "chunk_id": "inc_INC-2023-002",
                "source": "incident_reports.json",
                "doc_type": "operational"
            }
        }
    ]
    
    print("Testing entity extractor...")
    results = extract_entities_batch(test_chunks)
    
    for result in results:
        print(f"\nChunk: {result['chunk_id']}")
        print(f"Entities found:")
        for entity_type, values in result['entities'].items():
            if values:
                print(f"  {entity_type}: {values}")
                