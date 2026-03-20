# React 19 Migration Agent — Backend

Async pipeline that migrates React codebases to React 19 using AST-based static analysis, RAG-augmented documentation retrieval, and LLM-powered code rewriting.

https://github.com/user-attachments/assets/36fbe3f5-84ac-4fe3-843a-4e805a66bd3d

---

## How It Works
```
Upload .tsx files
      │
      ▼
AST audit (Tree-sitter) → detect React 19 violations
      │
      ▼
RAG retrieval (ChromaDB + HuggingFace) → fetch relevant React 19 docs
      │
      ▼
LLM rewrite (Groq) → fix code using rules + docs context
      │
      ▼
Migrated files stored in S3 → download via API
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI (Python 3.12, `uv`) |
| AST Analysis | Tree-sitter |
| LLM | Groq (openai/gpt-oss-120b) |
| Embeddings | HuggingFace (all-mpnet-base-v2) |
| Vector Store | ChromaDB |
| Storage | AWS S3 (LocalStack locally) |
| Infrastructure | Terraform |

---

## Project Structure
```
├── api/
│   ├── main.py              # FastAPI app
│   └── routes/              # upload, migrate, status, results, download
├── auditor.py               # Tree-sitter AST scanner
├── migration.py             # Pipeline + RAG retrieval
├── job_store.py             # Async job tracking
├── s3_client.py             # S3 client
├── ingest.py                # One-time ingestion script
├── terraform/               # Infrastructure as code
├── data/                    # Scraped React 19 docs (auto-generated)
├── chroma_db/               # ChromaDB (auto-generated)
└── migration_rules.yaml     # 14 React 19 migration rules
```

---

## Getting Started

### Prerequisites (macOS)
```bash
brew install uv localstack pipx hashicorp/tap/terraform
pipx install awscli-local
```

### Quick Start (Docker)
```bash
# copy and configure environment
cp .env.example .env
# add your GROQ_API_KEY

# start everything
docker-compose up --build
```

API at `http://localhost:8000` — docs at `http://localhost:8000/docs`.

### Manual Setup
```bash
# 1. install dependencies
uv sync

# 2. configure environment
cp .env.example .env
# add your GROQ_API_KEY

# 3. start localstack
localstack start

# 4. provision s3 buckets
cd terraform && terraform init && terraform apply

# 5. ingest react 18 to 19 upgrade guid (one time only)
python ingest.py

# 6. start api
uvicorn api.main:app --reload
```

---

## API

| Method | Endpoint | Description |
|---|---|---|
| POST | `/upload` | Upload `.tsx` files, returns `job_id` |
| POST | `/migrate/{job_id}` | Trigger async migration pipeline |
| GET | `/status/{job_id}` | Poll progress |
| GET | `/results/{job_id}` | Full results when complete |
| GET | `/download/{job_id}/{filename}` | Download migrated file |

---

## Migration Rules

14 rules covering refs, ReactDOM APIs, PropTypes, context, and TypeScript patterns. See `migration_rules.yaml` for the full list.

---

## RAG Pipeline

React 19 documentation is scraped from [react.dev](https://react.dev/blog/2024/04/25/react-19-upgrade-guide), chunked, embedded with HuggingFace (`all-mpnet-base-v2`), and stored in ChromaDB.

At migration time, relevant documentation chunks are retrieved using semantic search and injected into the LLM prompt alongside the migration rules — giving the LLM richer context for accurate rewrites.

To refresh the documentation:
```bash
python ingest.py
```

---

## LocalStack Persistence

Add to `~/.zshrc` to persist data between restarts:
```bash
export LOCALSTACK_VOLUME_DIR=~/.localstack/volume
```

---

## Production Deployment
```bash
cd terraform
terraform apply -var-file="terraform.prod.tfvars"
```

Set real AWS credentials via environment variables — never in files.

---

## Related

- **Frontend**: [react_migration_rag_frontend](https://github.com/babs12316/react_migration_rag_frontend)
