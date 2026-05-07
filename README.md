# A Hallucination-Resistant Retrieval-Augmented Generation System for Grounded Financial Query Answering

A production-grade Retrieval-Augmented Generation (RAG) system for grounded financial query answering. Deployed on Kubernetes via Minikube, the service integrates a multi-node LangGraph pipeline, three MCP data sources, FinBERT-based sentiment analysis, and a confidence-gated reflection mechanism.


>
> <img width="926" height="469" alt="Screenshot 2026-05-05 at 8 33 07 AM" src="https://github.com/user-attachments/assets/36c67775-c0f8-45ac-b5a5-54d76400fe0b" />




<img width="852" height="584" alt="image" src="https://github.com/user-attachments/assets/840c2e37-1e09-4d09-9002-ff311c624c6b" />






















## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Services](#services)
- [Pipeline Design](#pipeline-design)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Testing](#testing)
- [Benchmarking](#benchmarking)
- [Deployment](#deployment)


---

## Architecture Overview

<img width="648" height="586" alt="image" src="https://github.com/user-attachments/assets/7e499276-d8b5-49e2-ba2b-7b957a1d7631" />


The system is built around three layers:

```
┌─────────────────────────────────────────────────────┐
│  Data Sources — MCP Servers                         │
│  finance-market (Alpha Vantage)                     │
│  finance-sec    (SEC EDGAR)                         │
│  finance-social (Twitter/X sentiment)               │
├─────────────────────────────────────────────────────┤
│  LangGraph Agentic Pipeline                         │
│  intent → fetch → validate → store → retrieve       │
│  → ticker_guard → evaluate → answer                 │
│  → analyst (FinBERT) → reflection → scribe          │
├─────────────────────────────────────────────────────┤
│  Core — Vector Store + Model Backbone               │
│  ChromaDB (persistent)  +  all-MiniLM-L6-v2         │
└─────────────────────────────────────────────────────┘
```

Four microservices run as independent Kubernetes pods:

| Service | Image | Port | Role |
|---|---|---|---|
| `finance-api` | `finance-api:v2` | 8000 | FastAPI + LangGraph orchestration, FinBERT, ChromaDB |
| `finance-market` | `finance-market:v1` | 8003 | Alpha Vantage real-time OHLCV via MCP |
| `finance-sec` | `finance-sec:v1` | 8001 | SEC EDGAR 10-K/10-Q filings via MCP |
| `finance-social` | `finance-social-mcp:v1` | 8003 | Social sentiment (VADER / Twitter/X) via MCP |

---

## Project Structure

```
.
├── finance_service/                     # Main application package
│   ├── __init__.py
│   ├── main.py                          # FastAPI app + LangGraph graph + all 11 pipeline nodes
│   ├── baseline_model.py                # Plain LLM pipeline (BASELINE experiment mode)
│   ├── optimized_pipeline.py            # RAG pipeline (OPTIMIZED experiment mode)
│   ├── llm.py                           # LocalLlamaLLM wrapper — TinyLlama on MPS/CUDA/CPU
│   ├── config.py                        # Settings class — env vars, thresholds, entity registry
│   ├── service.py                       # FinanceService entrypoint / experiment mode switcher
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── analyst.py                   # FinBERT sentiment agent (AnalystAgent)
│   │   ├── reflection.py                # Confidence gate agent (ReflectionAgent)
│   │   ├── scribe.py                    # Structured report formatter (ScribeAgent)
│   │   ├── researcher.py                # MCP fetch + vector retrieval (used by benchmark)
│   │   └── orchestrator.py              # Standalone orchestrator (logic absorbed into main.py)
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── embedding_model.py           # Sentence transformer wrapper (all-MiniLM-L6-v2)
│   │   ├── financial_model.py           # FinBERT wrapper for direct use
│   │   └── vector_store.py              # In-memory FAISS vector store (benchmark use)
│   │
│   ├── evaluation/
│   │   ├── __init__.py
│   │   └── hallucination.py             # Sentence-overlap hallucination metric
│   │
│   └── ingestion/
│       ├── __init__.py
│       └── mcp_client.py                # JSON-RPC 2.0 MCP client
│
├── mcp_servers/                         # MCP server implementations (one per data source)
│   ├── __init__.py
│   ├── base_mcp.py                      # Shared MCP server base — /mcp and /health endpoints
│   ├── market_server.py                 # Alpha Vantage TIME_SERIES_DAILY endpoint
│   ├── sec_server.py                    # SEC EDGAR public REST API (ticker → CIK → filings)
│   ├── social_server.py                 # Social sentiment — VADER + Twitter/X API v2
│   ├── Dockerfile.market                # Container image for finance-market
│   ├── Dockerfile.sec                   # Container image for finance-sec
│   └── Dockerfile.social                # Container image for finance-social
│
├── db/
│   └── chroma.sqlite3                   # ChromaDB persistent vector store (do not commit)
│
├── # ── Kubernetes manifests ──────────────────────────────────────────
├── finance-api-deployment.yaml          # finance-api Deployment (2Gi / 500m)
├── finance-api-service.yaml             # NodePort 30080 → pod 8000
├── finance-market-deployment.yaml
├── finance-market-service.yaml          # ClusterIP → pod 8003
├── finance-sec-deployment.yaml
├── finance-sec-service.yaml             # ClusterIP → pod 8001
├── finance-social-deployment.yaml
├── finance-social-service.yaml          # ClusterIP → pod 8003
├── finance-configmap.yaml               # EXPERIMENT_MODE setting
│
├── # ── Container / local run ────────────────────────────────────────
├── Dockerfile                           # finance-api image (Python 3.12, installs requirements)
├── docker-compose.yaml                  # Local alternative to Kubernetes
├── deploy.sh                            # Full Minikube deploy automation script
├── requirements.txt                     # Python dependencies
├── logger.py                            # Structured logging + trace_step context manager
│
├── # ── Benchmark scripts ────────────────────────────────────────────
├── benchmark.py                         # BASELINE vs OPTIMIZED comparison (36 runs)
├── benchmark_page.py                    # Generates benchmark_01_*.png – benchmark_06_*.png
│
└── Readme.md                            # This file
```

---

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Python | 3.12+ | |
| Docker | 24+ | Must be running |
| Minikube | 1.32+ | `brew install minikube` |
| kubectl | 1.28+ | `brew install kubectl` |
| Alpha Vantage API key | — | [Free tier](https://www.alphavantage.co/support/#api-key): 25 req/day |

Optional for social sentiment:
- Twitter/X Bearer Token (free developer account)

---

## Quick Start

### 1. Clone and configure

```bash
git clone <repo-url>
export ALPHA_VANTAGE_API_KEY=your_key_here
# optional:
export TWITTER_BEARER_TOKEN=your_token_here
```

### 2. Deploy to Minikube (fully automated)

```bash
python3 -m venv iisc

source iisc/bin/activate

minikube delete

minikube start --memory=4096

pip install -r requirements.txt

chmod +x deploy.sh
./deploy.sh

kubectl port-forward service/finance-api-service 8080:80 &

python ./benchmark.py --url http://localhost:8080
```

This script:
- Starts Minikube if not running
- Switches Docker daemon to Minikube's environment
- Builds all four images inside Minikube
- Creates Kubernetes Secrets for API keys
- Applies all manifests
- Monitors rollout status

### 3. Access the API

```bash
# Recommended — stable localhost URL
kubectl port-forward service/finance-api-service 8080:8000

# Test it
curl -X POST http://localhost:8080/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "Summarize recent SEC filing for AAPL."}'
```

### 4. Run locally with Docker Compose (no Kubernetes)

```bash
docker-compose up --build
# API available at http://localhost:8000
```

---

## Services

### finance-api

The core service. Hosts the FastAPI application and runs the full LangGraph pipeline. Exposes a single `POST /analyze` endpoint.

```bash
kubectl exec -it deployment/finance-api -- bash
```

Resource limits: `memory: 2Gi`, `cpu: 500m`

### finance-market

Wraps the Alpha Vantage `TIME_SERIES_DAILY` endpoint as an MCP server. Returns the most recent trading day's OHLCV data for a given ticker.

```bash
# Direct test (from inside cluster)
curl -X POST http://finance-market:8003/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "fetch_market_data", "arguments": {"ticker": "AAPL"}}, "id": "1"}'
```

**Rate limit:** Free tier = 25 req/day, 5 req/min. No retry/backoff is implemented — silent failures will occur beyond the daily cap.

### finance-sec

Wraps the SEC EDGAR public REST API. Resolves ticker → CIK → filing metadata. Returns up to 5 recent 10-K/10-Q filings. No API key required.

### finance-social

Social sentiment MCP server. Behavior depends on whether a Twitter/X Bearer Token is configured:

- **With token:** Queries recent tweets via Twitter/X API v2, scores with VADER, returns aggregate sentiment.
- **Without token:** Returns a graceful degradation message. The `not_placeholder` validation check in `validate_node` ensures this no-data string cannot pass through as grounding evidence.

---

## Pipeline Design

The LangGraph pipeline runs 11 nodes in sequence. Each node either enriches the `AgentState` or sets a `block_reason` that causes all downstream nodes to skip.

```
intent_node → fetch_node → validate_node → store_node → retrieve_node
→ ticker_guard_node → evaluate_node → answer_node
→ analyst_node → reflection_node → scribe_node
```

### Guard nodes

| Node | Block reason | What it catches |
|---|---|---|
| `intent_node` | `BLOCKED_ADVISORY_QUERY` | Investment advice keywords: buy, sell, predict, overvalued, should i… |
| `fetch_node` | `BLOCKED_UNKNOWN_ENTITY` | Tickers/companies not in `ENTITY_REGISTRY` (AAPL, MSFT, TSLA, NVDA) |
| `fetch_node` | `BLOCKED_UNSUPPORTED_DOCUMENT_YEAR` | Years outside `[2022, 2023, 2024]` |
| `validate_node` | `BLOCKED_INVALID_TOOL_OUTPUT` | MCP responses failing any of 4 quality checks |
| `ticker_guard_node` | `BLOCKED_TICKER_MISMATCH` | Retrieved docs that don't mention the queried ticker |
| `evaluate_node` | `BLOCKED_LOW_SIMILARITY` | Cosine similarity below `SIMILARITY_THRESHOLD` (0.55) |

### Agents

**AnalystAgent** (`agents/analyst.py`) — runs `ProsusAI/finbert` on the assembled answer to produce a sentiment label (`positive` / `negative` / `neutral`) and confidence score. Loaded once at startup as a singleton.

**ReflectionAgent** (`agents/reflection.py`) — compares FinBERT confidence against `CONFIDENCE_THRESHOLD` (0.70). Routes to `scribe_node` if confidence ≥ threshold, otherwise terminates (`report = None`).

**ScribeAgent** (`agents/scribe.py`) — formats a structured Financial Report from the sentiment output.

### AgentState schema

```python
class AgentState(TypedDict):
    query:          str                 # Original user query
    intent_blocked: bool                # True if advisory keywords detected
    block_reason:   Optional[str]       # Reason code if pipeline halted
    fetched_data:   Dict[str, str]      # Raw MCP responses keyed by source
    retrieved_docs: List[str]           # Docs retrieved from ChromaDB
    answer:         str                 # Final answer text
    threshold:      float               # FinBERT confidence gate (default 0.70)
    sentiment:      Optional[Dict]      # {label, confidence} from FinBERT
    proceed:        Optional[bool]      # Set by ReflectionAgent
    report:         Optional[str]       # Final report from ScribeAgent
```

---

## API Reference

### POST /analyze

```bash
curl -X POST http://localhost:8080/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "What is AAPL stock price?"}'
```

**Request body:**

```json
{ "query": "string" }
```

**Response:**

```json
{
  "answer": "AAPL (2026-04-01) — Open: $174.23, High: $176.01, Low: $173.88, Close: $175.42, Volume: 52341200",
  "grounded": true,
  "hallucination_rate": 0.0,
  "faithfulness_score": 1.0,
  "block_reason": null,
  "tools_used": ["market", "sec", "social"],
  "sentiment": {
    "label": "neutral",
    "confidence": 0.931
  },
  "report": "\nFinancial Report:\n\nSentiment: neutral\nConfidence: 0.931\n"
}
```

**Blocked response example:**

```json
{
  "answer": "INSUFFICIENT_EVIDENCE",
  "grounded": false,
  "hallucination_rate": 0.0,
  "faithfulness_score": null,
  "block_reason": "BLOCKED_ADVISORY_QUERY",
  "tools_used": [],
  "sentiment": null,
  "report": null
}
```

| Field | Type | Description |
|---|---|---|
| `answer` | string | Retrieved document text or `INSUFFICIENT_EVIDENCE` |
| `grounded` | boolean | True if answer is not `INSUFFICIENT_EVIDENCE` |
| `hallucination_rate` | float | Sentence-overlap score — 0.0 = fully grounded |
| `faithfulness_score` | float \| null | 1.0 = fully faithful; null if blocked |
| `block_reason` | string \| null | Guard that halted the pipeline |
| `tools_used` | string[] | MCP sources that returned valid data |
| `sentiment` | object \| null | FinBERT result: `{label, confidence}` |
| `report` | string \| null | ScribeAgent report; null if confidence < threshold |

---

## Configuration

All runtime configuration is managed through Kubernetes ConfigMaps and Secrets.

| Variable | Source | Default | Description |
|---|---|---|---|
| `EXPERIMENT_MODE` | ConfigMap `finance-config` | `OPTIMIZED` | `OPTIMIZED` = RAG + agents, `BASELINE` = plain LLM |
| `MCP_MARKET_URL` | Deployment env | `http://finance-market:8003/mcp` | Market data MCP endpoint |
| `MCP_SEC_URL` | Deployment env | `http://finance-sec:8001/mcp` | SEC filings MCP endpoint |
| `MCP_SOCIAL_URL` | Deployment env | `http://finance-social:8003/mcp` | Social sentiment MCP endpoint |
| `ALPHA_VANTAGE_API_KEY` | Secret `alpha-vantage-secret` | — | Required for market data |
| `TWITTER_BEARER_TOKEN` | Secret (optional) | — | Required for live social sentiment |
| `CONFIDENCE_THRESHOLD` | `main.py` constant | `0.70` | FinBERT minimum confidence for report generation |
| `SIMILARITY_THRESHOLD` | `main.py` constant | `0.55` | ChromaDB minimum cosine similarity to accept a document |

To switch the running pipeline to BASELINE mode:

```bash
kubectl edit configmap finance-config
# change EXPERIMENT_MODE to BASELINE
kubectl rollout restart deployment/finance-api
```

---

## Testing


```bash
# Start the API first

kubectl port-forward service/finance-api-service 8080:80 &

```

## Benchmarking

Compares `BASELINE` (plain TinyLlama, no retrieval) against `OPTIMIZED` (RAG + agentic pipeline) across hallucination rate, faithfulness, grounded rate, and latency.

```bash
# Against live API (recommended — tests guard chain)
python benchmark.py --url http://localhost:8080

# In-process (bypasses guards — metrics are misleading for blocking behaviour)
python benchmark.py
```

> **Important:** Always use `--url` when benchmarking guard behaviour. The in-process runner bypasses `intent_node`, `fetch_node`, and other API guards entirely.

---

## Deployment

### Full deploy (automated)

```bash
export ALPHA_VANTAGE_API_KEY=your_key_here
./deploy.sh
```

### Manual steps

```bash
# 1. Point Docker to Minikube
eval $(minikube docker-env)

# 2. Build images
docker build -t finance-api:v2 .
docker build -f mcp_servers/Dockerfile.market -t finance-market:v1 .
docker build -f mcp_servers/Dockerfile.sec    -t finance-sec:v1 .
docker build -f mcp_servers/Dockerfile.social -t finance-social-mcp:v1 .

# 3. Create secrets
kubectl create secret generic alpha-vantage-secret \
  --from-literal=ALPHA_VANTAGE_API_KEY=$ALPHA_VANTAGE_API_KEY

# 4. Apply manifests
kubectl apply -f finance-configmap.yaml
kubectl apply -f finance-api-deployment.yaml
kubectl apply -f finance-api-service.yaml
kubectl apply -f finance-market-deployment.yaml
kubectl apply -f finance-market-service.yaml
kubectl apply -f finance-sec-deployment.yaml
kubectl apply -f finance-sec-service.yaml
kubectl apply -f finance-social-deployment.yaml
kubectl apply -f finance-social-service.yaml

# 5. Check status
kubectl get pods
kubectl rollout status deployment/finance-api
```

### Access on macOS (Docker driver)

The NodePort is not directly accessible on macOS with the Docker driver. Use port-forward instead:

```bash
kubectl port-forward service/finance-api-service 8080:8000
# API now at http://localhost:8080
```

### Teardown

```bash
kubectl delete -f .
minikube stop
```

---

---

## Technology Stack

| Component | Technology |
|---|---|
| API framework | FastAPI 0.110+ |
| Pipeline orchestration | LangGraph 0.1+ |
| Vector store | ChromaDB 0.5+ (persistent) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (384-dim) |
| Sentiment model | `ProsusAI/finbert` |
| LLM (baseline mode) | `TinyLlama/TinyLlama-1.1B-Chat-v1.0` |
| Data protocol | MCP (Model Context Protocol) JSON-RPC 2.0 |
| Market data | Alpha Vantage API |
| SEC data | SEC EDGAR public REST API |
| Deployment | Kubernetes / Minikube |
| Containerisation | Docker |

---

## Data Sources

All external data is fetched live at query time — there is no pre-built static corpus.

| Source | Server | Auth required | Volume per query |
|---|---|---|---|
| Stock market OHLCV | `finance-market` | Alpha Vantage API key | 1 record (most recent trading day) |
| SEC EDGAR filings | `finance-sec` | None | Up to 5 recent 10-K/10-Q filings |
| Social sentiment | `finance-social` | Twitter/X Bearer Token (optional) | Up to 20 tweets per ticker |

Supported tickers (`ENTITY_REGISTRY`): `AAPL`, `MSFT`, `TSLA`, `NVDA`

Supported document years: `2022`, `2023`, `2024`
