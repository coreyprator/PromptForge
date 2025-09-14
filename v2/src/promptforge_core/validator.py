from __future__ import annotations
import json, typing as t

class ValidationError(Exception): ...

def validate_files_payload(text: str) -> t.List[dict]:
    """
    Accepts a JSON string and returns a list of files.
    Schema (minimal):
    {
      "files": [{"path": str, "language": str, "contents": str}, ...]
    }
    """
    try:
        data = json.loads(text)
    except Exception as e:
        raise ValidationError(f"Invalid JSON: {e}")
    if not isinstance(data, dict) or "files" not in data or not isinstance(data["files"], list):
        raise ValidationError("JSON must be an object with a 'files' array")
    out = []
    for i, f in enumerate(data["files"]):
        if not isinstance(f, dict): raise ValidationError(f"files[{i}] must be an object")
        path = f.get("path"); lang = f.get("language"); contents = f.get("contents")
        if not path or not contents: raise ValidationError(f"files[{i}] missing path/contents")
        out.append({"path": path, "language": lang or "", "contents": contents})
    return out
