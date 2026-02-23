# Finance AI API

![Version](https://img.shields.io/badge/version-3.0.0-blue) ![Python](https://img.shields.io/badge/python-3.10%2B-brightgreen) ![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688) ![License](https://img.shields.io/badge/license-MIT-green)

**Developer:** Bhuvan Rai

A professional, production-grade **Financial AI** service built with **FastAPI**, **ChromaDB**, and **Google Gemini AI**. Combines Retrieval-Augmented Generation (RAG) with a deterministic **Financial Intelligence Layer** for intelligent, auditable financial analysis and personal finance assistance.

---

## 🚀 Endpoints

### 🔵 v1 — RAG Advisory Engine + Scoring + Analytics + Simulation

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/rag/ask` | Conversational Q&A over ingested documents. Accepts optional `history` for follow-ups. Returns cited answer (`[CHUNK X]`). |
| `POST` | `/api/v1/rag/retrieve` | Returns raw document chunks for auditing without generating an answer. |
| `POST` | `/api/v1/score/financial-health` | Deterministic 0–100 financial health score. Accepts `{ user, incomes, expenses, assets, liabilities, insurances, financialGoals }`. |
| `POST` | `/api/v1/analytics/net-worth` | Net worth, liquidity ratio, asset allocation %, debt-to-asset ratio. Accepts `{ userId, assets, liabilities }`. |
| `POST` | `/api/v1/analytics/goal-feasibility` | Required SIP, funding gap, goal risk per goal. Accepts `{ userId, incomes, expenses, financialGoals }`. |
| `POST` | `/api/v1/analytics/portfolio-alignment` | Risk profile vs actual allocation mismatch. Accepts `{ userId, riskProfile, assets }`. |
| `POST` | `/api/v1/simulate/stress-test` | Recession, Job Loss, Rate Hike scenarios. Accepts `{ userId, incomes, expenses, assets, liabilities }`. |

> **Scoring components:** Savings Rate (25) · Emergency Fund (20) · Debt Ratio (20) · Diversification (15) · Insurance Coverage (20)

---

### 🟡 v2 — Personalized RAG

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v2/user-based-retrieval/` | Full-profile personalized RAG. Accepts complete financial profile (income, assets, liabilities, goals, insurance). Returns a cited `answer` + an LLM-compressed `history` string for persistent conversational memory. |

---

### 🟢 v3 — Financial Intelligence Layer *(also available at v1)*

> All v3 analytics and simulation endpoints are registered at both `/api/v1/` (for backend compatibility) and `/api/v3/` (for semantic versioning).

---

### ⚪ System

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/health` | Service health check. |

---

## 🧠 Architecture

```
Financial Intelligence Layer
│
├── Scoring Engine     → /score/financial-health
├── Analytics Engine   → /analytics/net-worth
│                         /analytics/goal-feasibility
│                         /analytics/portfolio-alignment
├── Simulation Engine  → /simulate/stress-test
└── Advisory Engine    → /rag/ask
(LLM)                     /rag/retrieve
                          /user-based-retrieval/
```

**Project Structure:**
```
app/
├── api/v1/endpoints/
│   ├── analytics.py         # Net worth, goal feasibility, portfolio alignment
│   ├── simulate.py          # Stress test
│   ├── score.py             # Financial health score
│   ├── user_retrieval.py    # Personalized RAG
│   └── rag.py               # Document Q&A
├── services/
│   ├── engines/
│   │   ├── net_worth.py
│   │   ├── goal_engine.py
│   │   ├── stress_engine.py
│   │   └── portfolio_engine.py
│   ├── rag/pipeline.py
│   ├── llm/gemini.py
│   └── embedding/gemini.py
├── infrastructure/vectordb/chroma.py
└── models/
    ├── score_schema.py
    └── user_schema.py        # CamelCase + snake_case input support
```

---

## ⚙️ Key Capabilities

- **Conversational Memory**: Follow-ups auto-rewritten into standalone queries. LLM compresses history into a dense ≤200-word memory string per turn.
- **Personalized RAG**: Real financial numbers injected into the prompt for grounded, user-specific advice.
- **Deterministic Engines**: All scoring, analytics, and simulation endpoints use pure math — no LLM, fully auditable.
- **Dynamic Token Budgeting**: Simple queries capped at 50 tokens; complex queries up to 1000 tokens.
- **Rate-Limit Resilience**: Exponential backoff with retry on all Gemini API calls.
- **Dual Input Format**: All models accept both `camelCase` (frontend) and `snake_case` (Python-native).

---

## 🔧 Getting Started

1. **Setup environment:**
   ```bash
   cp .env.example .env
   # Add your GEMINI_API_KEY to .env
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Ingest documents** (from `data/raw/`):
   ```bash
   .\.venv\Scripts\python.exe scripts/ingest_docs.py
   ```

4. **Run the API:**
   ```bash
   uvicorn app.main:app --reload
   ```

Interactive docs: `http://localhost:8000/docs`

---

## 📋 Version History

### v3.0.0 — Full Financial Intelligence Layer
- Added **Analytics Engine**: net worth, goal feasibility, portfolio alignment
- Added **Simulation Engine**: recession, job loss, rate hike stress testing
- Added **User-Based Retrieval** with LLM-compressed persistent memory
- CamelCase + snake_case dual input support across all models
- Exponential backoff and rate-limit resilience on all Gemini calls

### v2.0.0 — Conversational RAG & Health Scoring
- Conversational RAG over financial/regulatory documents (ChromaDB + Gemini)
- Follow-up question support via query contextualization
- Deterministic Financial Health Score (5 components, 0–100)
- Dual endpoints: `/ask` (answer only) and `/retrieve` (full audit trail)

### v1.0.0 — RAG Foundation
- Initial RAG pipeline with ChromaDB and Gemini embeddings
- Document ingestion and chunking pipeline
- Basic `/ask` endpoint

---

*Built by [Bhuvan Rai](https://github.com/BhuvanRai)*
