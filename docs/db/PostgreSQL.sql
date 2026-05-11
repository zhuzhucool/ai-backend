-- Active: 1777708468747@@101.43.35.199@5432@ai-backend
-- 先创建数据库，再连接到这个库里执行下面的建表语句
-- 注意：PostgreSQL 的数据库名如果带 -，必须用双引号包起来
CREATE DATABASE "ai-backend";

-- documents 表：存文件信息
CREATE TABLE IF NOT EXISTS documents (
    id BIGSERIAL PRIMARY KEY, -- 自增主键，类似 MySQL 的 BIGINT AUTO_INCREMENT
    user_id BIGINT NOT NULL, -- 文件所属用户 ID
    filename TEXT NOT NULL, -- 原始文件名
    file_path TEXT NOT NULL, -- 文件存储路径
    content_type TEXT, -- MIME 类型，比如 image/png
    size BIGINT, -- 文件大小，单位字节
    status VARCHAR(32) NOT NULL DEFAULT 'pending', -- 文件状态，默认 pending
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW() -- 创建时间，带时区
);

CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id); -- 按用户查文件
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at); -- 按时间查文件
ALTER TABLE document ADD COLUMN IF NOT EXISTS text_content TEXT;

-- chat_messages 表：存聊天消息
CREATE TABLE IF NOT EXISTS chat_messages (
    id BIGSERIAL PRIMARY KEY, -- 消息主键
    session_id BIGINT NOT NULL, -- 会话 ID
    user_id BIGINT NOT NULL, -- 用户 ID
    role VARCHAR(16) NOT NULL, -- 角色：user / assistant / system / tool
    content TEXT NOT NULL, -- 消息内容
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), -- 创建时间
    CONSTRAINT chk_chat_messages_role
        CHECK (role IN ('user', 'assistant', 'system', 'tool')) -- 限制 role 只能是这几个值
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id); -- 按会话查消息
CREATE INDEX IF NOT EXISTS idx_chat_messages_user_id ON chat_messages(user_id); -- 按用户查消息
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at); -- 按时间查消息

-- llm_logs 表：存模型调用日志
CREATE TABLE IF NOT EXISTS llm_logs (
    id BIGSERIAL PRIMARY KEY, -- 日志主键
    user_id BIGINT NOT NULL, -- 发起调用的用户
    session_id BIGINT, -- 关联会话，可空
    model VARCHAR(100) NOT NULL, -- 模型名，比如 claude-sonnet-4-6
    prompt_tokens INTEGER NOT NULL DEFAULT 0, -- 输入 token 数
    completion_tokens INTEGER NOT NULL DEFAULT 0, -- 输出 token 数
    total_tokens INTEGER NOT NULL DEFAULT 0, -- 总 token 数
    latency_ms INTEGER, -- 调用耗时，毫秒
    success BOOLEAN NOT NULL DEFAULT FALSE, -- 是否成功
    error_message TEXT, -- 失败时的错误信息
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW() -- 创建时间
);

CREATE INDEX IF NOT EXISTS idx_llm_logs_user_id ON llm_logs(user_id); -- 按用户查日志
CREATE INDEX IF NOT EXISTS idx_llm_logs_session_id ON llm_logs(session_id); -- 按会话查日志
CREATE INDEX IF NOT EXISTS idx_llm_logs_created_at ON llm_logs(created_at); -- 按时间查日志
