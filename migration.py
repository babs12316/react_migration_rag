from langchain_core.messages import HumanMessage
from s3_client import download_file, upload_migrated_file
import job_store
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from auditor import run_audit
import yaml
import asyncio

llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)

CHROMA_DIR = "api/chroma_db"
COLLECTION = "react19_docs"

# load vectorstore once at module level
vectorstore = Chroma(
    collection_name=COLLECTION,
    persist_directory=CHROMA_DIR,
    embedding_function=HuggingFaceEmbeddings(),
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})


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
    job_store.set_running(job_id)

    for filename in filenames:
        try:
            content_bytes = download_file(job_id, filename)
            issues = run_audit(content_bytes, filename)

            if not issues:
                job_store.record_file_result(job_id, filename, [], False)
                await asyncio.sleep(0)  # ← yield control back to FastAPI
                continue

            issue_ids = [i["id"] for i in issues]
            rules = _load_rules(issue_ids)
            rag_context = get_rag_context(issues)

            original_code = content_bytes.decode("utf-8")
            migrated_code = _rewrite_code(original_code, issues, rules, rag_context)

            upload_migrated_file(job_id, filename, migrated_code)
            job_store.record_file_result(job_id, filename, issue_ids, True)
            await asyncio.sleep(0)  # ← yield control back to FastAPI

        except Exception as e:
            job_store.record_error(job_id, filename, str(e))
            await asyncio.sleep(0)  # ← yield control back to FastAPI

    job_store.set_complete(job_id)
