# EduHyperRAG: Enhanced Hyper-RAG with Agentic Verification

**Enhanced Hyper-RAG with Agentic Verification for Reliable and Explainable Knowledge Retrieval**

---

## 📌 Project Overview

EduHyperRAG is an educational AI knowledge retrieval and question-answering framework built on hypergraph-driven retrieval principles and multi-agent verification workflows. Unlike standard RAG or traditional graph RAG (which only model pairwise relationships), EduHyperRAG captures high-order, multi-entity relationships ($\ge 3$ concepts) using **HyperNetX**, and verifies evidence sufficiency and claim accuracy using **LangGraph**.

---

## 🏗 System Architecture & Offline/Online Pipelines

```
OFFLINE PIPELINE:
Raw Educational Documents (PDF / Text)
  → Text Cleaning & Structure Normalization (TextCleaner)
  → Dual Chunking (Fixed-Length & Semantic Chunker)
  → Concept & Multi-Entity Hyperedge Extraction (ConceptHyperedgeExtractor)
  → Hypergraph Construction (EduHypergraphBuilder / HyperNetX)
  → Knowledge Base Persistence (ChromaDB + Hypergraph JSON)

ONLINE PIPELINE:
User Query
  → Dual Semantic & Hypergraph Retrieval (HybridRetriever)
  → Agentic Verification Workflow (LangGraph StateGraph)
      └─> Iterative Retrieval Loop (Bounded by Max Iterations)
  → Grounded Educational Answer Generation (EducationalAnswerGenerator)
  → Line-by-Line Claim Verification & Hallucination Checking (HallucinationChecker)
  → Explainability & Evidence Display (EduExplainabilityEngine)
  → Final User Output
```

---

## 📂 Project Structure

```
eduhyperrag/
│
├── data/
│   ├── raw/                  # Raw text/PDF educational files (Photosynthesis)
│   ├── processed/            # Cleaned text & Phase 2 extractions JSON
│   ├── chunks/               # Extracted structured text chunks JSON
│   ├── knowledge_base/       # Hypergraph JSON, concepts, hyperedges, ChromaDB
│   └── evaluation/           # Benchmark results CSV, JSON, and comparison PNG chart
│
├── src/
│   ├── config.py             # Global configuration & environment loader
│   ├── preprocessing/        # Text cleaner, fixed & semantic chunkers, pipeline
│   ├── extraction/           # Concept & hyperedge extractor, Pydantic schemas, prompts
│   ├── hypergraph/           # HyperNetX graph builder, query engine, visualizer
│   ├── retrieval/            # ChromaDB semantic retriever, hypergraph retriever, hybrid retriever
│   ├── agents/               # LangGraph agent state, retrieval node, verification node, graph workflow
│   ├── generation/           # Grounded educational answer generator, explainability report engine
│   ├── evaluation/           # Benchmark dataset, metrics calculator, baseline runners, report engine
│   └── utils/                # Structured logger, file I/O helpers
│
├── tests/                    # 28 modular unit tests across all 10 phases
├── app/                      # Streamlit interactive Web UI application (`main.py`)
├── backend/                  # FastAPI REST API foundation & pipeline adapters
│   ├── app/
│   │   ├── api/              # API route controllers (health, etc.)
│   │   ├── core/             # Configuration & environment settings
│   │   ├── schemas/          # Pydantic v2 validation models
│   │   ├── services/         # Pipeline adapters connecting FastAPI to src/
│   │   ├── tests/            # Automated pytest suite for backend endpoints
│   │   └── main.py           # FastAPI application entrypoint with CORS & middleware
│   ├── requirements.txt      # Backend API dependencies
│   └── run.py                # Standalone development server runner
├── frontend/                 # React 18 + TypeScript + Vite + Tailwind CSS frontend
│   ├── public/
│   ├── src/
│   │   ├── components/       # Common design system (Button, Card, Input, Modal, etc.) & layout
│   │   ├── layouts/          # PublicLayout and AppLayout (sidebar + top navbar)
│   │   ├── pages/            # LandingPage, Auth placeholders, Teacher & Student workspaces
│   │   ├── routes/           # React Router v6 route configuration
│   │   ├── services/         # Axios API client (api.ts) with health check
│   │   └── types/            # TypeScript navigation and API schemas
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts
├── scripts/                  # Command-line execution pipelines for all phases
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## ⚡ Installation & Quick Start

### 1. Environment Setup
```bash
# Activate Python Virtual Environment
# On Windows:
C:\Users\hp\AppData\Local\Python\bin\python.exe -m venv venv
venv\Scripts\activate

# Install Core Pipeline Dependencies
pip install -r requirements.txt

# Install FastAPI Backend Dependencies
pip install -r backend/requirements.txt
```

### 2. Environment Configuration
Copy `.env.example` to `.env`:
```env
LLM_API_KEY=your_api_key_here
LLM_MODEL_NAME=gemini-2.5-flash
DATA_DIR=data
LOG_LEVEL=INFO
DEFAULT_CHUNK_SIZE=1200
DEFAULT_CHUNK_OVERLAP=100
```

---

## 🚀 Execution Pipelines Across All 10 Phases

Execute each phase sequentially using Python:

```bash
# Phase 1: Text Preprocessing and Chunking
python scripts/run_phase1_preprocessing.py

# Phase 2: Concept and Hyperedge Extraction
python scripts/run_phase2_extraction.py

# Phase 3: Hypergraph Construction and Analytics
python scripts/run_phase3_hypergraph.py

# Phase 4: Combined Semantic + Hypergraph Retrieval
python scripts/run_phase4_retrieval.py

# Phase 5: Agentic Evidence Verification (LangGraph)
python scripts/run_phase5_agents.py

# Phase 6: Grounded Answer Generation
python scripts/run_phase6_generation.py

# Phase 7: Hallucination Detection & Claim Verification
python scripts/run_phase7_hallucination.py

# Phase 8: Explainability & Evidence Display
python scripts/run_phase8_explainability.py

# Phase 9: Evaluation Benchmark Framework
python scripts/run_phase9_evaluation.py

# Phase 10: Launch Interactive Streamlit Web UI
streamlit run app/main.py
```

---

## 🌐 FastAPI Backend Foundation (Step 2 Migration)

The backend layer provides a robust, non-blocking FastAPI foundation that integrates cleanly with the existing EduHyper-RAG pipeline.

### 1. Launch FastAPI Server
```bash
# Option A: Standalone runner
python backend/run.py

# Option B: Direct uvicorn command
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

### 2. Interactive API Documentation
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **OpenAPI Schema**: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

### 3. Subsystem Health Verification
```bash
# Query API health status:
curl http://127.0.0.1:8000/api/health
```
*Note: Health inspection safely checks subsystem readiness (database, ChromaDB, hypergraph files, and module imports) without executing expensive LLM or embedding calls.*

### 4. Authentication & RBAC Endpoints (Step 4)
- `POST /api/auth/register`: Register new student or instructor accounts.
- `POST /api/auth/login`: Authenticate with username or email and password; generates JWT bearer token.
- `GET /api/auth/me`: Retrieve current user profile (requires Bearer token).
- `GET /api/auth/teacher-only`: Verified teacher RBAC route.
- `GET /api/auth/student-only`: Verified student RBAC route.

*Pre-seeded Test Accounts in Database:*
- **Teacher**: Username `teacher`, Password `password123`
- **Student**: Username `student`, Password `password123`

### 5. Backend REST API Endpoints (Steps 2-8)
- `GET /api/health`: Subsystem health status for database, ChromaDB, and HyperNetX knowledge base.
- `POST /api/auth/register`: Register new student or teacher account with PBKDF2 hashing.
- `POST /api/auth/login`: Authenticate and issue JWT bearer token.
- `GET /api/auth/me`: Retrieve current authenticated user profile.
- `GET /api/courses`: List instructor created courses or student enrolled courses (`?all=true` for full catalog).
- `POST /api/courses`: Create new educational course (Instructor only).
- `POST /api/courses/{course_id}/enroll`: Enroll student in curriculum course.
- `GET /api/documents`: List accessible documents with chunk, concept, and hyperedge counts.
- `POST /api/documents/upload?course_id={id}`: Upload PDF/text document and trigger automated Phase 1-4 pipeline.
- `GET /api/tutor/sample-questions`: Curated sample educational questions for demonstration.
- `POST /api/tutor/query`: Execute multi-phase online retrieval (Phase 4-8) with agentic verification and hallucination checking.
- `GET /api/tutor/history`: Student QA history with verification decisions, grounded scores, and audit trails.
- `GET /api/hypergraph/documents/{doc_id}`: Complete document hypergraph (concept nodes, multi-entity hyperedges, cardinality breakdown).
- `GET /api/hypergraph/documents/{doc_id}/concepts/{concept_name}`: Detailed concept inspection (degree, connected hyperedges, 1-hop neighbors).
- `GET /api/hypergraph/documents/{doc_id}/image`: Static HyperNetX matplotlib publication render plot.
- `GET /api/analytics/teacher`: Classroom QA engagement, mean support scores, hallucination flag rate, and audit log.
- `GET /api/analytics/student`: Personalized student learning progress, grounding mastery, and course study activity.
- `GET /api/analytics/benchmark`: Phase 9 empirical baseline comparison across 6 retrieval architectures.

### 6. Run Backend Test Suite
```bash
# Runs health, auth, course, document, tutor, hypergraph, and analytics test suites (30 passing tests):
python -m pytest backend/app/tests/ -v
```

---

## 💻 React Frontend Foundation (Step 3 Migration)

The user-facing frontend is built with React 18, TypeScript, Vite, Tailwind CSS, React Router v6, and Axios.

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Configure Environment
Copy `.env.example` to `.env` (configured by default for local development):
```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### 3. Launch Development Server
```bash
cd frontend
npm run dev
```
Access the application at [http://127.0.0.1:5173/](http://127.0.0.1:5173/).

### 4. Production Build & TypeScript Verification
```bash
cd frontend
npm run build
```

---

## 🧪 Automated Unit Test Suite

Run the pipeline pytest suite (28 passing tests):
```bash
python -m pytest tests/ -v
```

---

## 📊 Empirical Evaluation Results Summary

| Architecture | Correctness | Faithfulness | Context Recall | KMR | HER | Total Latency (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Vanilla LLM** | 0.1229 | 1.0000 | 0.0000 | 1.0000 | 0.0000 | 0.15 |
| **Traditional RAG** | 0.0894 | 0.9159 | 0.9000 | 0.1000 | 0.0841 | 489.87 |
| **GraphRAG** | 0.0898 | 0.9225 | 1.0000 | 0.0000 | 0.0775 | 419.66 |
| **LightRAG** | 0.0995 | 0.9266 | 1.0000 | 0.0000 | 0.0734 | 409.76 |
| **Original Hyper-RAG** | 0.0995 | 0.9381 | 1.0000 | 0.0000 | 0.0619 | 431.17 |
| **Proposed Enhanced Hyper-RAG** | **0.0941** | **0.9488** | **1.0000** | **0.0000** | **0.0512** | **515.21** |

---

## 📜 License & Citation

Developed for final-year undergraduate project on **Enhanced Hyper-RAG with Agentic Verification**.
