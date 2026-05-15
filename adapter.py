from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import requests
import json
import uuid
import time
import asyncio
import os

app = FastAPI()
auth_scheme = HTTPBearer(auto_error=False)

OPENCODE_URL = os.environ.get("OPENCODE_URL", "http://127.0.0.1:4096")
API_KEY = os.environ.get("API_KEY", "")


def verify_auth(credentials: HTTPAuthorizationCredentials | None = Depends(auth_scheme)):
    if not API_KEY:
        return
    if credentials is None or credentials.credentials != API_KEY:
        raise HTTPException(
            status_code=401,
            detail={
                "error": {
                    "message": "Incorrect API key provided. Set your API key in the Authorization header.",
                    "type": "invalid_request_error",
                    "param": None,
                    "code": "invalid_api_key",
                }
            },
        )


def create_session():
    resp = requests.post(f"{OPENCODE_URL}/session", json={})
    resp.raise_for_status()
    return resp.json()["id"]


def extract_assistant_text(response):
    for part in response.get("parts", []):
        if part.get("type") == "text":
            return part.get("text", "")
    return ""


def extract_tokens(response):
    tokens = response.get("info", {}).get("tokens", {})
    return {
        "prompt_tokens": tokens.get("input", 0) or tokens.get("total", 0) or 0,
        "completion_tokens": tokens.get("output", 0) or 0,
        "total_tokens": tokens.get("total", 0) or 0,
    }


def parse_model(model_str):
    if not model_str:
        return None
    parts = model_str.split("/", 1)
    if len(parts) == 2:
        return {"providerID": parts[0], "modelID": parts[1]}
    return {"providerID": "opencode", "modelID": model_str}


@app.get("/v1/models")
async def list_models(_=Depends(verify_auth)):
    try:
        resp = requests.get(f"{OPENCODE_URL}/provider", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            providers = data.get("all", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
            models = []
            for p in providers:
                if p.get("id") != "opencode":
                    continue
                for mid in (p.get("models") or {}):
                    models.append({
                        "id": mid,
                        "object": "model",
                        "created": int(time.time()),
                        "owned_by": "opencode",
                    })
            return {"object": "list", "data": models}
    except requests.RequestException:
        pass
    return {"object": "list", "data": []}


@app.post("/v1/chat/completions")
async def chat_completions(request: Request, _=Depends(verify_auth)):
    data = await request.json()
    messages = data.get("messages", [])
    stream = data.get("stream", False)
    model_str = data.get("model", "")

    system_message = ""
    history_texts = []
    last_user = ""

    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role == "system":
            system_message = content
        elif role == "user":
            if last_user:
                history_texts.append(last_user)
            last_user = content
        elif role == "assistant":
            history_texts.append(last_user)
            history_texts.append(content)
            last_user = ""

    if not last_user:
        last_user = "hello"

    session_id = create_session()

    model_param = parse_model(model_str)
    payload_base = {}
    if model_param:
        payload_base["model"] = model_param
    if system_message:
        payload_base["system"] = system_message

    def send_no_reply(text):
        try:
            requests.post(
                f"{OPENCODE_URL}/session/{session_id}/message",
                json={**payload_base, "parts": [{"type": "text", "text": text}], "noReply": True},
                timeout=30,
            )
        except requests.RequestException:
            pass

    for text in history_texts:
        send_no_reply(text)

    payload = {**payload_base, "parts": [{"type": "text", "text": last_user}]}

    try:
        resp = requests.post(
            f"{OPENCODE_URL}/session/{session_id}/message",
            json=payload,
            timeout=300,
        )
        resp.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    result = resp.json()
    text = extract_assistant_text(result)
    tokens = extract_tokens(result)
    completion_id = f"chatcmpl-{uuid.uuid4()}"
    created = int(time.time())

    if stream:

        async def generate():
            for char in text:
                chunk = {
                    "id": completion_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": model_str or "opencode",
                    "choices": [{
                        "index": 0,
                        "delta": {"content": char},
                        "finish_reason": None,
                    }],
                }
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.005)
            final = {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model_str or "opencode",
                "choices": [{
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop",
                }],
            }
            yield f"data: {json.dumps(final, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")
    else:
        return {
            "id": completion_id,
            "object": "chat.completion",
            "created": created,
            "model": model_str or "opencode",
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop",
            }],
            "usage": tokens,
        }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "80"))
    uvicorn.run(app, host="0.0.0.0", port=port)
