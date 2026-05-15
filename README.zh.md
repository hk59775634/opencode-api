# opencode-api

[English](./README.md) | **中文**

[opencode](https://opencode.ai) 的 OpenAI 兼容 API 代理 — 将 `opencode serve` 暴露为标准 `/v1/chat/completions` 接口。

## 功能

- **OpenAI 兼容** — 可作为任何 OpenAI 客户端的即插即用替代
- **免费模型** — 仅列出 opencode 免费模型（`deepseek-v4-flash-free`、`qwen3.6-plus-free` 等）
- **多轮对话** — 通过 `noReply` 消息保持上下文
- **系统提示词** — 将 `system` 角色映射到 opencode 的系统提示词
- **流式输出** — SSE 逐字符流式响应（聊天 & 文本补全）
- **图片输入** — 支持 `image_url` 格式，适用于视觉模型
- **文本补全** — 传统 `/v1/completions` 端点
- **API 密钥认证** — 可选 `API_KEY` 环境变量用于 Bearer Token 鉴权
- **模型映射** — 纯模型名自动补全为 `opencode/<model>` 提供商
- **健康检查** — `GET /health` 和 `GET /`

## 快速开始

```bash
# 使用 docker 运行
docker run -d -p 80:80 -e API_KEY=sk-mykey hk59775634/opencode-api:latest

# 或使用 docker-compose
API_KEY=sk-mykey docker compose up -d

# 无鉴权（不设置 API_KEY 则无需认证）
docker run -d -p 80:80 hk59775634/opencode-api:latest
```

## 使用示例

### 健康检查

```bash
curl http://localhost:80/health
# {"status":"ok","opencode":true}
```

### 列出模型

```bash
curl http://localhost:80/v1/models
```

### 对话补全

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

### 文本补全

```bash
curl -X POST http://localhost:80/v1/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-mykey" \
  -d '{
    "model": "deepseek-v4-flash-free",
    "prompt": "从前有座山",
    "max_tokens": 100,
    "stream": false
  }'
```

### 流式输出

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

### 图片输入（视觉模型）

```bash
curl -X POST http://localhost:80/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3.6-plus-free",
    "messages": [
      {
        "role": "user",
        "content": [
          {"type": "text", "text": "这张图片里有什么？"},
          {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
        ]
      }
    ]
  }'
```

## 配置项

| 环境变量 | 默认值 | 说明 |
|---|---|---|
| `API_KEY` | (空) | Bearer Token 鉴权。留空则关闭鉴权。 |
| `OPENCODE_URL` | `http://127.0.0.1:4096` | 后端 opencode serve 地址 |
| `PORT` | `80` | 适配器监听端口 |

## 架构

```
┌─────────────┐     /v1/chat/completions     ┌──────────────┐     session API     ┌──────────────┐
│  OpenAI SDK  │ ──────────────────────────►  │  adapter.py  │ ──────────────────► │ opencode     │
│  curl / 任意  │ ◄──────────────────────────  │  (port 80)   │ ◄────────────────── │ serve        │
└─────────────┘     OpenAI 格式               └──────────────┘     session API     │ (port 4096)  │
                                                                  └──────────────┘
```

## 构建

```bash
docker build -t opencode-api .
```

## 项目结构

```
├── adapter.py        # FastAPI 应用：OpenAI → opencode 代理
├── Dockerfile        # Docker 镜像（含 opencode + python 依赖）
├── entrypoint.sh     # 启动脚本：先启 opencode serve，再启 adapter
├── docker-compose.yml
├── README.md         # 英文文档
├── README.zh.md      # 中文文档
└── .gitignore
```
