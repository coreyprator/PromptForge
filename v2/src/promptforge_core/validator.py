from __future__ import annotations
import json, typing as t

class ValidationError(Exception): ...

def validate_files_payload(text_or_obj: t.Union[str, dict]) -> t.List[dict]:
    """Accepts a JSON string or dict and returns a list of files.
    Schema (minimal):
    { "files": [{"path": str, "language": str, "contents": str}, ...] }
    """
    if isinstance(text_or_obj, str):
        try:
            data = json.loads(text_or_obj)
        except Exception as e:
            raise ValidationError(f"Invalid JSON: {e}")
    elif isinstance(text_or_obj, dict):
        data = text_or_obj
    else:
        raise ValidationError("Expected JSON string or dict")
    if not isinstance(data, dict) or "files" not in data or not isinstance(data["files"], list):
        raise ValidationError("JSON must be an object with a 'files' array")
    out = []
    for i, f in enumerate(data["files"]):
        if not isinstance(f, dict): raise ValidationError(f"files[{i}] must be an object")
        path = f.get("path"); lang = f.get("language"); contents = f.get("contents")
        if not path or not contents: raise ValidationError(f"files[{i}] missing path/contents")
        out.append({"path": path, "language": (lang or ""), "contents": contents})
    return out
