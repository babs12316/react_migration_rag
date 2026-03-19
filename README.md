# React 19 Migration Agent — Backend

Async pipeline that migrates React codebases to React 19 using AST-based static analysis, RAG-augmented documentation retrieval, and LLM-powered code rewriting.

---

## How It Works
```
Upload .tsx files
      │
      ▼
AST audit (Tree-sitter) → detect React 19 violations
      │
      ▼
RAG retrieval (ChromaDB + Ollama) → fetch relevant React 19 docs
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
| LLM | Groq (llama3-70b-8192) |
| Embeddings | Ollama (nomic-embed-text) |
| Vector Store | ChromaDB |
| Storage | AWS S3 (LocalStack locally) |
| Infrastructure | Terraform |
| Frontend | React 19, Vite, Tailwind, Zustand |

---

## Project Structure
```
├── api/
│   ├── main.py              # FastAPI app
│   ├── migration.py         # Pipeline + RAG retrieval
│   ├── auditor.py           # Tree-sitter AST scanner
│   ├── job_store.py         # Async job tracking
│   ├── s3_client.py         # S3 client
│   └── routes/              # upload, migrate, status, results, download
├── frontend/                # React 19 frontend
├── terraform/               # Infrastructure as code
├── data/react_19_docs.txt   # Scraped React 19 docs
├── chroma_db/               # ChromaDB (auto-generated)
├── ingest.py                # One-time ingestion script
└── migration_rules.yaml     # 14 React 19 migration rules
```

---

## Getting Started

### Prerequisites (macOS)
```bash
brew install uv localstack ollama pipx hashicorp/tap/terraform
pipx install awscli-local
```

### Setup
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

# 5. start ollama + pull embedding model
ollama serve
ollama pull nomic-embed-text

# 6. ingest react 19 docs (one time only)
python ingest.py

# 7. start api
uvicorn api.main:app --reload
```

API at `http://localhost:8000` — docs at `http://localhost:8000/docs`.

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

## Frontend
```bash
# dev
cd frontend && npm run dev

# deploy to localstack s3
npm run build
awslocal s3 sync dist/ s3://react18_files-frontend --delete
open http://localhost:4566/migration-frontend/index.html
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