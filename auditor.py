import yaml
import tree_sitter_language_pack as ts_pack
from tree_sitter import Parser, Query  # Import Query directly


def run_audit(source_code: bytes, filename: str = "unknown"):
    with open("migration_rules.yaml", "r") as f:
        rules_data = yaml.safe_load(f)  # converts rules to Python dictionary and copies
        print(f"rules_data is {rules_data}")


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

        start = 0
        found_real_code = False

        while True:
            index = source_code.find(pattern, start)
            if index == -1:
                break  # pattern not found anywhere, move to next rule

            node = tree.root_node.descendant_for_byte_range(index, index + len(pattern))
            print(
                f"  PATTERN: {pattern} | INDEX: {index} | NODE TYPE: {node.type} | PARENT: {node.parent.type if node.parent else 'None'}")

            if node.type not in ["comment", "string", "string_fragment"]:
                found_real_code = True
                break  # found real code, stop searching this pattern

            start = index + 1  # this occurrence was a comment/string, skip past it and keep looking

        if found_real_code:
            findings.append({
                "id": rule['id'],
                "message": rule['description'],
                "file": filename
            })

    return findings


if __name__ == "__main__":
    with open("Button.tsx", "rb") as f:
        source_code = f.read()
    results = run_audit(source_code, "Button.tsx")
    if results:
        print("🔍 AUDIT COMPLETED: ISSUES FOUND")
        for issue in results:
            print(f"[{issue['id']}] {issue['message']} in {issue['file']}")
    else:
        print("✅ AUDIT COMPLETED: NO ISSUES FOUND")
