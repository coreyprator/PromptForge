from jsonschema import Draft202012Validator
import json, sys, pathlib

SCHEMA_PATH = pathlib.Path("v2/schemas/channel_a_v1.json")
PAYLOAD_PATH = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else None

if not PAYLOAD_PATH or not PAYLOAD_PATH.exists():
    print("Usage: validate_channel_a.py <payload.json>")
    raise SystemExit(2)

schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
validator = Draft202012Validator(schema)

payload = json.loads(PAYLOAD_PATH.read_text(encoding="utf-8"))
errors = sorted(validator.iter_errors(payload), key=lambda e: e.path)

if errors:
    print("SCHEMA: FAIL")
    for e in errors:
        loc = "/".join([str(p) for p in e.path]) or "(root)"
        print(f"- {loc}: {e.message}")
    raise SystemExit(1)

print("SCHEMA: PASS")
