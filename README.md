# LawShield
# LawShield AI Service

> **An intelligent, privacy-first legal AI backend** powered by a multi-agent LangGraph pipeline, hybrid RAG (Retrieval-Augmented Generation), automatic PII masking tailored for Indian legal documents, and a robust document processing pipeline for PDFs, DOCX, and plain text.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Module Breakdown](#module-breakdown)
  - [Multi-Agent Graph](#1-multi-agent-graph-graph)
  - [PII Masking Pipeline](#2-pii-masking-pipeline-masking)
  - [Document Processing](#3-document-processing-document_processing)
  - [RAG Pipeline](#4-rag-pipeline-rag)
  - [LLM Providers](#5-llm-providers-llm)
  - [Chat Service](#6-chat-service-chat)
- [API Reference](#api-reference)
- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Running the Service](#running-the-service)
- [Configuration](#configuration)
- [Project Structure](#project-structure)

---

## Overview

LawShield AI Service is a FastAPI-based backend that provides:

| Capability | Description |
|---|---|
| **Intelligent Chat** | Multi-agent orchestration (Supervisor → Planner → Researcher → Reviewer) powered by LangGraph |
| **PII Masking** | Automatic detection and masking of 26 entity types before text reaches the LLM — restored transparently in the final response |
| **Document Processing** | Three-stage PDF extraction (PyMuPDF → pdfplumber → OCR), DOCX/TXT support, rich metadata extraction |
| **Hybrid RAG** | Combines semantic vector search (Qdrant) with BM25 lexical search (Elasticsearch) and cross-encoder reranking |
| **Multi-LLM Support** | Switch between OpenAI, Google Gemini, and Anthropic Claude at runtime |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Application                       │
│  /chat  │  /documents  │  /rag  │  /llm  │  /health            │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │       Chat Service       │
                    │  (masking ↔ unmasking)  │
                    └────────────┬────────────┘
                                 │
              ┌──────────────────▼──────────────────┐
              │        LangGraph Multi-Agent          │
              │                                       │
              │   Supervisor → Planner → Research     │
              │        ↑                     │        │
              │        └──── Reviewer ◄──────┘        │
              └──────────────────┬──────────────────-─┘
                                 │
              ┌──────────────────▼──────────────────┐
              │           RAG Pipeline               │
              │  Hybrid Search (Qdrant + ES)         │
              │  + BGE Reranker                      │
              └─────────────────────────────────────┘
```

### Request Flow

```
User Message
    │
    ▼
mask_text()          ← strip PII before it reaches the LLM
    │
    ▼
LangGraph Graph
    ├─ Supervisor  →  decides: needs research? or simple reply?
    ├─ Planner     →  creates a step-by-step research plan
    ├─ Research    →  runs hybrid_search(), synthesises findings
    └─ Reviewer    →  quality-gates the answer; loops back if rejected
    │
    ▼
restore_text()       ← re-inject original PII values
    │
    ▼
Final Response
```

---

## Module Breakdown

### 1. Multi-Agent Graph (`graph/`)

The core reasoning engine is a stateful LangGraph graph with four nodes:

| Node | Role |
|---|---|
| **Supervisor** | Analyses the request and decides whether full research is needed (`planner`) or a direct reply is sufficient (`FINISH`) |
| **Planner** | Produces a step-by-step research plan tailored to the legal query |
| **Research** | Executes the plan by running hybrid search against indexed documents; synthesises findings using the LLM |
| **Reviewer** | Evaluates the research output quality; approves or rejects (re-routes back to Planner up to 3 times) |

**State** (`graph/state.py`):

```python
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    plan: str
    research_data: List[str]
    review_status: str   # "approved" | "rejected"
    next_node: str
```

**Routing conditions** (`graph/conditions/routing.py`):
- Supervisor → `planner` or `END` based on `next_node`
- Reviewer → `planner` (if rejected and loop count < 3) or `END`

---

### 2. PII Masking Pipeline (`masking/`)

A privacy-first masking layer that intercepts every message *before* it reaches the LLM and restores original values *after* the response is generated. The LLM never sees raw PII.

#### Entity Coverage (26 types)

**Built-in Presidio entities:**

| Entity | Examples |
|---|---|
| `PERSON` | Client name, judge, witness |
| `EMAIL_ADDRESS` | Legal correspondence emails |
| `PHONE_NUMBER` | Generic international formats |
| `CREDIT_CARD` | Luhn-validated card numbers |
| `ORGANIZATION` | Law firms, companies |
| `LOCATION` | Addresses, cities |
| `DATE_TIME` | Hearing dates |
| `URL` | Links with personal paths |
| `NRP` | Nationality, religious, political identifiers |
| `MEDICAL_LICENSE` | Doctor identifiers |
| `IBAN_CODE` | International bank accounts |
| `IP_ADDRESS` | IPv4/IPv6 in cyber-law filings |

**India-specific custom entities:**

| Entity | Format | Example |
|---|---|---|
| `AADHAAR_NUMBER` | 12 digits, first digit 2–9 | `2345 6789 0123` |
| `IN_PAN` | `AAAAA9999A` | `ABCDE1234F` |
| `IN_GSTIN` | 15-char GST ID | `27AAPFU0939F1ZV` |
| `IN_VOTER_ID` | 3 alpha + 7 digits | `ABC1234567` |
| `IN_DRIVING_LICENCE` | State + RTO + year + 7 digits | `MH12 2019 0012345` |
| `IN_PASSPORT` | 1 alpha + 7 digits | `A1234567` |
| `IN_IFSC` | 4 alpha + 0 + 6 alphanumeric | `SBIN0001234` |
| `IN_PHONE_NUMBER` | +91 / 10-digit mobile | `+91 98765 43210` |
| `IN_VEHICLE_REG` | AA-00-AA-0000 | `MH-12-AB-1234` |
| `BANK_ACCOUNT` | 9–18 digits (context-gated) | `123456789012` |
| `US_SSN` | `XXX-XX-XXXX` | `123-45-6789` |
| `DATE_OF_BIRTH` | DD/MM/YYYY, ISO | `15/04/1990` |

#### Pipeline Features

- **Overlap resolution** — when two recognisers detect the same span, the higher-confidence result wins
- **Confidence threshold** — results below 0.35 are discarded to cut false positives
- **Short-token guard** — single-character detections (e.g. "I" as PERSON) are rejected
- **Case-insensitive deduplication** — "John Doe" and "john doe" always get the same placeholder
- **Single-pass restoration** — O(n) regex substitution instead of O(k×n) loop
- **Serialisable state** — `MaskingState.to_dict()` / `from_dict()` for persistence
- **Multi-turn merge** — `MaskingState.merge()` for session-spanning deduplication

#### Usage

```python
from masking import mask_text, restore_text

masked, state = mask_text("My client John Doe, PAN ABCDE1234F")
# masked → "My client <PERSON_1>, <IN_PAN_1>"

response = llm.invoke(masked)   # LLM never sees real PII

final = restore_text(response.content, state)
# final → original names/IDs restored
```

---

### 3. Document Processing (`document_processing/`)

A three-stage pipeline that handles PDF, DOCX, DOC, and TXT files.

#### PDF Extraction Strategy

```
Stage 1: PyMuPDF (fitz)
    │  Fast extraction for digitally-created PDFs
    │  Detects scanned pages (< 20 chars of text)
    ▼
Stage 2: pdfplumber  (for sparse pages)
    │  Better layout handling for multi-column / complex PDFs
    │  Extracts tables → pipe-delimited strings
    ▼
Stage 3: PaddleOCR  (for still-scanned pages)
    │  Renders each page to PNG at 200 DPI
    │  Confidence-filtered OCR (< 70% dropped)
    ▼
Clean → Metadata → Result
```

#### Text Cleaning (`cleaner.py`)

| Problem | Fix |
|---|---|
| PDF ligatures (ﬁ, ﬂ, ﬀ) | Expanded to fi, fl, ff |
| Soft hyphens, BOM, zero-width spaces | Removed |
| Hyphenated line-breaks (`appli-\ncation`) | Repaired to `application` |
| Control characters (0x00–0x1F) | Stripped |
| Page-number artefact lines | Removed |
| Multiple blank lines | Collapsed to one paragraph break |
| Windows `\r\n` line endings | Normalised |
| Non-breaking / narrow spaces | Converted to regular spaces |

#### Metadata Extraction (`metadata.py`)

Unified schema across all file types:

```json
{
  "file_type": "pdf",
  "page_count": 12,
  "word_count": 3400,
  "char_count": 19872,
  "title": "Sale Deed",
  "author": "Adv. Sharma",
  "creation_date": "2023-04-15T12:00",
  "mod_date": "2023-05-01T09:30",
  "encrypted": false,
  "pdf_version": "1.7",
  "file_size_bytes": 204800
}
```

#### API Response

```json
{
  "filename": "contract.pdf",
  "file_type": "pdf",
  "text": "THIS AGREEMENT is entered into...",
  "page_count": 5,
  "word_count": 2100,
  "char_count": 12500,
  "scanned_pages": 0,
  "pages": [
    {"page_number": 1, "word_count": 450, "is_scanned": false},
    {"page_number": 2, "word_count": 380, "is_scanned": false}
  ],
  "metadata": { ... },
  "error": null
}
```

---

### 4. RAG Pipeline (`rag/`)

| Component | Technology | Purpose |
|---|---|---|
| **Embeddings** | `BAAI/bge-large-en-v1.5` (HuggingFace) | 1024-dim vectors, normalised |
| **Vector Store** | Qdrant | Semantic similarity search |
| **Lexical Store** | Elasticsearch | BM25 keyword search |
| **Reranker** | `BAAI/bge-reranker-base` (CrossEncoder) | Re-scores top-k results |
| **Chunking** | `RecursiveCharacterTextSplitter` | 1000 chars, 200 overlap |

**Hybrid search** fetches from both Qdrant and Elasticsearch, deduplicates by text, reranks the combined pool with a cross-encoder, and returns the top-3 most relevant chunks.

---

### 5. LLM Providers (`llm/`)

Swap providers at runtime via the `provider` field in any chat request.

| Provider | Model | Set `DEFAULT_LLM_PROVIDER` |
|---|---|---|
| OpenAI | `gpt-4o-mini` | `openai` |
| Google Gemini | `gemini-1.5-flash` | `gemini` |
| Anthropic | `claude-3-haiku-20240307` | `anthropic` |

---

### 6. Chat Service (`chat/`)

- **`POST /chat/`** — Non-streaming. Runs the full LangGraph pipeline and returns the final answer.
- **`POST /chat/stream`** — Server-Sent Events (SSE). Streams node-by-node execution status and the final answer.
- **`DELETE /chat/history/{session_id}`** — Clear in-memory conversation history.

Session history is stored in-memory per `session_id`. For production, wire `get_session_history()` to Redis via `settings.REDIS_URL`.

---

## API Reference

### Base URL
```
http://localhost:8000
```

### Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/chat/` | Non-streaming chat |
| `POST` | `/chat/stream` | Streaming chat (SSE) |
| `DELETE` | `/chat/history/{session_id}` | Clear session history |
| `POST` | `/documents/upload` | Process a document |
| `POST` | `/documents/upload-and-ingest` | Process + index into RAG |
| `GET` | `/documents/supported-types` | List accepted file types |
| `POST` | `/rag/ingest` | Index raw text into RAG |
| `POST` | `/rag/ask` | Ask a question over indexed documents |
| `GET` | `/llm/status` | LLM module status |

### Interactive API Docs
After starting the server, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Example: Chat Request

```bash
curl -X POST http://localhost:8000/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "user-123",
    "message": "What are the legal remedies available for breach of contract in India?",
    "provider": "gemini"
  }'
```

### Example: Streaming Chat

```bash
curl -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "user-123",
    "message": "Explain Section 138 of the Negotiable Instruments Act"
  }'
```

### Example: Upload a Document

```bash
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@/path/to/contract.pdf"
```

### Example: Upload + Ingest into RAG

```bash
curl -X POST http://localhost:8000/documents/upload-and-ingest \
  -F "file=@/path/to/legal_brief.pdf"
```

### Example: RAG Question

```bash
curl -X POST http://localhost:8000/rag/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the payment terms in the uploaded contract?",
    "collection_name": "documents"
  }'
```

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.13+ | Use `uv` or `pyenv` |
| Docker + Docker Compose | Latest | For Qdrant + Elasticsearch |
| `uv` (recommended) | Latest | Fast package manager |

### Install `uv` (if not installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## Environment Setup

### 1. Clone and enter the directory

```bash
cd lawShield/ai_service
```

### 2. Create the virtual environment and install dependencies

```bash
uv venv
uv sync
```

Or with standard pip:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
```

### 3. Download the spaCy NLP model

Required for PII entity detection (one-time download, ~382 MB):

```bash
uv run python -m spacy download en_core_web_lg
```

Or with pip:

```bash
python -m spacy download en_core_web_lg
```

### 4. Configure environment variables

Copy the example and fill in your API keys:

```bash
cp .env.example .env   # or edit .env directly
```

**.env file:**

```dotenv
# ── LLM Provider API Keys ─────────────────────────────────────────
# Set the key for whichever provider you select below.
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AIza...
ANTHROPIC_API_KEY=sk-ant-...

# Active provider: openai | gemini | anthropic
DEFAULT_LLM_PROVIDER=gemini

# ── Infrastructure ────────────────────────────────────────────────
QDRANT_URL=http://localhost:6333
ELASTICSEARCH_URL=http://localhost:9200

# ── Optional: Redis for persistent session history ────────────────
REDIS_URL=redis://localhost:6379
```

> **Note:** You only need an API key for the provider you intend to use. The service starts even if other keys are absent.

---

## Running the Service

### Step 1 — Start infrastructure (Qdrant + Elasticsearch)

```bash
docker compose up -d
```

Verify they are up:

```bash
# Qdrant health
curl http://localhost:6333/healthz

# Elasticsearch health
curl http://localhost:9200/_cluster/health?pretty
```

### Step 2 — Start the FastAPI server

#### With `uv` (recommended):

```bash
uv run python main.py
```

#### With the virtual environment activated:

```bash
source .venv/bin/activate
python main.py
```

#### Or with `uvicorn` directly (hot-reload):

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The server will be available at **http://localhost:8000**.

---

### Quick Smoke Test

Once the server is running, verify all systems are working:

```bash
# 1. Health check
curl http://localhost:8000/health

# 2. LLM status
curl http://localhost:8000/llm/status

# 3. List accepted document types
curl http://localhost:8000/documents/supported-types

# 4. Send a simple chat message
curl -X POST http://localhost:8000/chat/ \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "message": "Hello, who are you?"}'
```

---

## Configuration

All settings are managed via `config/settings.py` using Pydantic Settings and are read from `.env`.

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | `None` | OpenAI API key |
| `GEMINI_API_KEY` | `None` | Google Gemini API key |
| `ANTHROPIC_API_KEY` | `None` | Anthropic API key |
| `DEFAULT_LLM_PROVIDER` | `openai` | Active provider (`openai` / `gemini` / `anthropic`) |
| `QDRANT_URL` | `http://localhost:6333` | Qdrant vector database URL |
| `ELASTICSEARCH_URL` | `http://localhost:9200` | Elasticsearch URL |
| `REDIS_URL` | `None` | Optional Redis for session history persistence |

### Masking Configuration

Tunable constants in `masking/ner.py`:

```python
CONFIDENCE_THRESHOLD = 0.35   # Lower → more detections, more false positives
                               # Higher → fewer detections, fewer false positives
```

### Chunking Configuration

In `rag/chunking.py`:

```python
chunk_size    = 1000   # Characters per chunk
chunk_overlap = 200    # Overlap between adjacent chunks
```

---

## Project Structure

```
ai_service/
├── main.py                          # FastAPI app entry point
├── pyproject.toml                   # Dependencies (uv/pip)
├── docker-compose.yml               # Qdrant + Elasticsearch
├── .env                             # API keys and config (git-ignored)
│
├── config/
│   └── settings.py                  # Pydantic Settings
│
├── chat/                            # Chat API
│   ├── router.py                    # POST /chat/, /chat/stream, DELETE /chat/history
│   ├── chat_service.py              # LangGraph orchestration + masking integration
│   └── history.py                   # In-memory session history store
│
├── graph/                           # LangGraph multi-agent system
│   ├── graph.py                     # StateGraph definition and compilation
│   ├── state.py                     # AgentState TypedDict
│   ├── nodes/
│   │   ├── supervisor.py            # Routing decision node
│   │   ├── planner.py               # Research plan generator
│   │   ├── research.py              # RAG-powered research executor
│   │   └── reviewer.py              # Quality gate with re-route logic
│   └── conditions/
│       └── routing.py               # route_supervisor(), route_reviewer()
│
├── masking/                         # PII masking pipeline
│   ├── masking_pipeline.py          # mask_text(), restore_text() — main API
│   ├── replacement.py               # MaskingState — bidirectional placeholder map
│   ├── ner.py                       # Presidio AnalyzerEngine setup (26 entities)
│   └── regex.py                     # 14 custom recognisers (India-specific)
│
├── document_processing/             # Document ingestion pipeline
│   ├── loaders.py                   # Main entry: process_document()
│   ├── parser.py                    # PyMuPDF, pdfplumber, OCR, DOCX, TXT parsers
│   ├── cleaner.py                   # Text normalisation (ligatures, artefacts, etc.)
│   ├── metadata.py                  # Unified metadata extraction (PDF/DOCX/TXT)
│   ├── ocr.py                       # PaddleOCR wrapper with confidence filtering
│   └── router.py                    # POST /documents/upload, /upload-and-ingest, /supported-types
│
├── rag/                             # Retrieval-Augmented Generation
│   ├── pipelines.py                 # ingest_document(), ask_question_pipeline()
│   ├── retrieval.py                 # hybrid_search() — Qdrant + Elasticsearch
│   ├── embedding.py                 # BGE large embedding model
│   ├── reranker.py                  # BGE cross-encoder reranker
│   ├── chunking.py                  # RecursiveCharacterTextSplitter
│   └── router.py                    # POST /rag/ingest, /rag/ask
│
└── llm/                             # LLM provider abstraction
    ├── providers/
    │   ├── base.py                  # BaseLLMProvider ABC
    │   └── factory.py               # OpenAI / Gemini / Anthropic providers
    ├── prompts/
    │   └── templates.py             # ChatPromptTemplate definitions
    ├── parser.py                    # Output parsers
    └── router.py                    # GET /llm/status
```

---

## Troubleshooting

### spaCy model not found

```
OSError: [E050] Can't find model 'en_core_web_lg'
```

**Fix:**

```bash
uv run python -m spacy download en_core_web_lg
```

The service will fall back to `en_core_web_sm` automatically if the large model is absent — masking still works but with lower accuracy.

---

### Qdrant / Elasticsearch connection errors

The RAG pipeline degrades gracefully — chat and document upload still work. Vector search returns empty results until the databases are running.

```bash
docker compose up -d
docker compose ps      # verify both services are "Up"
```

---

### PaddleOCR not installed

OCR is only triggered for scanned PDFs. If PaddleOCR is not installed, scanned pages return empty text and the rest of the document is still processed normally.

```bash
uv add paddleocr paddlepaddle
```

---

### Gemini API key format

Valid Gemini API keys start with `AIza`. If you see authentication errors, regenerate your key at [Google AI Studio](https://aistudio.google.com/app/apikey).
