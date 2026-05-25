# Agent chat / memory / logging todo

## 必须改

- [ ] 把 `session_id` 类型统一成字符串或 BIGINT，避免 PostgreSQL integer out of range
- [ ] 调整 `agent_chat.py` 的异常边界，数据库异常后先 rollback，避免事务污染
- [ ] `ConversationMemory.get_history()` 过滤空 content、非法 role、过长历史内容
- [ ] `ConversationMemory.get_history()` 失败时记录日志并降级为空历史，不让当前请求直接失败
- [ ] `AgentToolLogWriter.save()` 失败时记录日志，不影响用户拿到 Agent 回答
- [ ] `LLMLog` 写入失败时记录日志，不影响主请求返回
- [ ] 处理 DeepSeek thinking mode 的 `reasoning_content` 传递，避免工具调用后的 400

## 建议改

- [ ] 统一 `ConversationMemory` 的数据库异常处理和 rollback 责任
- [ ] 统一 `AgentToolLogWriter` 的数据库异常处理和 rollback 责任
- [ ] 检查 `LLMLog`、`ChatMessage`、`AgentToolLog` 的字段类型一致性
- [ ] 复查 `app/api/chat.py` 和 `app/api/agent_chat.py` 的 LLM 调用参数是否统一
- [ ] 补充 `/agent/chat` 的接口测试，覆盖直接回答、tool 调用、memory 失败、tool log 失败
- [ ] 补充 `/agent/sessions/{id}/tool-logs` 的接口测试，确认按 `session_id + user_id` 隔离
- [ ] 给 AgentLoop 的 messages 打印加调试工具，输出 role、content 摘要、tool_calls 数量

## 以后再说

- [ ] 给 Agent 接口加临时关闭开关，出事故时切回普通 chat 或返回维护中
- [ ] 准备数据修复脚本：删除空 assistant 消息、清理重复测试消息、截断异常长历史
- [ ] 加 Agent 调用监控：LLM 失败率、tool 失败率、memory 失败率、平均 iterations
- [ ] 给会话历史做摘要压缩，避免长历史占满上下文
- [ ] 把 Agent 模块按 DDD 方向拆成 application/domain/infrastructure
