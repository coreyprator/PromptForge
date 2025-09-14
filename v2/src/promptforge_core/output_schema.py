from __future__ import annotations
import json
from typing import Dict, Any

FILES_SCHEMA: Dict[str, Any] = {
    "name": "files_payload",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "files": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "path": {"type": "string", "minLength": 1},
                        "language": {"type": "string"},
                        "contents": {"type": "string"}
                    },
                    "required": ["path", "contents"]
                }
            }
        },
        "required": ["files"]
    }
}

def example_payload() -> str:
    ex = {
        "files": [
            {
                "path": "src/example/hello.py",
                "language": "python",
                "contents": "print('hello from PromptForge V2')\n"
            }
        ]
    }
    return json.dumps(ex, indent=2)
