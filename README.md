# Finance AI API

A professional, production-grade **Financial AI** service built with **FastAPI**, **ChromaDB**, and **Google Gemini AI**. Combines Retrieval-Augmented Generation (RAG) with a deterministic **Financial Intelligence Layer** for intelligent, auditable financial analysis and personal finance assistance.

---

## 🚀 Endpoints

### RAG (Advisory Engine)

#### `POST /api/v1/rag/ask`
Conversational RAG over ingested regulatory documents. Accepts optional `history` for follow-up questions. Returns cited answers (e.g., `[CHUNK 1]`).

#### `POST /api/v1/rag/retrieve`
Returns raw document chunks for auditing and transparency, without generating an answer.

#### `POST /api/v1/user-based-retrieval/`
Full-profile personalized RAG. Injects the user's real financial numbers (income, savings, EMI, risk profile, goals) into the retrieval prompt. Returns an `answer` + an LLM-compressed `history` string for persistent conversational memory.

---

### Scoring Engine

#### `POST /api/v1/score/financial-health`
Deterministic 0–100 score across 5 components. No LLM.

| Component          | Max |
|--------------------|-----|
| Savings Rate       | 25  |
| Emergency Fund     | 20  |
| Debt Ratio         | 20  |
| Diversification    | 15  |
| Insurance Coverage | 20  |

---

### Analytics Engine

#### `POST /api/v1/analytics/net-worth`
Computes net worth, liquidity ratio (months of runway), asset allocation %, and debt-to-asset ratio.

#### `POST /api/v1/analytics/goal-feasibility`
Per-goal analysis using the Future Value of Annuity formula. Returns required SIP, funding gap, inflation-adjusted target, and goal risk score (`low` / `medium` / `high` / `critical`).

#### `POST /api/v1/analytics/portfolio-alignment`
Checks mismatch between declared `risk_profile` and actual asset allocation. Flags behavioral inconsistencies (e.g., aggressive investor holding 90% FD).

---

### Simulation Engine

#### `POST /api/v1/simulate/stress-test`
Simulates 3 financial shock scenarios:
- **Recession**: 30% equity crash + 20% income drop
- **Job Loss**: Primary salary income drops to zero
- **Rate Hike**: All loan EMIs increase by 20%

Returns monthly surplus/shortfall, months of runway, per-scenario verdict, and overall resilience (`LOW` / `MEDIUM` / `HIGH`).

---

### `GET /api/v1/health` — Health Check

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
