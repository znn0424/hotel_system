from typing import Any
from datetime import datetime, timedelta, timezone

import jwt
import redis
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from tortoise.contrib.fastapi import register_tortoise
from tortoise.exceptions import DBConnectionError, IntegrityError

from api.add_room import add_room
from model import Room
from settings import (
    ADMIN_PASSWORD,
    ADMIN_USERNAME,
    JWT_ALGORITHM,
    JWT_EXPIRE_MINUTES,
    JWT_SECRET_KEY,
    TORTOISE_ORM,
)


app = FastAPI(
    title="酒店房态管理 API",
    description="提供酒店房间状态的新增、查询和删除接口。",
    version="1.0.0",
)

# Vue 开发服务器默认使用 5173 端口，同时允许 localhost 和 127.0.0.1。
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

r = redis.Redis(
    host="127.0.0.1",
    port=6379,
    db=0,
    decode_responses=True,
)

templates = Jinja2Templates(directory="template")

register_tortoise(
    app,
    config=TORTOISE_ORM,
    generate_schemas=True,
)

app.include_router(add_room, prefix="/api", tags=["其他"])


class RoomCreate(BaseModel):
    """新增或更新房间状态的请求体。"""

    room_id: int
    status: str


class AdminLogin(BaseModel):
    """管理员登录请求体。"""

    username: str
    password: str


def error_response(
    status_code: int,
    message: str,
    detail: Any = None,
) -> JSONResponse:
    """生成统一格式的错误响应。"""
    return JSONResponse(
        status_code=status_code,
        content={
            "code": status_code,
            "message": message,
            "detail": detail,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """处理请求参数校验异常。"""
    return error_response(
        status_code=422,
        message="请求参数校验失败",
        detail=jsonable_encoder(exc.errors()),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    """处理接口主动抛出的 HTTP 异常。"""
    return error_response(
        status_code=exc.status_code,
        message=str(exc.detail),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """兜底处理未预期异常，避免向前端暴露堆栈信息。"""
    return error_response(
        status_code=500,
        message="服务器内部错误",
    )


@app.get(
    "/",
    summary="打开首页",
    description="返回酒店房态管理的服务端页面。",
    tags=["基础"],
)
async def read_root(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="home.html",
    )


@app.post(
    "/admin/login",
    summary="管理员登录",
    description="校验管理员账号密码并返回 JWT token。",
    tags=["管理员"],
)
async def admin_login(data: AdminLogin):
    if data.username != ADMIN_USERNAME or data.password != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误",
        )

    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=JWT_EXPIRE_MINUTES
    )
    token = jwt.encode(
        {
            "sub": data.username,
            "exp": expires_at,
        },
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )
    return {
        "access_token": token,
        "token_type": "bearer",
    }


@app.post(
    "/room/set",
    summary="新增或更新房间状态",
    description=(
        "先写入 MySQL，数据库操作成功后再更新 Redis 缓存。"
        "如果 Redis 更新失败，接口会返回服务器错误，数据库记录仍然保留。"
    ),
    response_description="房间状态保存成功",
    tags=["房间管理"],
)
async def set_room(data: RoomCreate):
    try:
        room_obj, created = await Room.get_or_create(
            room_id=data.room_id,
            defaults={"status": data.status},
        )
        if not created:
            room_obj.status = data.status
            await room_obj.save(update_fields=["status"])

        # 数据库成功后再更新缓存，保证数据库是主数据源。
        r.set(f"room:{data.room_id}", data.status)
        return {"message": f"Room {data.room_id} set to {data.status}"}
    except (DBConnectionError, IntegrityError) as exc:
        raise HTTPException(
            status_code=500,
            detail="房间状态写入数据库失败",
        ) from exc
    except redis.RedisError as exc:
        raise HTTPException(
            status_code=500,
            detail="房间状态已写入数据库，但 Redis 缓存更新失败",
        ) from exc


@app.get(
    "/room/{room_id}",
    summary="查询单个房间状态",
    description="根据房间号查询 Redis 中缓存的房间状态。",
    response_description="房间号和房间状态",
    tags=["房间管理"],
)
async def get_room(room_id: int):
    try:
        status = r.get(f"room:{room_id}")
        if status is None:
            raise HTTPException(
                status_code=404,
                detail=f"Room {room_id} not found",
            )
        return {"room_id": room_id, "status": status}
    except redis.RedisError as exc:
        raise HTTPException(
            status_code=500,
            detail="读取 Redis 房间状态失败",
        ) from exc


@app.get(
    "/room",
    summary="查询全部房间状态",
    description="返回 Redis 中所有已缓存的房间状态。",
    response_description="以房间号为键、状态为值的对象",
    tags=["房间管理"],
)
async def get_all_rooms():
    try:
        rooms = r.keys("room:*")
        room_status = {}
        for room_key in rooms:
            room_id = room_key.split(":", 1)[1]
            room_status[room_id] = r.get(room_key)
        return room_status
    except redis.RedisError as exc:
        raise HTTPException(
            status_code=500,
            detail="读取 Redis 房间状态失败",
        ) from exc


@app.delete(
    "/room/{room_id}",
    summary="删除房间",
    description=(
        "先删除 MySQL 中的房间记录，数据库删除成功后再删除 Redis 缓存。"
        "如果数据库中没有该房间，也会清理可能残留的 Redis 缓存。"
    ),
    response_description="房间删除成功",
    tags=["房间管理"],
)
async def delete_room(room_id: int):
    try:
        room_obj = await Room.get_or_none(room_id=room_id)
        if room_obj is None:
            # 清理可能存在的脏缓存，然后返回资源不存在。
            r.delete(f"room:{room_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Room {room_id} not found",
            )

        await room_obj.delete()
        r.delete(f"room:{room_id}")
        return {"message": f"Room {room_id} deleted"}
    except redis.RedisError as exc:
        raise HTTPException(
            status_code=500,
            detail="房间已从数据库删除，但 Redis 缓存删除失败",
        ) from exc
    except DBConnectionError as exc:
        raise HTTPException(
            status_code=500,
            detail="删除房间数据库记录失败",
        ) from exc


app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
