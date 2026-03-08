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

@tool("audit_code_file")
def audit_code_file(file_path: str) -> List[Dict]:
    """Scans a file for React 19 compatibility issues using Tree-sitter AST."""
    return run_audit(file_path)


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

tools = [audit_code_file, get_migration_rules, write_final_file]

SYSTEM_PROMPT = (
    "You are a React 19 Migration Expert. You follow a strict 3-step loop:\n"
    "1. AUDIT: Use audit_code_file.\n"
    "2. LEARN: Use get_migration_rules with the ID found.\n"
    "3. COMMIT: Use write_final_file to save the new code to disk.\n\n"
    "CRITICAL: Never just chat the code. You MUST call write_final_file with the full code. "
    "Maintain the .tsx extension for all React components."
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
    if os.path.exists("Button.tsx"):
        run_migration_agent("Button.tsx")
    else:
        print("Missing Button.tsx! Please create the file first.")
