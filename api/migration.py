import os
from langchain_core.messages import HumanMessage
from api.s3_client import download_file, upload_migrated_file
from api import job_store
from auditor import run_audit
from refactor_agent import get_migration_rules, llm


def _rewrite_code(original_code: str, issues: list[dict]) -> str:
    """Send code to LLM for rewriting based on issues and rules."""
    issue_ids = [i["id"] for i in issues]
    rules = "\n\n".join(get_migration_rules.invoke(id) for id in issue_ids)
    issue_summary = "\n".join(f"- {i['id']}: {i['message']}" for i in issues)

    prompt = (
        f"Original code:\n{original_code}\n\n"
        f"Issues found:\n{issue_summary}\n\n"
        f"Fix rules:\n{rules}\n\n"
        f"Return the fully corrected file. No explanation. No markdown fences."
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()


async def run_migration_pipeline(job_id: str, filenames: list[str]):
    """
    Runs for each file in the job:
    1. Download bytes from S3
    2. AST audit
    3. If issues: fetch rules → rewrite with LLM → upload migrated file to S3
    4. Update job state throughout
    """
    job_store.set_running(job_id)

    for filename in filenames:
        try:
            # ── 1. Download from S3 ──
            content_bytes = download_file(job_id, filename)

            # ── 2. Audit — pass bytes directly, no temp file needed ──
            issues = run_audit(content_bytes, filename)

            if not issues:
                job_store.record_file_result(job_id, filename, [], False)
                continue

            # ── 3. Rewrite with LLM ──
            original_code = content_bytes.decode("utf-8")
            migrated_code = _rewrite_code(original_code, issues)

            # ── 4. Upload migrated file to S3 ──
            upload_migrated_file(job_id, filename, migrated_code)

            # ── 5. Update job state ──
            job_store.record_file_result(
                job_id,
                filename,
                [i["id"] for i in issues],
                True
            )

        except Exception as e:
            job_store.record_error(job_id, filename, str(e))

    job_store.set_complete(job_id)
