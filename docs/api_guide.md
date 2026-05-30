# 前端接口对接文档

本文档面向前端联调使用，描述当前后端已有接口、鉴权方式、主要业务流程和常见错误。

## 1. 基础信息

### 服务地址

本地开发默认地址：

```text
http://127.0.0.1:18001
```

Swagger 在线文档：

```text
http://127.0.0.1:18001/docs
```

OpenAPI JSON：

```text
http://127.0.0.1:18001/openapi.json
```

### 请求格式

普通接口默认使用 JSON：

```http
Content-Type: application/json
```

文档上传接口使用 multipart：

```http
Content-Type: multipart/form-data
```

## 2. 鉴权和用户身份

当前项目还没有正式登录系统，前端联调用请求头模拟用户身份。

### 通用请求头

大部分业务接口需要：

```http
X-API-Key: dev-secret-zhuzhucool
X-User-Id: 1
```

说明：

| 请求头 | 必填 | 说明 |
| --- | --- | --- |
| `X-API-Key` | 部分接口必填 | 后端 API Key。当前代码中固定校验值为 `dev-secret-zhuzhucool`。 |
| `X-User-Id` | 业务接口必填 | 当前用户 ID，数字类型。用于隔离聊天记录、文档、知识库数据。 |

### 不需要 API Key 的接口

| 接口 | 说明 |
| --- | --- |
| `GET /health` | 健康检查 |
| `POST /documents/upload` | 当前代码未加 `X-API-Key` 校验，但仍需要 `X-User-Id` |
| `GET /documents` | 当前代码未加 `X-API-Key` 校验 |
| `DELETE /documents/{document_id}` | 当前代码未加 `X-API-Key` 校验，但仍需要 `X-User-Id` |
| `POST /knowledge/search` | 当前代码未加 `X-API-Key` 校验，但仍需要 `X-User-Id` |

联调时建议前端统一带上 `X-API-Key` 和 `X-User-Id`，减少后续接口加鉴权后的改动。

## 3. 统一错误说明

当前后端还没有统一响应包裹层，成功响应直接返回业务对象。

常见错误：

| HTTP 状态码 | 场景 | 返回示例 |
| --- | --- | --- |
| 400 | 参数内容不合法，例如空消息、文件名为空、文件格式不支持 | `{ "detail": "仅支持 txt/pdf/docx/xlsx 格式" }` |
| 401 | `X-API-Key` 不正确或缺失 | `{ "detail": "Invalid API key" }` |
| 404 | 删除不存在或不属于当前用户的文档 | `{ "detail": "文档不存在" }` |
| 422 | 请求参数类型错误、必填字段缺失、请求头缺失 | FastAPI 默认校验错误结构 |
| 500 | 文档索引失败、Agent 持久化失败等服务端异常 | `{ "detail": "文档索引失败" }` |
| 503 | 知识库检索服务不可用 | `{ "detail": "检索服务暂时不可用，请稍后重试" }` |

前端建议：

- `401`：提示鉴权失败或重新配置 API Key。
- `422`：优先检查请求参数和请求头。
- `500` / `503`：展示通用错误提示，并保留请求参数方便后端排查。

## 4. 主流程

### 4.1 普通聊天流程

1. 前端生成或复用 `session_id`。
2. 调用 `POST /chat` 发送用户消息。
3. 后端返回助手回复。
4. 需要展示历史记录时，调用 `GET /sessions/{session_id}/messages`。

### 4.2 文档知识库流程

1. 用户上传 `.txt`、`.pdf`、`.docx`、`.xlsx` 文件。
2. 前端调用 `POST /documents/upload`。
3. 返回 `status = indexed` 时，表示文档已解析、切分、生成 embedding 并写入向量库。
4. 前端可以调用 `GET /documents` 展示文档列表。
5. 用户提问时：
   - 只看检索片段：调用 `POST /knowledge/search`。
   - 需要直接生成答案：调用 `POST /knowledge/query`。

注意：当前上传接口是同步处理，文件解析和索引完成后才返回。大文件可能等待较久，前端应展示 loading。

### 4.3 Agent 聊天流程

1. 前端调用 `GET /agent/tools` 获取可用工具。
2. 调用 `POST /agent/chat` 发送消息。
3. 后端返回 `answer` 和本次调用过的工具列表 `tool_calls`。
4. 需要查看某个会话的工具调用日志时，调用 `GET /agent/sessions/{session_id}/tool-logs`。

当前 Agent 可用工具包括：

- 计算器
- 当前时间
- 知识库检索

## 5. 接口详情

## 5.1 健康检查

```http
GET /health
```

是否需要请求头：否。

成功响应：

```json
{
  "status": "ok",
  "service": "ai-backend"
}
```

## 5.2 普通聊天

```http
POST /chat
```

请求头：

```http
Content-Type: application/json
X-API-Key: dev-secret-zhuzhucool
X-User-Id: 1
```

请求体：

```json
{
  "message": "你好，介绍一下你自己",
  "session_id": 123,
  "temperature": 0.7,
  "max_tokens": 1024
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `message` | string | 是 | 用户消息，不能为空字符串。 |
| `session_id` | number | 否 | 会话 ID。当前模型默认值为 `123`，建议前端明确传入。 |
| `temperature` | number | 是 | 取值范围 `0.0` 到 `2.0`。 |
| `max_tokens` | number | 是 | 取值范围 `1` 到 `3072`。 |

成功响应：

```json
{
  "session_id": 123,
  "message": "你好，我是一个 AI 助手。",
  "model": "gpt-4o-mini",
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 18,
    "total_tokens": 30
  }
}
```

失败示例：

```json
{
  "detail": {
    "error": "bad_request",
    "message": "message 不能为空"
  }
}
```

## 5.3 查询会话消息

```http
GET /sessions/{session_id}/messages
```

请求头：

```http
X-API-Key: dev-secret-zhuzhucool
X-User-Id: 1
```

路径参数：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `session_id` | number | 会话 ID。 |

成功响应：

```json
{
  "session_id": 123,
  "messages": [
    {
      "id": 1,
      "session_id": 123,
      "user_id": 1,
      "content": "你好",
      "role": "user",
      "created_at": "2026-05-27T10:30:00"
    },
    {
      "id": 2,
      "session_id": 123,
      "user_id": 1,
      "content": "你好，我是一个 AI 助手。",
      "role": "assistant",
      "created_at": "2026-05-27T10:30:02"
    }
  ]
}
```

## 5.4 上传文档

```http
POST /documents/upload
```

请求头：

```http
X-User-Id: 1
```

建议同时带上：

```http
X-API-Key: dev-secret-zhuzhucool
```

请求类型：

```http
multipart/form-data
```

表单字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `file` | File | 是 | 支持 `.txt`、`.pdf`、`.docx`、`.xlsx`，最大 20MB。 |

成功响应：

```json
{
  "document_id": 1,
  "filename": "example.pdf",
  "status": "indexed",
  "chunks_count": 12
}
```

状态说明：

| status | 说明 |
| --- | --- |
| `indexed` | 文档已完成解析、切分和向量索引，可用于知识库检索。 |
| `failed` | 文档索引失败。当前接口失败时会返回 500。 |

失败示例：

```json
{
  "detail": "仅支持 txt/pdf/docx/xlsx 格式"
}
```

前端注意：

- 上传接口会等待索引完成后返回，建议展示进度或 loading。
- 当前没有单独的上传进度查询接口。
- 当前删除文档不会删除服务端磁盘上的原文件，只删除数据库文档记录和向量分片。

## 5.5 查询文档列表

```http
GET /documents?user_id=1&limit=20&offset=0
```

请求头：

```http
X-User-Id: 1
```

建议同时带上：

```http
X-API-Key: dev-secret-zhuzhucool
```

Query 参数：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `user_id` | number | 是 | 无 | 要查询的用户 ID。当前接口从 query 读取。建议与 `X-User-Id` 保持一致。 |
| `limit` | number | 否 | 20 | 每页条数，范围 `1` 到 `100`。 |
| `offset` | number | 否 | 0 | 偏移量，最小 `0`。 |

成功响应：

```json
{
  "total": 1,
  "documents": [
    {
      "id": 1,
      "filename": "example.pdf",
      "status": "indexed",
      "created_at": "2026-05-27T10:30:00"
    }
  ]
}
```

## 5.6 删除文档

```http
DELETE /documents/{document_id}
```

请求头：

```http
X-User-Id: 1
```

建议同时带上：

```http
X-API-Key: dev-secret-zhuzhucool
```

路径参数：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `document_id` | number | 文档 ID。只能删除当前用户自己的文档。 |

成功响应：

```json
{
  "document_id": 1,
  "status": "deleted"
}
```

失败示例：

```json
{
  "detail": "文档不存在"
}
```

## 5.7 知识库检索

只返回检索命中的文档片段，不调用 LLM。

```http
POST /knowledge/search?query=项目支持哪些文件格式&top_k=5
```

请求头：

```http
X-User-Id: 1
```

建议同时带上：

```http
X-API-Key: dev-secret-zhuzhucool
```

Query 参数：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `query` | string | 是 | 无 | 检索关键词或问题。 |
| `top_k` | number | 否 | 5 | 返回结果数量。 |

成功响应：

```json
{
  "query": "项目支持哪些文件格式",
  "results": [
    {
      "text": "支持 txt、pdf、docx、xlsx 格式。",
      "source_file": "example.pdf",
      "page_number": 1,
      "section_title": null,
      "similarity": 0.82,
      "low_confidence": false
    }
  ]
}
```

## 5.8 知识库问答

先检索文档片段，再调用 LLM 生成答案。

```http
POST /knowledge/query?query=项目支持哪些文件格式&top_k=5
```

请求头：

```http
X-API-Key: dev-secret-zhuzhucool
X-User-Id: 1
```

Query 参数：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `query` | string | 是 | 无 | 用户问题。 |
| `top_k` | number | 否 | 5 | 参与问答的检索结果数量。 |

成功响应：

```json
{
  "answer": "项目支持 txt、pdf、docx、xlsx 格式。",
  "sources": [
    {
      "file": "example.pdf",
      "page": 1,
      "similarity": 0.82
    }
  ],
  "confidence": "high"
}
```

低置信度响应：

```json
{
  "answer": "文档中未找到与您问题相关的内容，请确认已上传相关文档。",
  "sources": [],
  "confidence": "low"
}
```

## 5.9 Agent 聊天

```http
POST /agent/chat
```

请求头：

```http
Content-Type: application/json
X-API-Key: dev-secret-zhuzhucool
X-User-Id: 1
```

请求体：

```json
{
  "message": "帮我查一下知识库里关于项目支持文件格式的内容",
  "session_id": 123,
  "temperature": 0.7,
  "max_tokens": 1024
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `message` | string | 是 | 用户消息，不能为空字符串。 |
| `session_id` | number 或 null | 否 | 不传时后端会用当前时间戳生成。建议前端传入，方便查历史和工具日志。 |
| `temperature` | number | 否 | 默认 `0.7`，范围 `0.0` 到 `2.0`。 |
| `max_tokens` | number | 否 | 默认 `1024`，范围 `1` 到 `3072`。 |

成功响应：

```json
{
  "session_id": 123,
  "answer": "根据知识库，项目支持 txt、pdf、docx、xlsx 格式。",
  "iterations": 2,
  "tool_calls": [
    {
      "tool": "knowledge_search",
      "arguments": {
        "query": "项目支持文件格式",
        "top_k": 5
      },
      "result": {
        "results": []
      }
    }
  ]
}
```

前端展示建议：

- `answer` 展示给用户。
- `tool_calls` 可以先不展示，后续做调试面板或“使用了哪些工具”时再展示。
- `iterations` 可用于调试，不建议作为普通用户界面核心信息。

## 5.10 查询 Agent 可用工具

```http
GET /agent/tools
```

请求头：

```http
X-API-Key: dev-secret-zhuzhucool
X-User-Id: 1
```

成功响应：

```json
{
  "tools": [
    {
      "name": "get_current_time",
      "description": "获取当前时间",
      "parameters": {
        "type": "object",
        "properties": {}
      }
    }
  ]
}
```

实际工具列表以后端返回为准。

## 5.11 查询 Agent 工具调用日志

```http
GET /agent/sessions/{session_id}/tool-logs
```

请求头：

```http
X-API-Key: dev-secret-zhuzhucool
X-User-Id: 1
```

路径参数：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `session_id` | number | Agent 会话 ID。 |

成功响应：

```json
{
  "session_id": 123,
  "tool_logs": [
    {
      "id": 1,
      "session_id": 123,
      "user_id": 1,
      "tool": "knowledge_search",
      "arguments": {
        "query": "项目支持文件格式",
        "top_k": 5
      },
      "result": {
        "results": []
      },
      "iteration": 1,
      "success": true,
      "error_message": null,
      "created_at": "2026-05-27T10:30:00"
    }
  ]
}
```

## 6. 前端联调建议

### 会话 ID

- 普通聊天和 Agent 聊天都建议前端生成 `session_id` 并复用。
- 可以用时间戳，也可以用后端返回的 `session_id`。
- 如果 Agent 聊天不传 `session_id`，后端会自动生成并返回。

### 用户 ID

- 当前用 `X-User-Id` 模拟登录用户。
- 不同用户之间的聊天记录、文档和知识库数据相互隔离。
- 前端本地开发可以先固定为 `1`。

### 文档状态

- 当前文档上传成功后通常直接返回 `indexed`。
- 如果后续改成异步索引，前端需要根据文档状态展示处理中状态；当前版本暂时不需要轮询。

### 知识库问答

- 如果用户还没上传文档，`/knowledge/query` 大概率返回低置信度答案。
- 前端可以在 `confidence = low` 时提示用户先上传相关文档。
- 如果只想调试召回效果，用 `/knowledge/search`；如果要直接给用户答案，用 `/knowledge/query`。

### 普通聊天和 Agent 聊天区别

| 接口 | 用途 | 是否会调用工具 | 是否适合展示工具过程 |
| --- | --- | --- | --- |
| `/chat` | 普通大模型聊天 | 否 | 否 |
| `/agent/chat` | 可使用工具的智能体聊天 | 是 | 是 |
| `/knowledge/query` | 基于已上传文档问答 | 内部检索文档 | 展示 sources 即可 |

## 7. curl 示例

### 普通聊天

```bash
curl -X POST "http://127.0.0.1:18001/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-secret-zhuzhucool" \
  -H "X-User-Id: 1" \
  -d '{
    "message": "你好",
    "session_id": 123,
    "temperature": 0.7,
    "max_tokens": 1024
  }'
```

### 上传文档

```bash
curl -X POST "http://127.0.0.1:18001/documents/upload" \
  -H "X-User-Id: 1" \
  -F "file=@./example.pdf"
```

### 知识库问答

```bash
curl -X POST "http://127.0.0.1:18001/knowledge/query?query=项目支持哪些文件格式&top_k=5" \
  -H "X-API-Key: dev-secret-zhuzhucool" \
  -H "X-User-Id: 1"
```

### Agent 聊天

```bash
curl -X POST "http://127.0.0.1:18001/agent/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-secret-zhuzhucool" \
  -H "X-User-Id: 1" \
  -d '{
    "message": "现在几点？",
    "session_id": 123,
    "temperature": 0.7,
    "max_tokens": 1024
  }'
```

## 8. 当前需要前后端提前确认的点

这些不是接口不能用，而是后续容易变动：

1. `X-API-Key` 当前代码固定写死为 `dev-secret-zhuzhucool`，没有读取 `.env` 里的 `API_KEY`。
2. 部分接口当前没有加 `X-API-Key` 校验，但建议前端统一携带。
3. `GET /documents` 当前通过 query 参数传 `user_id`，而不是只从 `X-User-Id` 获取。
4. 当前没有统一响应结构，成功和失败结构不一致。
5. 当前没有真实登录、注册、token 刷新流程。
6. 当前没有 CORS 配置，如果浏览器跨域请求失败，需要后端补 CORS 中间件。
7. 当前没有文档索引进度查询接口，上传接口会等待索引结束。
