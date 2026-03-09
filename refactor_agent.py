import os
from typing import List, Dict
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_groq import ChatGroq
import yaml

from auditor import run_audit

load_dotenv()


# --- 1. TOOLS ---

@tool("find_tsx_files")
def find_tsx_files(directory: str) -> List[str]:
    """Scans a directory recursively and returns all .tsx file paths.
    Skips node_modules, build, dist and .next folders."""
    tsx_files = []

    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in ['node_modules', 'build', 'dist', '.next']]

        for file in files:
            if file.endswith(".tsx"):
                tsx_files.append(os.path.join(root, file))

    return tsx_files


@tool("read_file")
def read_file(file_path: str) -> str:
    """Reads the full source code of a file and returns it as a string."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"ERROR: File not found: {file_path}"


@tool("audit_code_file")
def audit_code_file(file_path: str) -> str:
    """Scans a file for React 19 compatibility issues using Tree-sitter AST."""
    findings = run_audit(file_path)

    if not findings:
        return "NO_ISSUES_FOUND: This file is already React 19 compliant."

    # Convert list to string — Groq requires string responses
    result = ""
    for f in findings:
        result += f"Issue ID: {f['id']} | Message: {f['message']} | File: {f['file']}\n"

    return result.strip()


@tool("get_migration_rules")
def get_migration_rules(issue_id: str) -> str:
    """Fetches the specific React 19 fix for a given rule ID from the YAML rulebook."""

    with open("migration_rules.yaml", "r") as f:
        rules_data = yaml.safe_load(f)

    for rule in rules_data['rules']:
        if rule['id'] == issue_id:
            return (
                f"Rule ID: {rule['id']}. "
                f"Description: {rule['description']}. "
                f"Pattern to fix: {rule['pattern']}."
            )

    return "Standard React 19 migration: pass ref as a prop to the function."


@tool("write_final_file")
def write_final_file(file_path: str, new_code: str) -> str:
    """
    SAVES the code to disk.
    REQUIRED: 'new_code' must be the ACTUAL full source code string.
    The file will always be saved with the suffix '_migrated.tsx'.
    """

    # Clean the path and force the .tsx extension
    base_name = file_path.replace("_migrated.tsx", "").replace(".tsx", "")
    output_path = f"{base_name}_migrated.tsx"

    # Remove markdown fluff
    clean_code = new_code.strip().replace("```tsx", "").replace("```", "")

    with open(output_path, "w") as f:
        f.write(clean_code)

    return f"SUCCESS: File saved as {output_path}. You are finished."


# --- 2. AGENT CONFIGURATION ---

llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)

tools = [find_tsx_files, audit_code_file, get_migration_rules, read_file, write_final_file]

SYSTEM_PROMPT = (
    "You are a React 19 Migration Expert.\n\n"
    "WORKFLOW — follow this EXACT order for EVERY file:\n"
    "1. SCAN: Use find_tsx_files to get ALL files.\n"
    "2. For EACH file:\n"
    "   a. AUDIT: Use audit_code_file.\n"
    "   b. If NO_ISSUES_FOUND → move to next file immediately.\n"
    "   c. If issues found:\n"
    "      - READ: Use read_file to get the current source code.\n"
    "      - RULES: Use get_migration_rules for each issue ID.\n"
    "      - REWRITE: Fix the code based on the rules.\n"
    "      - SAVE: Use write_final_file with the corrected code.\n"
    "3. Process ALL files. Never stop early."
)
agent = create_agent(llm, tools, system_prompt=SYSTEM_PROMPT)


# --- 3. EXECUTION ENGINE ---

def run_migration_agent(target_file: str):
    print(f"🚀 Starting Migration Engine for: {target_file}")

    # First Pass
    result = agent.invoke({
        "messages": [{"role": "user", "content": f"Migrate {target_file} to React 19 and SAVE it using your tools."}]
    })

    # Trace Summary
    for msg in result["messages"]:
        msg.pretty_print()

    # Final Verification
    expected_file = target_file.replace(".tsx", "_migrated.tsx")
    if os.path.exists(expected_file):
        print(f"\n✨ SUCCESS: {expected_file} created on disk.")
    else:
        print(f"\n❌ ERROR: Agent failed to create {expected_file}.")


if __name__ == "__main__":
    run_migration_agent("./react18_files")
