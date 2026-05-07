from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from app.core import config
from app.services import llm
app = FastAPI()

settings = config.Settings()

print(settings)
# 定义请求体数据模型
class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None
class ChatRequest(BaseModel):
    message: str 
    session_id: str = "default"
    temperature: float = Field(ge=0.0, le=2.0)
    max_tokens: int = Field(ge=1, le=1024*3)

class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

class ChatResponse(BaseModel):
    session_id: str
    message: str
    model: str
    usage: Usage | None

@app.post("/items/")
async def create_item(item: Item):
    """创建新商品，接收 JSON 请求体"""
    return item

@app.get("/tiems/{item_id}")
async def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q" : q}

@app.get("/health")
async def chat_health():
    return {"status": "ok", "service" : "ai-backend"}

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail={
            "error": "bad_request",
            "message": "message 不能为空"
        })
    try:
        response = llm.llm_chat(req.message, req.temperature, req.max_tokens)
    except llm.LLMError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e
    result = ChatResponse(session_id=req.session_id,
                          message=response.choices[0].message.content,
                          model=settings.OPENAI_MODEL,
                          usage=Usage(
                                prompt_tokens = response.usage.prompt_tokens,
                                completion_tokens = response.usage.completion_tokens,
                                total_tokens = response.usage.total_tokens
                          )if response.usage else None
                        )
    return result

# 1. 定义依赖函数
def common_parameters(q: str | None = None, skip: int = 0, limit: int = 100):
    return {"q": q, "skip": skip, "limit": limit}


# 2. 在路由中使用依赖
@app.get("/items/")
async def read_items(commons: dict = Depends(common_parameters)):
    # commons 接收依赖函数的返回值
    return commons


@app.get("/users/")
async def read_users(commons: dict = Depends(common_parameters)):
    # 多个路由可以复用同一个依赖
    return commons

#uvicorn app.main:app --reload --port 18001