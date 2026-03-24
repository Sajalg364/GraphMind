# SAP Order-to-Cash Graph Explorer

A graph-based data modeling and natural language query system for SAP Order-to-Cash (O2C) data. Users explore interconnected business entities visually and query the data conversationally — the system translates natural language into SQL via Google Gemini, executes it, and returns data-backed answers.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                         │
│  ┌─────────────────────┐    ┌────────────────────────────────┐  │
│  │  Graph Visualization │    │     Chat Interface             │  │
│  │  (react-force-graph) │    │  ┌──────────┐ ┌────────────┐  │  │
│  │                      │    │  │ User Msg  │ │ AI Response │  │  │
│  │  • Click to inspect  │    │  └──────────┘ │ + SQL shown │  │  │
│  │  • Expand neighbors  │    │               └────────────┘  │  │
│  │  • Color-coded nodes │    │  Example queries provided     │  │
│  └─────────────────────┘    └────────────────────────────────┘  │
└───────────────────────────────┬──────────────────────────────────┘
                                │ HTTP (REST API)
┌───────────────────────────────▼──────────────────────────────────┐
│                      Backend (FastAPI)                            │
│  ┌──────────┐  ┌────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │ /api/graph│  │/api/node/  │  │ /api/chat    │  │/api/stats │  │
│  │  Returns  │  │  Returns   │  │  NL → SQL    │  │  Table    │  │
│  │  nodes +  │  │  metadata  │  │  execution   │  │  counts   │  │
│  │  edges    │  │  + conns   │  │  + answer    │  │           │  │
│  └────┬─────┘  └─────┬──────┘  └──────┬───────┘  └─────┬─────┘  │
│       │              │               │                 │         │
│  ┌────▼──────────────▼───────────────▼─────────────────▼─────┐  │
│  │                    Graph Module                            │  │
│  │  • Entity configs (8 types)                               │  │
│  │  • Edge queries (8 relationship types)                    │  │
│  │  • Neighbor expansion                                     │  │
│  └───────────────────────┬───────────────────────────────────┘  │
│                          │                                       │
│  ┌───────────────────────▼───────────────────────────────────┐  │
│  │                    LLM Module                              │  │
│  │  Google Gemini 2.0 Flash                                  │  │
│  │  ┌─────────────────┐  ┌──────────────────────────────┐    │  │
│  │  │ System Prompt    │  │ Two-phase query:             │    │  │
│  │  │ • Schema context │  │ 1. NL → SQL generation       │    │  │
│  │  │ • Output format  │  │ 2. Results → NL answer       │    │  │
│  │  │ • Guardrails     │  │                              │    │  │
│  │  └─────────────────┘  └──────────────────────────────┘    │  │
│  └───────────────────────────────────────────────────────────┘  │
│                          │                                       │
│  ┌───────────────────────▼───────────────────────────────────┐  │
│  │                   SQLite Database                          │  │
│  │  19 tables • Indexed join paths • WAL mode                │  │
│  └───────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## NL-to-SQL Query Flow (Sequence)

```
User                Frontend            Backend             Gemini            SQLite
 │                    │                   │                   │                 │
 │  "Which products   │                   │                   │                 │
 │   have most bills?"│                   │                   │                 │
 │───────────────────>│                   │                   │                 │
 │                    │  POST /api/chat   │                   │                 │
 │                    │──────────────────>│                   │                 │
 │                    │                   │  Send NL question │                 │
 │                    │                   │  + full DB schema │                 │
 │                    │                   │──────────────────>│                 │
 │                    │                   │                   │                 │
 │                    │                   │  Returns JSON:    │                 │
 │                    │                   │  {type:"sql",     │                 │
 │                    │                   │   sql:"SELECT.."} │                 │
 │                    │                   │<──────────────────│                 │
 │                    │                   │                   │                 │
 │                    │                   │  Validate SQL     │                 │
 │                    │                   │  (SELECT only)    │                 │
 │                    │                   │                   │                 │
 │                    │                   │  Execute SQL      │                 │
 │                    │                   │─────────────────────────────────────>│
 │                    │                   │                   │     Results     │
 │                    │                   │<─────────────────────────────────────│
 │                    │                   │                   │                 │
 │                    │                   │  Send results     │                 │
 │                    │                   │  + question to    │                 │
 │                    │                   │  Gemini for       │                 │
 │                    │                   │  NL answer        │                 │
 │                    │                   │──────────────────>│                 │
 │                    │                   │                   │                 │
 │                    │                   │  NL answer        │                 │
 │                    │                   │<──────────────────│                 │
 │                    │                   │                   │                 │
 │                    │  {answer, sql,    │                   │                 │
 │                    │   data, rowCount} │                   │                 │
 │                    │<──────────────────│                   │                 │
 │                    │                   │                   │                 │
 │  Display answer    │                   │                   │                 │
 │  + SQL query       │                   │                   │                 │
 │<───────────────────│                   │                   │                 │
```

---

## Graph Data Model

### Entities (Nodes)

| Entity | Table | Primary Key | Color |
|--------|-------|-------------|-------|
| SalesOrder | sales_order_headers | salesOrder | Blue |
| Delivery | outbound_delivery_headers | deliveryDocument | Green |
| BillingDocument | billing_document_headers | billingDocument | Red |
| JournalEntry | journal_entry_items | accountingDocument | Orange |
| Payment | payments | accountingDocument | Purple |
| Customer | business_partners | businessPartner | Teal |
| Product | products | product | Crimson |
| Plant | plants | plant | Sky Blue |

### Relationships (Edges)

| Source | → | Target | Join Logic |
|--------|---|--------|------------|
| SalesOrder | HAS_DELIVERY | Delivery | delivery_items.referenceSdDocument = salesOrder |
| Delivery | BILLED_AS | BillingDocument | billing_items.referenceSdDocument = deliveryDocument |
| BillingDocument | GENERATES_ENTRY | JournalEntry | journal_entries.referenceDocument = billingDocument |
| JournalEntry | CLEARED_BY | Payment | payments.clearingAccountingDocument = accountingDocument |
| SalesOrder | PLACED_BY | Customer | salesOrder.soldToParty = businessPartner |
| SalesOrder | CONTAINS_PRODUCT | Product | salesOrderItem.material = product |
| Delivery | FROM_PLANT | Plant | deliveryItem.plant = plant |
| BillingDocument | BILLED_TO | Customer | billingDocument.soldToParty = businessPartner |

---

## Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Frontend** | React + react-force-graph-2d | Interactive canvas-based graph, handles hundreds of nodes smoothly |
| **Backend** | Python FastAPI | Async-capable, auto-docs, fast JSON serialization |
| **Database** | SQLite (WAL mode) | Zero-config, single file, perfect for read-heavy analytical workloads |
| **LLM** | Google Gemini 2.0 Flash | Free tier, fast, good SQL generation |
| **Build** | Vite | Fast HMR for development |

### Why SQLite over a graph database?

- The O2C dataset has well-defined relational structure with clear foreign keys — SQL JOINs handle traversals efficiently
- SQLite needs zero infrastructure and the database is a single portable file
- NL-to-SQL is a well-studied problem with strong LLM support; NL-to-Cypher/Gremlin is less reliable
- Indexed join paths give sub-millisecond query times on this dataset size

---

## LLM Prompting Strategy

### Two-Phase Approach

1. **Phase 1 — NL to SQL**: The system prompt embeds the complete database schema with all 19 tables, columns, types, and join relationships. Gemini generates a structured JSON response containing the SQL query.

2. **Phase 2 — Results to Answer**: Query results are sent back to Gemini with the original question, and it produces a clear natural language summary referencing actual data.

### Key Prompt Design Decisions

- **Schema-in-prompt**: The full schema is included in the system prompt rather than retrieved via RAG. At ~2K tokens, it fits comfortably and gives Gemini complete context for accurate JOINs.
- **Structured output**: Gemini returns JSON (`{type, sql, explanation}`) for reliable parsing. Avoids ambiguity in free-text SQL extraction.
- **Low temperature** (0.1): Deterministic SQL generation, no creative hallucination.
- **JOIN path documentation**: The O2C flow path (Sales Order → Delivery → Billing → Journal → Payment) is explicitly documented in the prompt, since these cross-table relationships are non-obvious.

---

## Guardrails

| Layer | Mechanism |
|-------|-----------|
| **LLM System Prompt** | Explicit instruction to reject off-topic queries with a standard message |
| **Keyword Detection** | Client-side fallback catches common off-topic patterns (weather, jokes, recipes, code) |
| **SQL Validation** | Regex-based check rejects INSERT/UPDATE/DELETE/DROP/ALTER/TRUNCATE. Only SELECT allowed. |
| **Multi-statement Block** | Queries with multiple semicolons are rejected |
| **Result Limits** | Default LIMIT 50 in prompt instructions; max 100 rows sent to LLM |

Example rejected queries:
- "Tell me a joke" → *"This system is designed to answer questions related to the SAP Order-to-Cash dataset only."*
- "DROP TABLE sales_order_headers" → Blocked by SQL validation
- "What's the weather?" → Rejected by keyword detection and LLM

---

## Project Structure

```
DodgeAi/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app, routes, startup
│   │   ├── database.py       # SQLite schema, connection, schema description
│   │   ├── ingest.py         # JSONL → SQLite data loader
│   │   ├── graph.py          # Graph construction (nodes, edges, neighbors)
│   │   ├── llm.py            # Gemini integration, NL-to-SQL, guardrails
│   │   └── schema.py         # Pydantic request/response models
│   ├── requirements.txt
│   └── .env                  # GEMINI_API_KEY
├── frontend/
│   ├── src/
│   │   ├── App.jsx           # Main app: graph + chat panels
│   │   ├── api.js            # API client functions
│   │   ├── index.css         # Dark theme styling
│   │   └── main.jsx          # React entry point
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── sap-order-to-cash-dataset/ # Source data (JSONL files)
└── README.md
```

---

## Setup & Run

### Prerequisites

- Python 3.10+
- Node.js 18+
- Google Gemini API key ([get free key](https://ai.google.dev))

### Backend

```bash
cd backend
pip install -r requirements.txt

# Set your Gemini API key
# Edit .env file: GEMINI_API_KEY=your_key_here

# Start the server (auto-ingests data on first run)
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

---

## Features

- **Interactive Graph Visualization**: Force-directed graph with 8 color-coded entity types. Click nodes to see metadata, expand to discover neighbors.
- **Natural Language to SQL**: Ask questions in plain English — Gemini generates SQL, the system executes it, and returns both the answer and the generated query.
- **Conversation History**: The chat maintains context from previous messages (last 6 turns) for follow-up questions.
- **Domain Guardrails**: Off-topic queries are rejected at multiple layers (LLM prompt, keyword detection, SQL validation).
- **Full O2C Flow Tracing**: Trace any document through the complete Sales Order → Delivery → Billing → Journal Entry → Payment pipeline.

---

## Example Queries

| Query | What it does |
|-------|-------------|
| "Which products have the most billing documents?" | Joins billing_document_items with products, counts and ranks |
| "Trace billing document 90504248" | Follows the full O2C chain for a specific document |
| "Sales orders delivered but not billed" | LEFT JOINs deliveries and billing to find gaps |
| "Top 5 customers by total order value" | Aggregates sales_order_headers by soldToParty |
| "Show payments for customer 310000108" | Joins payments with business_partners |
