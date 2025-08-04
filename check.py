import json

def get_changed_fields(before, after, path="", action=None):
    changes = []
    # Both dicts: recurse common keys
    if isinstance(before, dict) and isinstance(after, dict):
        for key in before.keys() & after.keys():
            new_path = f"{path}.{key}" if path else key
            changes += get_changed_fields(before[key], after[key], new_path, action)
    # Both lists: recurse each pair by index
    elif isinstance(before, list) and isinstance(after, list):
        min_len = min(len(before), len(after))
        for i in range(min_len):
            changes += get_changed_fields(before[i], after[i], f"{path}[{i}]", action)
    # Leaf: values differ
    else:
        if before != after:
            changes.append({
                "key": path,
                "before": before,
                "after": after,
                "action": action or "update"
            })
    return changes

# Example usage:
def highlight_changes(resource_changes):
    for rc in resource_changes:
        actions = rc["change"]["actions"]
        before = rc["change"].get("before", {})
        after = rc["change"].get("after", {})
        if actions != ["no-op"]:
            print(f"\nResource: {rc['address']} (Actions: {actions})")
            diffs = get_changed_fields(before, after, action="update" if "update" in actions else "replace")
            for diff in diffs:
                print(f"{diff['key']}: '{diff['before']}' → '{diff['after']}' (action: {diff['action']})")

# ---- Main ----
with open("plan.json") as f:
    data = json.load(f)
highlight_changes(data.get("resource_changes", []))
