import json, sys, os, time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent.router import route_query

with open("measurement/benchmark_questions.json") as f:
    questions = json.load(f)

results = []
for idx, q in enumerate(questions):
    print(f"Running query {idx+1}/{len(questions)}: '{q['question']}'")
    
    # Simple retry loop for rate limits
    max_retries = 5
    retry_delay = 5
    for attempt in range(max_retries):
        try:
            start = time.time()
            result = route_query(q["question"])
            elapsed = round(time.time() - start, 2)
            break
        except Exception as e:
            if "rate_limit" in str(e).lower() or "429" in str(e):
                print(f"  Rate limit encountered (Attempt {attempt+1}/{max_retries}). Sleeping {retry_delay}s...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                print(f"  Error: {e}")
                result = {
                    "answer": f"ERROR: {e}",
                    "confidence": 0,
                    "sources": [],
                    "intent_classified": "error"
                }
                elapsed = 0.0
                break
    else:
        print("  Failed to execute query after maximum retries due to rate limits.")
        result = {
            "answer": "ERROR: Rate limit exceeded",
            "confidence": 0,
            "sources": [],
            "intent_classified": "error"
        }
        elapsed = 0.0

    # Check routing correctness
    routing_correct = result["intent_classified"] == q["expected_agent"]
    
    # Check answer contains expected keywords
    answer_lower = result["answer"].lower()
    keyword_hits = [kw for kw in q.get("expected_contains", []) if kw.lower() in answer_lower]
    
    results.append({
        "id": q["id"],
        "question": q["question"],
        "expected_agent": q["expected_agent"],
        "got_agent": result["intent_classified"],
        "routing_correct": routing_correct,
        "confidence": result["confidence"],
        "keyword_hits": f"{len(keyword_hits)}/{len(q.get('expected_contains',[]))}",
        "time_sec": elapsed,
        "answer_preview": result["answer"][:200]
    })
    
    # Sleep to avoid hitting rate limits on subsequent calls
    time.sleep(4)

# Summary
correct_routes = sum(1 for r in results if r["routing_correct"])
print(f"\n=== BENCHMARK RESULTS ===")
print(f"Routing accuracy: {correct_routes}/{len(results)} ({round(correct_routes/len(results)*100,1)}%)")
print(f"Avg response time: {round(sum(r['time_sec'] for r in results)/len(results),2)}s")
print(f"\nPer-question breakdown:")
for r in results:
    status = "[OK]  " if r["routing_correct"] else "[FAIL]"
    print(f"  {status} [{r['id']}] -> got '{r['got_agent']}', conf={r['confidence']}, time={r['time_sec']}s")

with open("measurement/benchmark_results.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nFull results saved to measurement/benchmark_results.json")