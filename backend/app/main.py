import os
from functools import lru_cache
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .schema import ChatRequest, ChatResponse
from .graph import build_graph_data, get_node_details, get_neighbors
from .llm import query_llm
from .database import DB_PATH, init_db
from .ingest import ingest_all

app = FastAPI(title="SAP O2C Graph Explorer", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    if not DB_PATH.exists():
        print("Database not found. Running data ingestion...")
        ingest_all()
    else:
        init_db()


_graph_cache = {}

@app.get("/api/graph")
def get_graph(limit: int = 300):
    if limit not in _graph_cache:
        _graph_cache[limit] = build_graph_data(limit_nodes=limit)
    return _graph_cache[limit]


@app.get("/api/node/{entity_type}/{entity_id}")
def get_node(entity_type: str, entity_id: str):
    result = get_node_details(entity_type, entity_id)
    if not result:
        return {"error": "Node not found"}
    return result


@app.get("/api/neighbors/{entity_type}/{entity_id}")
def get_node_neighbors(entity_type: str, entity_id: str):
    return get_neighbors(entity_type, entity_id)


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    result = query_llm(req.question, req.conversation_history)
    return ChatResponse(
        type=result.get("type", "text"),
        answer=result.get("answer", ""),
        sql=result.get("sql"),
        row_count=result.get("rowCount"),
        data=result.get("data"),
    )


@app.get("/api/stats")
def get_stats():
    from .database import get_connection
    conn = get_connection()
    cur = conn.cursor()
    stats = {}
    tables = [
        ("Sales Orders", "sales_order_headers"),
        ("Sales Order Items", "sales_order_items"),
        ("Deliveries", "outbound_delivery_headers"),
        ("Delivery Items", "outbound_delivery_items"),
        ("Billing Documents", "billing_document_headers"),
        ("Billing Items", "billing_document_items"),
        ("Journal Entries", "journal_entry_items"),
        ("Payments", "payments"),
        ("Customers", "business_partners"),
        ("Products", "products"),
        ("Plants", "plants"),
    ]
    for label, table in tables:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        stats[label] = cur.fetchone()[0]
    conn.close()
    return stats


FRONTEND_DIR = Path(_file_).parent.parent.parent / "frontend" / "dist"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
