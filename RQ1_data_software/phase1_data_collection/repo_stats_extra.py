import json
import re


def load_possibly_broken_json(path):
    """Load a JSON file that may contain either:
    - a single JSON array, or
    - many JSON objects separated by newlines or commas (imperfect output from other scripts).

    Returns a Python list of objects.
    """
    with open(path, 'r') as f:
        text = f.read()

    # Try normal load first
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
        # If it's a single object, wrap in list
        return [data]
    except json.JSONDecodeError:
        pass

    objs = []
    # Try line-oriented parsing (NDJSON / one JSON object per line, possibly trailing commas)
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Remove trailing commas from objects written with a trailing comma
        if line.endswith(','):
            line = line[:-1].rstrip()
        try:
            objs.append(json.loads(line))
            continue
        except json.JSONDecodeError:
            pass

    if objs:
        return objs

    # Fallback: find {...} blocks using a simple regex (non-greedy) and parse them
    for m in re.finditer(r"\{.*?\}", text, re.DOTALL):
        chunk = m.group(0)
        try:
            objs.append(json.loads(chunk))
        except json.JSONDecodeError:
            continue

    return objs


repo_data = load_possibly_broken_json('data/repo_stats.json')

python_repos = []
cpp_repos = []
both_repos = []
for r in repo_data:
    # defensive access and coerce to int if possible
    cpp_count = int(r.get('cpp', 0) or 0)
    py_count = int(r.get('py', 0) or 0)

    if cpp_count == 0 and py_count == 0:
        print('both are 0')
    if cpp_count == 0 and py_count != 0:
        python_repos.append(r)
    if cpp_count != 0 and py_count == 0:
        cpp_repos.append(r)
    if cpp_count != 0 and py_count != 0:
        both_repos.append(r)

print(len(python_repos))
print(len(cpp_repos))
print(len(both_repos))

# Write valid JSON arrays (overwrite mode)
with open('data/python_repo_stats.json', 'w') as outfile:
    json.dump(python_repos, outfile, indent=2)

with open('data/cpp_repo_stats.json', 'w') as outfile:
    json.dump(cpp_repos, outfile, indent=2)

with open('data/both_repo_stats.json', 'w') as outfile:
    json.dump(both_repos, outfile, indent=2)

