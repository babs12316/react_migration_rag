# React 19 Migration Agent — Backend

A production-grade async migration pipeline that automatically migrates React codebases to React 19. Uses AST-based static analysis to detect deprecated patterns and an LLM to rewrite components based on declarative migration rules.

---

## Overview

Migrating a large React codebase to React 19 involves many mechanical but error-prone changes: replacing `forwardRef`, removing `propTypes`, updating `ReactDOM.render`, migrating legacy context APIs, and more. This service automates that process by:

1. **Auditing** uploaded `.tsx` files using Tree-sitter AST analysis to detect React 19 violations
2. **Rewriting** components using an LLM guided by `migration_rules.yaml`
3. **Storing** original and migrated files in S3
4. **Tracking** job progress asynchronously so the frontend can poll for updates

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 (managed with `uv`) |
| API | FastAPI |
| AST Analysis | Tree-sitter |
| LLM | Groq (llama3-70b-8192) |
| File Storage | AWS S3 (LocalStack locally) |
| Infrastructure | Terraform |
| Frontend | React 19, Vite, Tailwind CSS, Zustand |

---

## Project Structure
```
react-migration-agent/
├── api/
│   ├── main.py              # FastAPI app + CORS
│   ├── job_store.py         # In-memory async job tracking
│   ├── migration.py         # Migration pipeline
│   ├── s3_client.py         # boto3 S3 client (LocalStack/AWS)
│   └── routes/
│       ├── upload.py        # POST /upload
│       ├── migrate.py       # POST /migrate/{job_id}
│       ├── status.py        # GET /status/{job_id}
│       ├── results.py       # GET /results/{job_id}
│       └── download.py      # GET /download/{job_id}/{filename}
├── frontend/                # React 19 frontend
├── terraform/               # Infrastructure as code
├── migration/               # Sample .tsx files for testing
├── auditor.py               # Tree-sitter AST scanner
├── refactor_agent.py        # LLM + migration tools
├── migration_rules.yaml     # Declarative React 19 migration rules
├── pyproject.toml
└── uv.lock
```

---

## Architecture
```
User uploads .tsx files
        │
        ▼
POST /upload → files stored in S3 (uploads bucket) → job_id returned
        │
        ▼
POST /migrate/{job_id} → background pipeline starts → returns immediately
        │
        ▼
For each file:
  1. Download from S3
  2. AST audit (Tree-sitter) → detect React 19 violations
  3. If issues found → fetch rules from migration_rules.yaml
  4. LLM rewrites the code
  5. Migrated file uploaded to S3 (results bucket)
  6. Job state updated
        │
        ▼
GET /status/{job_id} → frontend polls every 2 seconds
        │
        ▼
GET /results/{job_id} → full results when complete
        │
        ▼
GET /download/{job_id}/{filename} → fetch migrated file from S3
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/) for dependency management
- [LocalStack](https://localstack.cloud/) for local AWS simulation
- [Terraform](https://terraform.io/) for infrastructure provisioning
- [Groq API key](https://console.groq.com/)

### 1. Install dependencies
```bash
uv sync
```

### 2. Configure environment

Create a `.env` file in the project root:
```env
GROQ_API_KEY=your_groq_api_key

# LocalStack (local dev only — remove for production)
AWS_ENDPOINT_URL=http://localhost:4566
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
```

### 3. Start LocalStack
```bash
localstack start
```

### 4. Provision S3 buckets with Terraform
```bash
cd terraform
terraform init
terraform apply
```

This creates three S3 buckets:
- `migration-upload` — stores uploaded `.tsx` files
- `migration-results` — stores migrated output files
- `migration-frontend` — serves the React frontend

### 5. Start the API
```bash
uvicorn api.main:app --reload
```

API available at `http://localhost:8000`.
Interactive docs at `http://localhost:8000/docs`.

---

## API Endpoints

### `POST /upload`
Upload `.tsx` files for migration.

**Request:** `multipart/form-data` with one or more `.tsx` files

**Response:**
```json
{
    "job_id": "a1b2c3d4",
    "files_uploaded": 3,
    "filenames": ["Button.tsx", "Input.tsx", "Form.tsx"]
}
```

---

### `POST /migrate/{job_id}`
Trigger the migration pipeline for a job.

**Response:**
```json
{
    "job_id": "a1b2c3d4",
    "status": "queued",
    "files": 3,
    "message": "Migration started. Poll /status/a1b2c3d4 for progress."
}
```

---

### `GET /status/{job_id}`
Poll migration progress.

**Response:**
```json
{
    "job_id": "a1b2c3d4",
    "status": "running",
    "total_files": 3,
    "processed": 1,
    "progress_percent": 33
}
```

---

### `GET /results/{job_id}`
Get full results once migration is complete.

**Response:**
```json
{
    "job_id": "a1b2c3d4",
    "status": "complete",
    "total_files": 3,
    "migrated": 2,
    "skipped": 1,
    "results": [
        {
            "file": "Button.tsx",
            "issues_found": ["R19-REF-001"],
            "migrated": true
        },
        {
            "file": "Input.tsx",
            "issues_found": [],
            "migrated": false
        }
    ],
    "errors": []
}
```

---

### `GET /download/{job_id}/{filename}`
Download a migrated file from S3.

Returns the migrated file as a downloadable attachment.

---

## Migration Rules

`migration_rules.yaml` is the source of truth for what constitutes a valid React 19 migration. Both the auditor and refactor agent read from this file.

| Rule ID | Pattern | Description |
|---|---|---|
| R19-REF-001 | `forwardRef` | Replace with ref as standard prop |
| R19-REF-002 | `element.ref` | Replace with `element.props.ref` |
| R19-REF-003 | `MutableRefObject` | Replace with `RefObject` |
| R19-REF-004 | `this.refs` | Replace with `useRef` |
| R19-DOM-001 | `render` | Replace `ReactDOM.render` with `createRoot` |
| R19-DOM-002 | `hydrate` | Replace with `hydrateRoot` |
| R19-DOM-003 | `unmountComponentAtNode` | Replace with `root.unmount()` |
| R19-DOM-004 | `findDOMNode` | Replace with `useRef` |
| R19-TYPES-001 | `propTypes` | Migrate to TypeScript interface |
| R19-TYPES-002 | `defaultProps` | Replace with ES6 default parameters |
| R19-CTX-001 | `contextTypes` | Migrate to `React.createContext()` |
| R19-CTX-002 | `getChildContext` | Migrate to `Context.Provider` |
| R19-DEP-001 | `createFactory` | Replace with JSX |
| R19-TS-002 | `useRef` | Add argument `useRef(undefined)` |

---

## Frontend

The React 19 frontend is built with Vite, Tailwind CSS, and Zustand.

### Run locally
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

### Deploy to LocalStack S3
```bash
cd frontend
npm run build
awslocal s3 sync dist/ s3://migration-frontend --delete
```

Open `http://localhost:4566/migration-frontend/index.html`.

---

## Testing with curl
```bash
# 1. upload
curl -X POST http://localhost:8000/upload/ \
  -F "files=@migration/R19-REF-001-forwardRef.tsx"

# 2. migrate (replace {job_id} with value from step 1)
curl -X POST http://localhost:8000/migrate/{job_id}

# 3. poll status
curl http://localhost:8000/status/{job_id}

# 4. results
curl http://localhost:8000/results/{job_id}

# 5. download migrated file
curl http://localhost:8000/download/{job_id}/R19-REF-001-forwardRef.tsx
```

---

## Development

### Add dependencies
```bash
uv add <package>
```

### Run with auto-reload
```bash
uvicorn api.main:app --reload
```

---

## Deployment

Terraform configuration is in `terraform/` for deploying to real AWS.
```bash
cd terraform
terraform init
terraform apply -var-file="terraform.prod.tfvars"
```

For production, set credentials via environment variables — never in files:
```bash
export AWS_ACCESS_KEY_ID=your_real_key
export AWS_SECRET_ACCESS_KEY=your_real_secret
```