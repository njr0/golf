import json

def load(path):
    """
    Reads JSONL (new-line separated Python dicts with common keys) from path.
    Returns list of dictionaries.
    """
    with open(path) as f:
        for line in f.readlines():
            if line.strip():
                yield json.loads(line)
