from fastapi import Depends, FastAPI
from pydantic import BaseModel
from app.core import config
app = FastAPI()

settings = config.Settings()

print(settings)
# 定义请求体数据模型
class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

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