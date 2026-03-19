from langchain_core.messages import HumanMessage
from s3_client import download_file, upload_migrated_file
import job_store
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from auditor import run_audit
import yaml

llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)

CHROMA_DIR = "api/chroma_db"
COLLECTION = "react19_docs"
EMBED_MODEL = "nomic-embed-text"

# load vectorstore once at module level
vectorstore = Chroma(
    collection_name=COLLECTION,
    persist_directory=CHROMA_DIR,
    embedding_function=HuggingFaceEmbeddings(),
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

"""
def get_migration_rules(issue_id: str) -> str:
   
    with open("migration_rules.yaml", "r") as f:
        rules_data = yaml.safe_load(f)

    for rule in rules_data['rules']:
        if rule['id'] == issue_id:
            return (
                f"Rule ID: {rule['id']}. "
                f"Description: {rule['description']}. "
                f"Pattern to fix: {rule['pattern']}."
            )

    return "Standard React 19 react18_files: pass ref as a prop to the function."
"""

def get_rag_context(issues: list[dict]) -> str:
    """Retrieve relevant React 19 docs from ChromaDB for each issue."""
    docs = []
    for issue in issues:
        query = f"React 19 {issue['id']} {issue['message']}"
        results = retriever.invoke(query)
        docs.extend([doc.page_content for doc in results])
    # deduplicate
    seen = set()
    unique_docs = []
    for doc in docs:
        if doc not in seen:
            seen.add(doc)
            unique_docs.append(doc)
    return "\n\n".join(unique_docs)


def _rewrite_code(original_code: str, issues: list[dict], rules: str, rag_context: str) -> str:
    issue_summary = "\n".join(f"- {i['id']}: {i['message']}" for i in issues)
    prompt = (
        f"Original code:\n{original_code}\n\n"
        f"Issues found:\n{issue_summary}\n\n"
        f"Fix rules:\n{rules}\n\n"
        f"React 19 documentation:\n{rag_context}\n\n"
        f"Return the fully corrected file. No explanation. No markdown fences."
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()


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

async def run_migration_pipeline(job_id: str, filenames: list[str]):
    """
     Runs for each file in the job:
     1. Download bytes from S3
     2. AST audit — detect React 19 violations
     3. If no issues → mark as skipped, move to next file
     4. If issues found:
        a. Fetch fix rules from YAML
        b. Retrieve relevant React 19 docs from ChromaDB (RAG)
        c. Rewrite code with LLM using rules + RAG context
        d. Upload migrated file to S3 results bucket
     5. Update job state after each file
     """

    job_store.set_running(job_id)

    for filename in filenames:
        try:
            # ── 1. Download from S3 ──
            content_bytes = download_file(job_id, filename)

            # ── 2. Audit ──
            issues = run_audit(content_bytes, filename)

            if not issues:
                job_store.record_file_result(job_id, filename, [], False)
                continue

            # ── 3. Fetch rules + RAG context ──
            issue_ids = [i["id"] for i in issues]
            rules = _load_rules(issue_ids)
            rag_context = get_rag_context(issues)

            # ── 4. Rewrite with LLM ──
            original_code = content_bytes.decode("utf-8")
            migrated_code = _rewrite_code(original_code, issues, rules, rag_context)

            # ── 5. Upload migrated file to S3 ──
            upload_migrated_file(job_id, filename, migrated_code)

            # ── 6. Update job state ──
            job_store.record_file_result(
                job_id,
                filename,
                issue_ids,
                True
            )

        except Exception as e:
            job_store.record_error(job_id, filename, str(e))

    job_store.set_complete(job_id)
