import yaml
import asyncio
import os
from typing import Any
from groq import Groq
from langchain_core.messages import HumanMessage, AIMessage
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
import time
import hashlib

from langchain.agents.middleware import (
    ModelRetryMiddleware,
    ModelFallbackMiddleware,
    ModelCallLimitMiddleware,
    before_model,
    after_model,
    AgentState,
    hook_config,
)
from langgraph.runtime import Runtime
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from s3_client import download_file, upload_migrated_file
import job_store
from auditor import run_audit

# ─────────────────────────────────────────────
# ChromaDB
# ─────────────────────────────────────────────
CHROMA_DIR = "api/chroma_db"
COLLECTION = "react19_docs"

vectorstore = Chroma(
    collection_name=COLLECTION,
    persist_directory=CHROMA_DIR,
    embedding_function=HuggingFaceEmbeddings(),
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# ─────────────────────────────────────────────
# Context window — fetched dynamically from Groq
# ─────────────────────────────────────────────
PRIMARY_MODEL = "openai/gpt-oss-120b"
FALLBACK_MODEL = "groq/llama-3.3-70b-versatile"


def _get_context_window(model_id: str) -> int:
    """Fetch model context window from Groq API. Falls back to 131072 if unavailable."""
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        for model in client.models.list().data:
            if model.id == model_id:
                return model.context_window
    except Exception:
        pass
    return 131072


CONTEXT_WINDOW = _get_context_window(PRIMARY_MODEL)
MAX_PROMPT_CHARS = int(CONTEXT_WINDOW * 0.7) * 4  # 70% of tokens × 4 chars per token

# ─────────────────────────────────────────────
# Middleware constants
# ─────────────────────────────────────────────
INJECTION_PATTERNS = [
    "ignore previous instructions",
    "ignore all instructions",
    "system prompt",
    "acknowledge these",
    "before migrating please",
    "as a helpful assistant",
]

REFUSAL_PHRASES = [
    "i'm sorry",
    "i cannot",
    "i can't",
    "i am unable",
    "i must decline",
]

BLOCKED_SIGNAL = "BLOCKED: suspicious content detected"
REFUSED_SIGNAL = "REFUSED: llm declined to process"


# ─────────────────────────────────────────────
# Middleware hooks
# ─────────────────────────────────────────────
@before_model
@hook_config(can_jump_to=["end"])
def validate_input(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    last_message = state["messages"][-1].content

    # ── 1. Prompt length check ──
    if len(last_message) > MAX_PROMPT_CHARS:
        return {
            "messages": [AIMessage(
                f"BLOCKED: prompt too large ({len(last_message):,} chars). "
                f"Max allowed: {MAX_PROMPT_CHARS:,} chars. "
                f"Break your file into smaller components."
            )],
            "jump_to": "end"
        }

    # ── 2. Injection check ──
    if any(p in last_message.lower() for p in INJECTION_PATTERNS):
        return {
            "messages": [AIMessage(BLOCKED_SIGNAL)],
            "jump_to": "end"
        }

    return None


@after_model
@hook_config(can_jump_to=["end"])
def validate_output(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    last_message = state["messages"][-1].content.lower()

    if any(phrase in last_message for phrase in REFUSAL_PHRASES):
        return {
            "messages": [AIMessage(REFUSED_SIGNAL)],
            "jump_to": "end"
        }

    return None


# ─────────────────────────────────────────────
# Agent — no tools, just middleware
# ─────────────────────────────────────────────
rewrite_agent = create_agent(
    model=init_chat_model(PRIMARY_MODEL, model_provider="groq"),
    tools=[],
    middleware=[
        validate_input,
        validate_output,
        ModelRetryMiddleware(
            max_retries=3,
            backoff_factor=2.0,
            initial_delay=1.0,
        ),
        ModelFallbackMiddleware(init_chat_model("llama-3.3-70b-versatile", model_provider="groq")),
        ModelCallLimitMiddleware(run_limit=1),
    ],
)


# ─────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────
def get_rag_context(issues: list[dict]) -> str:
    """Retrieve relevant React 19 docs from ChromaDB for each issue."""
    docs = []
    for issue in issues:
        query = f"React 19 {issue['id']} {issue['message']}"
        results = retriever.invoke(query)
        docs.extend([doc.page_content for doc in results])
    seen = set()
    unique_docs = []
    for doc in docs:
        if doc not in seen:
            seen.add(doc)
            unique_docs.append(doc)
    return "\n\n".join(unique_docs)


def _load_rules(issue_ids: list[str]) -> str:
    """Fetch fix rules from YAML for given issue IDs."""
    with open("migration_rules.yaml", "r") as f:
        rules_data = yaml.safe_load(f)
    results = []
    for rule in rules_data["rules"]:
        if rule["id"] in issue_ids:
            results.append(
                f"Rule {rule['id']}: {rule['description']}\n"
                f"Fix: {rule['transformation_logic']}"
            )
    return "\n\n".join(results)


# in-memory cache — lives as long as server is running
_llm_cache: dict[str, str] = {}


def _cache_key(original_code: str) -> str:
    return hashlib.sha256(original_code.encode()).hexdigest()


def _rewrite_code(original_code: str, issues: list[dict], rules: str, rag_context: str) -> str:
    """
    Rewrite code using agent with middleware:
    - validate_input  → length + injection check before LLM
    - validate_output → refusal detection after LLM
    - ModelRetryMiddleware → auto retry on 503/timeout
    - ModelFallbackMiddleware → switch to fallback model if primary fails
    - ModelCallLimitMiddleware → exactly 1 LLM call per rewrite
    """
    # ── check cache first ──
    key = _cache_key(original_code)
    if key in _llm_cache:
        print(f"Cache hit — skipping LLM call")
        return _llm_cache[key]

    issue_summary = "\n".join(f"- {i['id']}: {i['message']}" for i in issues)
    prompt = (
        f"Original code:\n{original_code}\n\n"
        f"Issues found:\n{issue_summary}\n\n"
        f"Fix rules:\n{rules}\n\n"
        f"React 19 documentation:\n{rag_context}\n\n"
        f"Return the fully corrected file. No explanation. No markdown fences."
    )

    result = rewrite_agent.invoke({"messages": [HumanMessage(content=prompt)]})
    last_message = result["messages"][-1].content

    # detect if agent was blocked or refused — raise so pipeline records as error
    if BLOCKED_SIGNAL in last_message or REFUSED_SIGNAL in last_message or "BLOCKED:" in last_message:
        raise ValueError(last_message)

    migrated_code = last_message.strip()

    # ── store in cache ──
    _llm_cache[key] = migrated_code
    print(f"Cache miss — stored result, cache size: {len(_llm_cache)}")

    return migrated_code


# ─────────────────────────────────────────────
# Pipeline
# ─────────────────────────────────────────────
async def _process_file(job_id: str, filename: str):
    """Process a single file asynchronously."""
    try:
        # ── 1. Download from S3 ──
        content_bytes = download_file(job_id, filename)

        # ── 2. AST audit ──
        issues = run_audit(content_bytes, filename)

        if not issues:
            job_store.record_file_result(job_id, filename, [], False)
            return

        # ── 3. Fetch rules + RAG context ──
        issue_ids = [i["id"] for i in issues]
        rules = _load_rules(issue_ids)
        rag_context = get_rag_context(issues)

        # ── 4. Rewrite — run in thread pool ──
        original_code = content_bytes.decode("utf-8")
        migrated_code = await asyncio.to_thread(
            _rewrite_code, original_code, issues, rules, rag_context
        )

        # ── 5. Upload to S3 ──
        upload_migrated_file(job_id, filename, migrated_code)

        # ── 6. Update job state ──
        job_store.record_file_result(job_id, filename, issue_ids, True)

    except Exception as e:
        job_store.record_error(job_id, filename, str(e))


async def run_migration_pipeline(job_id: str, filenames: list[str]):
    """
    Runs for each file in the job:
    1. Download bytes from S3
    2. AST audit — detect React 19 violations
    3. If no issues → mark as skipped, move to next file
    4. If issues found:
       a. Fetch fix rules from YAML
       b. Retrieve relevant React 19 docs from ChromaDB (RAG)
       c. Rewrite code with LLM in thread pool (parallel)
       d. Upload migrated file to S3 results bucket
    5. Update job state after each file
    """
    job_store.set_running(job_id)
    start = time.time()
    print("timer started")
    await asyncio.gather(*[_process_file(job_id, f) for f in filenames])
    elapsed = time.time() - start
    print(f"Migration completed in {elapsed:.2f}s for {len(filenames)} files")
    print(f"Average: {elapsed / len(filenames):.2f}s per file")
    job_store.set_complete(job_id)
