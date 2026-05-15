# opencode-api

OpenAI-compatible API proxy for [opencode](https://opencode.ai) — exposes `opencode serve` as a standard `/v1/chat/completions` endpoint.

## Features

- **OpenAI-compatible** — drop-in replacement for any OpenAI client
- **Free models** — only lists opencode free models (`deepseek-v4-flash-free`, `qwen3.6-plus-free`, etc.)
- **Multi-turn conversation** — preserves context via `noReply` messages
- **System prompts** — maps `system` role to opencode's system prompt
- **Streaming** — SSE character-by-character streaming
- **API key auth** — optional `API_KEY` env var for bearer token auth
- **Model mapping** — bare model name → `opencode/<model>` provider

## Quick Start

```bash
# run with docker
docker run -d -p 80:80 -e API_KEY=sk-mykey hk59775634/opencode-api:latest

# or with docker-compose
API_KEY=sk-mykey docker compose up -d

# without auth (API_KEY not set → no auth required)
docker run -d -p 80:80 hk59775634/opencode-api:latest
```

## Usage

### List models

```bash
curl http://localhost:80/v1/models
```

### Chat completion

```bash
curl -X POST http://localhost:80/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-mykey" \
  -d '{
    "model": "deepseek-v4-flash-free",
    "messages": [
      {"role": "system", "content": "你是一只猫娘，每句话结尾加喵"},
      {"role": "user", "content": "你好"}
    ],
    "stream": false
  }'
```

### Streaming

```bash
curl -N -X POST http://localhost:80/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-mykey" \
  -d '{
    "model": "deepseek-v4-flash-free",
    "messages": [{"role": "user", "content": "你好"}],
    "stream": true
  }'
```

## Configuration

| Environment Variable | Default | Description |
|---|---|---|
| `API_KEY` | (empty) | Bearer token for auth. Omit to disable auth. |
| `OPENCODE_URL` | `http://127.0.0.1:4096` | Backend opencode serve URL |
| `PORT` | `80` | Adapter listening port |

## Architecture

```
┌─────────────┐     /v1/chat/completions     ┌──────────────┐     session API     ┌──────────────┐
│  OpenAI SDK  │ ──────────────────────────►  │  adapter.py  │ ──────────────────► │ opencode     │
│  curl / any  │ ◄──────────────────────────  │  (port 80)   │ ◄────────────────── │ serve        │
└─────────────┘     OpenAI format             └──────────────┘     session API     │ (port 4096)  │
                                                                  └──────────────┘
```

## Build

```bash
docker build -t opencode-api .
```

## Project Structure

```
├── adapter.py        # FastAPI app: OpenAI → opencode proxy
├── Dockerfile        # Docker image with opencode + python deps
├── entrypoint.sh     # Starts opencode serve, then adapter
├── docker-compose.yml
└── README.md
```
