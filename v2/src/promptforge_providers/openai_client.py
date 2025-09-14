from __future__ import annotations
import os, json, base64, mimetypes, re, logging
from typing import List, Optional, Tuple

log = logging.getLogger("promptforge")

def _have_openai() -> bool:
    try:
        import openai  # noqa
        return True
    except Exception as e:
        log.debug("OpenAI import failed: %s", e)
        return False

def _b64_image_url(path: str) -> Optional[dict]:
    try:
        mime = mimetypes.guess_type(path)[0] or "image/png"
        raw = open(path, "rb").read()
        b64 = base64.b64encode(raw).decode("ascii")
        return {"type":"image_url","image_url":{"url": f"data:{mime};base64,{b64}"}}
    except Exception as e:
        log.warning("Could not read image %s: %s", path, e)
        return None

def _content_parts(user_text: str, attachments: Optional[List[str]]) -> list:
    parts = [{"type": "text", "text": user_text}]
    if attachments:
        for p in attachments:
            p = str(p)
            if p.lower().endswith((".png",".jpg",".jpeg",".gif",".webp",".bmp")):
                url = _b64_image_url(p)
                if url: parts.append(url)
    return parts

def _extract_json_block(text: str) -> str:
    if not text:
        raise ValueError("Empty response from model.")
    fence = re.search(r"```(?:json)?\\s*(.*?)\\s*```", text, flags=re.S)
    if fence:
        text = fence.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end+1]
    return text

def _client():
    from openai import OpenAI
    key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_APIKEY") or os.getenv("OPENAI_TOKEN")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set in environment.")
    return OpenAI(api_key=key)

def call_structured_channel_a(system: str, user: str, model: Optional[str] = None, attachments: Optional[List[str]] = None) -> Tuple[Optional[dict], Optional[str]]:
    default_model = os.getenv("PF_MODEL_A", "gpt-4o-mini")
    model = model or default_model

    if not _have_openai():
        mock = {"files":[{"path":"README.mock.txt","contents":"OpenAI SDK not installed. Mock payload."}]}
        return mock, "OpenAI SDK not installed; returning mock payload."

    try:
        cl = _client()
        messages = [
            {"role":"system","content": system},
            {"role":"user","content": _content_parts(user, attachments)},
        ]
        r = cl.chat.completions.create(
            model=model, messages=messages, temperature=0.0, response_format={"type":"json_object"}
        )
        content = r.choices[0].message.content or ""
        try:
            obj = json.loads(_extract_json_block(content))
        except Exception as je:
            log.exception("JSON parse error")
            return None, f"Failed to parse model JSON: {je}\\nRaw:\\n{content}"
        return obj, None
    except Exception as e:
        msg = str(e)
        if "insufficient_quota" in msg or "Error code: 429" in msg:
            msg += "\\nHint: Billing/quota issue. See OpenAI dashboard."
        log.exception("Channel A error")
        return None, msg

def call_prose_channel_b(system: str, user: str, model: Optional[str] = None, attachments: Optional[List[str]] = None) -> Tuple[str, Optional[str]]:
    default_model = os.getenv("PF_MODEL_B", "gpt-4o-mini")
    model = model or default_model

    if not _have_openai():
        return "OpenAI SDK not installed; returning mock prose.", "OpenAI SDK not installed."

    try:
        cl = _client()
        messages = [
            {"role":"system","content": system},
            {"role":"user","content": _content_parts(user, attachments)},
        ]
        r = cl.chat.completions.create(model=model, messages=messages, temperature=0.2)
        text = (r.choices[0].message.content or "").strip()
        return text, None
    except Exception as e:
        msg = str(e)
        if "insufficient_quota" in msg or "Error code: 429" in msg:
            msg += "\\nHint: Billing/quota issue. See OpenAI dashboard."
        log.exception("Channel B error")
        return f"[Error] {type(e).__name__}: {msg}", msg