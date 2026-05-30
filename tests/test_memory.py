from datetime import datetime, timedelta

import pytest
from sqlalchemy import BigInteger
from sqlmodel import SQLModel, Session, create_engine, select
from sqlalchemy.exc import SQLAlchemyError

from app.agent.memory import ConversationMemory, ConversationMemoryError
from app.models.chat_message import ChatMessage

BIG_SESSION_ID = 1_748_440_000_123


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


# @pytest.mark.asyncio
# async def test_save_creates_user_and_assistant_messages(db_session):
#     memory = ConversationMemory(db_session, user_id=1)

#     await memory.save(
#         session_id=100,
#         user_msg="你好",
#         assistant_msg="你好，我可以帮你。",
#     )

#     messages = db_session.exec(
#         select(ChatMessage).order_by(ChatMessage.created_at)
#     ).all()

#     print("保存后的消息:", [
#         {
#             "session_id": msg.session_id,
#             "user_id": msg.user_id,
#             "role": msg.role,
#             "content": msg.content,
#         }
#         for msg in messages
#     ])

#     assert len(messages) == 2

#     assert messages[0].session_id == 100
#     assert messages[0].user_id == 1
#     assert messages[0].role == "user"
#     assert messages[0].content == "你好"

#     assert messages[1].session_id == 100
#     assert messages[1].user_id == 1
#     assert messages[1].role == "assistant"
#     assert messages[1].content == "你好，我可以帮你。"


# @pytest.mark.asyncio
# async def test_get_history_returns_agent_message_format(db_session):
#     base_time = datetime.utcnow()

#     db_session.add(ChatMessage(
#         session_id=100,
#         user_id=1,
#         role="user",
#         content="第一条用户消息",
#         created_at=base_time,
#     ))
#     db_session.add(ChatMessage(
#         session_id=100,
#         user_id=1,
#         role="assistant",
#         content="第一条助手回复",
#         created_at=base_time + timedelta(seconds=1),
#     ))
#     db_session.commit()

#     memory = ConversationMemory(db_session, user_id=1)

#     history = await memory.get_history(session_id=100)

#     print("读取到的历史:", history)

#     assert history == [
#         {"role": "user", "content": "第一条用户消息"},
#         {"role": "assistant", "content": "第一条助手回复"},
#     ]


# @pytest.mark.asyncio
# async def test_get_history_filters_by_session_id_and_user_id(db_session):
#     db_session.add(ChatMessage(
#         session_id=100,
#         user_id=1,
#         role="user",
#         content="当前用户当前会话",
#     ))
#     db_session.add(ChatMessage(
#         session_id=100,
#         user_id=2,
#         role="user",
#         content="其他用户同会话",
#     ))
#     db_session.add(ChatMessage(
#         session_id=200,
#         user_id=1,
#         role="user",
#         content="当前用户其他会话",
#     ))
#     db_session.commit()

#     memory = ConversationMemory(db_session, user_id=1)

#     history = await memory.get_history(session_id=100)

#     print("隔离后的历史:", history)

#     assert history == [
#         {"role": "user", "content": "当前用户当前会话"}
#     ]


# @pytest.mark.asyncio
# async def test_get_history_respects_limit(db_session):
#     base_time = datetime.utcnow()

#     for index in range(5):
#         db_session.add(ChatMessage(
#             session_id=100,
#             user_id=1,
#             role="user",
#             content=f"消息 {index}",
#             created_at=base_time + timedelta(seconds=index),
#         ))

#     db_session.commit()

#     memory = ConversationMemory(db_session, user_id=1)

#     history = await memory.get_history(session_id=100, limit=2)

#     print("limit 后的历史:", history)

#     assert history == [
#         {"role": "user", "content": "消息 3"},
#         {"role": "user", "content": "消息 4"},
#     ]


@pytest.mark.asyncio
async def test_save_and_get_history_accept_big_session_id(db_session):
    memory = ConversationMemory(db_session, user_id=1)

    await memory.save(
        session_id=BIG_SESSION_ID,
        user_msg="你好",
        assistant_msg="你好，我可以帮你。",
    )

    history = await memory.get_history(session_id=BIG_SESSION_ID)
    messages = db_session.exec(
        select(ChatMessage).order_by(ChatMessage.created_at)
    ).all()

    print("大 session_id 保存结果:", [
        {
            "session_id": msg.session_id,
            "user_id": msg.user_id,
            "role": msg.role,
            "content": msg.content,
        }
        for msg in messages
    ])
    print("大 session_id 读取历史:", history)

    assert [message.session_id for message in messages] == [BIG_SESSION_ID, BIG_SESSION_ID]
    assert history == [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好，我可以帮你。"},
    ]


def test_chat_message_session_and_user_ids_use_big_integer():
    assert isinstance(ChatMessage.__table__.c.session_id.type, BigInteger)
    assert isinstance(ChatMessage.__table__.c.user_id.type, BigInteger)


class FailingCommitDb:
    def __init__(self):
        self.added = []
        self.rollback_called = False

    def add(self, item):
        self.added.append(item)

    def commit(self):
        raise SQLAlchemyError("database write failed")

    def rollback(self):
        self.rollback_called = True


@pytest.mark.asyncio
async def test_save_rolls_back_and_raises_memory_error_when_commit_fails():
    db = FailingCommitDb()
    memory = ConversationMemory(db, user_id=1)

    with pytest.raises(ConversationMemoryError) as exc_info:
        await memory.save(
            session_id=BIG_SESSION_ID,
            user_msg="你好",
            assistant_msg="你好，我可以帮你。",
        )

    print("写入异常:", exc_info.value)
    print("rollback_called:", db.rollback_called)

    assert str(exc_info.value) == "保存会话记忆失败"
    assert db.rollback_called is True
    assert len(db.added) == 2
