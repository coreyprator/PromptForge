import argparse
import json
import sys
from pathlib import Path

EXT_TO_LANG = {
    ".py": "python",
    ".ps1": "powershell",
    ".json": "json",
    ".psm1": "powershell",
    ".psd1": "powershell",
    ".cmd": "batch",
    ".bat": "batch",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".toml": "toml",
    ".md": "markdown",
    ".txt": "text"
}

LANG_STUB = {
    "python": "pass\n",
    "powershell": "#\n",
    "json": "{}\n",
    "yaml": "#\n",
    "toml": "#\n",
    "markdown": "\n",
    "text": "\n",
    "batch": "REM\n"
}

def infer_language_from_path(path: str) -> str | None:
    return EXT_TO_LANG.get(Path(path).suffix.lower())

def stub_for_language(lang: str) -> str:
    return LANG_STUB.get(lang, "\n")

def fix_payload(payload: dict, fill_stubs: bool = True):
    changes: list[str] = []
    errors: list[str] = []

    if not isinstance(payload, dict):
        return None, ["Payload must be a JSON object"]

    files = payload.get("files")
    if not isinstance(files, list):
        return None, ["Payload.files must be a list"]

    for i, f in enumerate(files):
        if not isinstance(f, dict):
            errors.append(f"files[{i}] is not an object")
            continue

        path = f.get("path")
        if not path:
            errors.append(f"files[{i}].path missing")
            continue

        op = f.get("op")
        if not op:
            f["op"] = "write"
            op = "write"
            changes.append(f"files[{i}].op defaulted to 'write'")

        lang = (f.get("language") or "").lower().strip()
        if not lang:
            guessed = infer_language_from_path(path)
            if guessed:
                f["language"] = guessed
                lang = guessed
                changes.append(f"files[{i}].language inferred as '{guessed}'")
            else:
                f["language"] = "text"
                lang = "text"
                changes.append(f"files[{i}].language defaulted to 'text'")

        if op in ("write", "patch"):
            missing = "contents" not in f or f.get("contents") is None
            if missing and fill_stubs:
                f["contents"] = stub_for_language(lang)
                changes.append(f"files[{i}].contents filled with stub for '{lang}'")
            elif missing:
                errors.append(f"files[{i}].contents missing for op={op}")

        if op == "rename":
            if not f.get("from") or not f.get("to"):
                errors.append(f"files[{i}] missing 'from' or 'to' for op=rename")

    return payload, (errors if errors else changes)

def main() -> None:
    parser = argparse.ArgumentParser(description="Fix common Channel-A payload issues.")
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output")
    parser.add_argument("--inplace", action="store_true")
    parser.add_argument("--no-stubs", dest="stubs", action="store_false")
    parser.add_argument(
        "--report-json-only",
        action="store_true",
        help="Emit only a JSON report to stdout",
    )
    args = parser.parse_args()

    src = Path(args.input)
    if not src.exists():
        print(f"Input not found: {src}", file=sys.stderr)
        sys.exit(2)

    payload = json.loads(src.read_text(encoding="utf-8"))
    fixed, msgs = fix_payload(payload, fill_stubs=args.stubs)

    if fixed is None:
        report = {"status": "unfixable", "input_path": str(src), "messages": msgs}
        print(json.dumps(report, ensure_ascii=False))
        sys.exit(1 if args.report_json_only else 0)

    if args.inplace and not args.output:
        dst = src
    else:
        dst = Path(args.output) if args.output else src.with_suffix(".fixed.json")

    dst.write_text(json.dumps(fixed, indent=2, ensure_ascii=False), encoding="utf-8")

    report = {
        "status": "fixed" if msgs else "unchanged",
        "input_path": str(src),
        "output_path": str(dst),
        "messages": msgs,
    }

    if args.report_json_only:
        print(json.dumps(report, ensure_ascii=False))
    else:
        print("Fix report:")
        for m in msgs:
            print(f"- {m}")
        print(f"Wrote: {dst}")

if __name__ == "__main__":
    main()
