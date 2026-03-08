import yaml
import tree_sitter_language_pack as ts_pack
from tree_sitter import Parser, Query  # Import Query directly


def run_audit(file_to_scan):
    with open("migration_rules.yaml", "r") as f:
        rules_data = yaml.safe_load(f)  # converts rules to Python dictionary and copies
        print(f"rules_data is {rules_data}")
    with open(file_to_scan, "rb") as f:
        source_code = f.read()  # One big string
        print(f"source code {source_code}")

    # Use the parser just to get the tree
    tsx_lang = ts_pack.get_language("tsx")
    print(f"tsx_lang is {tsx_lang}")
    parser = Parser(tsx_lang)
    print(f"parser is {parser}")
    tree = parser.parse(source_code)
    print(f"tree is {tree}")

    findings = []
    for rule in rules_data['rules']:
        pattern = rule['pattern'].encode()
        print(f"pattern is {pattern}")
        start_index = source_code.find(pattern)

        if start_index != -1:
            # Check the AST: Is this specific spot a 'comment' or 'string'?
            node = tree.root_node.descendant_for_byte_range(start_index, start_index + len(pattern))
            print(f"node is {node}")

            # If the node type is an identifier or call_expression, it's REAL code.
            if node.type not in ["comment", "string", "string_fragment"]:
                findings.append({
                    "id": rule['id'],
                    "message": rule['description'],
                    "file": file_to_scan
                })
    return findings


if __name__ == "__main__":
    results = run_audit("Button.tsx")
    if results:
        print("🔍 AUDIT COMPLETED: ISSUES FOUND")
        for issue in results:
            print(f"[{issue['id']}] {issue['message']} in {issue['file']}")
    else:
        print("✅ AUDIT COMPLETED: NO ISSUES FOUND")
