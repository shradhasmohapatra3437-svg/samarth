import os
import sys
import time
from collections import defaultdict
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.router import route_query
from knowledge_graph.graph_query import load_graph
from rca.priority_scorer import score_equipment_priority
from modules.maintenance.failure_intelligence import generate_fleet_report
from modules.compliance.qms_report import generate_qms_report
from rag.embedder import get_chroma_client, get_or_create_collection

app = FastAPI(title="Samarth Expert Copilot API - Hardened Edition")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Simple Request Counter Rate Limiter (No external dependency required)
class RequestRateLimiter:
    def __init__(self, requests_limit: int = 15, window_secs: int = 60):
        self.requests_limit = requests_limit
        self.window_secs = window_secs
        self.client_records = defaultdict(list)

    def check_rate_limit(self, client_ip: str) -> bool:
        now = time.time()
        # Filter timestamps outside window
        self.client_records[client_ip] = [
            t for t in self.client_records[client_ip]
            if now - t < self.window_secs
        ]
        if len(self.client_records[client_ip]) >= self.requests_limit:
            return False
        self.client_records[client_ip].append(now)
        return True

limiter = RequestRateLimiter(requests_limit=15, window_secs=60)


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str
    confidence: float
    sources: list[str]
    intent_classified: str
    equipment_id: str | None = None


@app.get("/")
def root():
    return {"status": "Samarth API running - Hardened Edition"}


@app.get("/health")
def health_check():
    """
    Diagnostic endpoint reports:
    - Overall status
    - Knowledge graph nodes count
    - Chroma vector DB document count
    """
    try:
        graph = load_graph()
        graph_nodes = graph.number_of_nodes()
    except Exception:
        graph_nodes = 0

    try:
        client_db = get_chroma_client()
        collection = get_or_create_collection(client_db)
        chroma_docs = collection.count()
    except Exception:
        chroma_docs = 0

    return {
        "status": "healthy",
        "graph_nodes_count": graph_nodes,
        "chroma_documents_count": chroma_docs
    }


@app.post("/query", response_model=QueryResponse)
def query_endpoint(query_request: QueryRequest, request: Request):
    # 1. Rate Limiting check
    client_ip = request.client.host if request.client else "unknown"
    if not limiter.check_rate_limit(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Maximum 15 requests per minute allowed."
        )

    # 2. Input validation
    question = query_request.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="Question cannot be empty.")
    if len(question) > 1000:
        raise HTTPException(status_code=422, detail="Question length exceeds the 1000 characters limit.")

    # 3. Request processing with error catching
    try:
        result = route_query(question)
        return result
    except Exception as e:
        err_msg = str(e)
        if "rate_limit" in err_msg.lower() or "429" in err_msg:
            raise HTTPException(
                status_code=429,
                detail="Groq LLM rate limit reached. Please wait a few minutes before trying again."
            )
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {err_msg}")


@app.get("/equipment/list")
def list_equipment():
    try:
        graph = load_graph()
        equip_nodes = [node for node, data in graph.nodes(data=True) if data.get("node_type") == "equipment"]
        return {"equipment": sorted(equip_nodes)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load equipment list: {str(e)}")


@app.get("/equipment/{equipment_id}/priority")
def get_priority(equipment_id: str):
    try:
        res = score_equipment_priority(equipment_id)
        if "error" in res:
            raise HTTPException(status_code=404, detail=res["error"])
        return res
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate equipment priority: {str(e)}")


@app.get("/equipment/{equipment_id}/qms-report")
def get_qms_report_endpoint(equipment_id: str):
    try:
        report = generate_qms_report(equipment_id)
        return report
    except Exception as e:
        err_msg = str(e)
        if "rate_limit" in err_msg.lower() or "429" in err_msg:
            raise HTTPException(
                status_code=429, 
                detail="Groq LLM rate limit reached during compliance audit calculation."
            )
        raise HTTPException(status_code=500, detail=f"Failed to generate QMS report: {err_msg}")


@app.get("/fleet/failure-report")
def get_fleet_report_endpoint():
    try:
        report = generate_fleet_report()
        return report
    except Exception as e:
        err_msg = str(e)
        if "rate_limit" in err_msg.lower() or "429" in err_msg:
            raise HTTPException(
                status_code=429, 
                detail="Groq LLM rate limit reached during fleet failure analysis."
            )
        raise HTTPException(status_code=500, detail=f"Failed to generate fleet report: {err_msg}")


@app.get("/graph/data")
def get_graph_data():
    try:
        graph = load_graph()
        nodes = []
        for n, data in graph.nodes(data=True):
            nodes.append({
                "id": n,
                "label": n,
                "type": data.get("node_type", "unknown"),
                "mentions": data.get("mentions", 1)
            })
        edges = []
        for u, v, data in graph.edges(data=True):
            edges.append({
                "source": u,
                "target": v,
                "relationship": data.get("relationship", "RELATED_TO"),
                "weight": data.get("weight", 1)
            })
        return {"nodes": nodes, "edges": edges}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load graph data: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)