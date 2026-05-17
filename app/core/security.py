from fastapi import HTTPException, Header

def verify_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")):
    if x_api_key != "dev-secret-zhuzhucool":
        raise HTTPException(status_code=401, detail="Invalid API key")

def get_current_user_id(
    x_user_id: int = Header(alias="X-User-Id"),
) -> int:
    return x_user_id

