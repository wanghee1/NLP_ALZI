"""_extract_json 케이스별 동작 검증."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from src.rag.chain import _extract_json

CASES = [
    ('{"consultation": "ok", "grounds": []}', "bare JSON"),
    ('```json\n{"consultation": "ok", "grounds": []}\n```', "code fence json"),
    ('```JSON\n{"consultation": "ok", "grounds": []}\n```', "code fence JSON uppercase"),
    ('answer:\n\n```json\n{"consultation": "ok", "grounds": []}\n```\n', "preamble + fence"),
    ('here is the result\n{"consultation": "ok", "grounds": []}', "preamble no fence"),
]

all_pass = True
for raw, label in CASES:
    extracted = _extract_json(raw)
    try:
        d = json.loads(extracted)
        print(f"PASS [{label}] consultation={d.get('consultation')}")
    except Exception as e:
        print(f"FAIL [{label}] {e}")
        all_pass = False

print("\nRESULT:", "ALL PASS" if all_pass else "SOME FAILED")
sys.exit(0 if all_pass else 1)
