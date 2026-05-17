# AI Assistant API

这是一个基于 FastAPI 的 AI 后端练习项目，主要用于学习企业后端常见能力：接口鉴权、用户数据隔离、聊天接口、文档上传、知识库问答、请求日志和模型调用日志。

项目当前使用 OpenAI 兼容接口调用大模型，数据库使用 PostgreSQL，ORM 使用 SQLModel。

## 功能列表

### 已完成

- `/health` 健康检查接口
- API Key 鉴权
  - 通过请求头 `X-API-Key` 校验
  - `/health` 不需要鉴权
  - `/chat`、文档上传、知识库查询等接口需要鉴权
- 简化用户身份
  - 通过请求头 `X-User-Id` 传入用户 ID
  - 聊天记录、文档、模型调用日志都带 `user_id`
- 聊天接口 `/chat`
  - 支持 `message`
  - 支持 `session_id`
  - 支持 `temperature`
  - 支持 `max_tokens`
  - 保存用户消息和助手回复
- 聊天历史查询 `/sessions/{session_id}/messages`
  - 按 `session_id` 查询
  - 按 `user_id` 隔离数据
- 文档上传 `/documents/upload`
  - 支持 `.txt`、`.pdf`、`.docx`、`.xlsx`
  - 限制文件大小
  - 保存文件信息到数据库
  - 提取文本内容
- 文档列表 `/documents`
  - 按 `user_id` 查询文档
- 知识库问答 `/knowledge/query`
  - 根据 `document_id` 查询文档
  - 查询时校验 `user_id`
- 请求日志
  - 记录请求方法
  - 记录请求路径
  - 记录状态码
  - 记录耗时
  - 异常时记录错误信息
  - 不打印 API Key
- 模型调用日志 `llm_logs`
  - 记录用户
  - 记录 session_id
  - 记录 model
  - 记录 prompt_tokens、completion_tokens、total_tokens
  - 记录 latency_ms
  - 记录 success
  - 记录 error_message
  - 记录 created_at

### 还需要完善

- 失败的模型调用日志需要确认是否已经在异常路径写入数据库
- Dockerfile 和 docker-compose.yml 当前需要补充可直接启动的配置
- 需要补充自动化测试覆盖更多接口
- 需要补充数据库迁移方案，例如 Alembic
- 需要补充更完整的用户登录系统，目前只是通过 `X-User-Id` 简化模拟
- 需要补充生产环境日志采集方案
- 需要补充模型 token 成本的 SQL 统计示例或成本字段

## 环境变量说明

项目从 `.env` 读取配置。可以参考 `.env.example`：

```env
APP_NAME=ai-backend
ENV=dev

OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=gpt-4o-mini

DATABASE_URL=postgresql://postgres:password@localhost:5432/ai_backend
API_KEY=dev-secret-key
```

字段说明：

| 变量名 | 说明 | 示例 |
| --- | --- | --- |
| `APP_NAME` | 应用名称 | `ai-backend` |
| `ENV` | 运行环境 | `dev` |
| `OPENAI_BASE_URL` | OpenAI 兼容接口地址 | `https://api.openai.com/v1` |
| `OPENAI_API_KEY` | 模型服务 API Key | `your-api-key-here` |
| `OPENAI_MODEL` | 模型名称 | `gpt-4o-mini` |
| `DATABASE_URL` | PostgreSQL 连接地址 | `postgresql://postgres:password@localhost:5432/ai_backend` |
| `API_KEY` | 本项目接口鉴权 Key | `dev-secret-key` |

注意：

- 不要把真实 `OPENAI_API_KEY` 提交到 Git。
- README 和 `.env.example` 只能写示例值。
- 本地真实配置写到 `.env`。

## 本地启动方式

### 1. 创建虚拟环境

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows PowerShell：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 准备环境变量

复制示例配置：

```bash
cp .env.example .env
```

然后修改 `.env`：

```env
OPENAI_API_KEY=your-api-key-here
DATABASE_URL=postgresql://postgres:password@localhost:5432/ai_backend
API_KEY=dev-secret-key
```

### 4. 准备 PostgreSQL 数据库

创建数据库：

```sql
CREATE DATABASE ai_backend;
```

确认 `.env` 中的 `DATABASE_URL` 指向这个数据库。

项目启动时会执行数据库初始化逻辑，创建项目需要的表。

### 5. 启动服务

```bash
uvicorn app.main:app --reload --port 18001
```

启动后访问：

```text
http://127.0.0.1:18001/docs
```

## Docker 启动方式

当前仓库里已经有 `Dockerfile` 和 `docker-compose.yml` 文件，但需要确认内容是否完整。

如果 Docker 配置已经补全，通常启动方式是：

```bash
docker compose up --build
```

如果只启动应用容器，需要保证 PostgreSQL 已经可访问，并且环境变量 `DATABASE_URL` 指向正确地址。

示例：

```env
DATABASE_URL=postgresql://postgres:password@db:5432/ai_backend
```

常见 Docker Compose 服务应该包括：

- `api`：FastAPI 应用
- `db`：PostgreSQL 数据库

## 接口调用示例

下面示例默认服务运行在：

```text
http://127.0.0.1:18001
```

### 健康检查

`/health` 不需要 API Key。

```bash
curl http://127.0.0.1:18001/health
```

预期返回：

```json
{
  "status": "ok",
  "service": "ai-backend"
}
```

### 聊天接口

```bash
curl -X POST "http://127.0.0.1:18001/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-secret-key" \
  -H "X-User-Id: 1" \
  -d '{
    "message": "你好，介绍一下你自己",
    "session_id": 123,
    "temperature": 0.7,
    "max_tokens": 1024
  }'
```

### 查询聊天历史

```bash
curl "http://127.0.0.1:18001/sessions/123/messages" \
  -H "X-API-Key: dev-secret-key" \
  -H "X-User-Id: 1"
```

### 上传文档

```bash
curl -X POST "http://127.0.0.1:18001/documents/upload" \
  -H "X-API-Key: dev-secret-key" \
  -H "X-User-Id: 1" \
  -F "file=@./example.txt"
```

### 查询文档列表

```bash
curl "http://127.0.0.1:18001/documents?user_id=1&limit=20&offset=0" \
  -H "X-API-Key: dev-secret-key" \
  -H "X-User-Id: 1"
```

### 知识库问答

```bash
curl -X POST "http://127.0.0.1:18001/knowledge/query?messages=请总结这个文档&document_id=1" \
  -H "X-API-Key: dev-secret-key" \
  -H "X-User-Id: 1"
```

## 数据库表说明

### chatmessage

保存聊天消息。

| 字段 | 说明 |
| --- | --- |
| `id` | 主键 |
| `session_id` | 会话 ID |
| `user_id` | 用户 ID |
| `role` | 消息角色，例如 `user`、`assistant` |
| `content` | 消息内容 |
| `created_at` | 创建时间 |

### document

保存上传文档信息。

| 字段 | 说明 |
| --- | --- |
| `id` | 主键 |
| `user_id` | 用户 ID |
| `filename` | 原始文件名 |
| `file_path` | 服务端保存路径 |
| `content_type` | 文件类型 |
| `size` | 文件大小 |
| `status` | 文档状态 |
| `text_content` | 提取出的文本内容 |
| `created_at` | 创建时间 |

### llmlog

保存模型调用日志。

| 字段 | 说明 |
| --- | --- |
| `id` | 主键 |
| `user_id` | 用户 ID |
| `session_id` | 会话 ID |
| `model` | 模型名称 |
| `prompt_tokens` | 输入 token 数 |
| `completion_tokens` | 输出 token 数 |
| `total_tokens` | 总 token 数 |
| `latency_ms` | 模型调用耗时，单位毫秒 |
| `success` | 是否调用成功 |
| `error_message` | 失败原因 |
| `created_at` | 创建时间 |

## 常用 SQL

### 查询当天模型调用次数

PostgreSQL：

```sql
SELECT COUNT(*) AS today_calls
FROM llmlog
WHERE created_at >= CURRENT_DATE
  AND created_at < CURRENT_DATE + INTERVAL '1 day';
```

### 按用户查询当天模型调用次数

```sql
SELECT user_id, COUNT(*) AS today_calls
FROM llmlog
WHERE created_at >= CURRENT_DATE
  AND created_at < CURRENT_DATE + INTERVAL '1 day'
GROUP BY user_id
ORDER BY today_calls DESC;
```

### 查询当天 token 消耗

```sql
SELECT
  model,
  SUM(prompt_tokens) AS prompt_tokens,
  SUM(completion_tokens) AS completion_tokens,
  SUM(total_tokens) AS total_tokens
FROM llmlog
WHERE created_at >= CURRENT_DATE
  AND created_at < CURRENT_DATE + INTERVAL '1 day'
GROUP BY model;
```

### 估算 token 成本

不同模型价格不同，下面只是示例算法。实际价格以模型服务商为准。

```sql
SELECT
  model,
  SUM(prompt_tokens) AS prompt_tokens,
  SUM(completion_tokens) AS completion_tokens,
  SUM(prompt_tokens) / 1000000.0 * 0.15
    + SUM(completion_tokens) / 1000000.0 * 0.60 AS estimated_cost_usd
FROM llmlog
WHERE created_at >= CURRENT_DATE
  AND created_at < CURRENT_DATE + INTERVAL '1 day'
GROUP BY model;
```

## 常见问题

### 1. 请求 `/chat` 返回 401

检查请求头是否带了正确的 API Key：

```http
X-API-Key: dev-secret-key
```

同时确认 `.env` 中的 `API_KEY` 和请求头一致。

### 2. 请求返回 422

常见原因：

- JSON 字段缺失
- `temperature` 不在 `0.0` 到 `2.0` 之间
- `max_tokens` 小于 1 或超过限制
- `X-User-Id` 类型不符合后端定义

当前项目的 `user_id` 是数字类型，所以请求头建议使用：

```http
X-User-Id: 1
```

### 3. 数据库连接失败

检查：

- PostgreSQL 是否启动
- 数据库是否已创建
- `.env` 中的 `DATABASE_URL` 是否正确
- 用户名、密码、端口是否正确

### 4. 模型调用失败

检查：

- `OPENAI_API_KEY` 是否有效
- `OPENAI_BASE_URL` 是否正确
- `OPENAI_MODEL` 是否可用
- 网络是否能访问模型服务

### 5. 文档上传失败

检查：

- 文件是否存在
- 文件后缀是否是 `.txt`、`.pdf`、`.docx`、`.xlsx`
- 文件大小是否超过限制

### 6. 为什么 `/health` 不需要鉴权

`/health` 通常给部署平台、监控系统使用，用来判断服务是否存活，所以一般不要求业务 API Key。

### 7. 为什么不能打印完整请求头

请求头里可能包含：

```http
X-API-Key: dev-secret-key
```

如果日志打印完整请求头，API Key 可能泄露。请求日志只记录方法、路径、状态码和耗时。
