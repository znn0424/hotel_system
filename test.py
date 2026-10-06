import redis
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.staticfiles import StaticFiles
from settings import TORTOISE_ORM
from model import Room
from tortoise.contrib.fastapi import register_tortoise
import uvicorn

app = FastAPI(title="test")
r = redis.Redis(host='127.0.0.1',port=6379,db=0,decode_responses=True)
# 文件夹名字 template，和这里一致
templates = Jinja2Templates(directory="template")
register_tortoise(
    app,
    config=TORTOISE_ORM,
    generate_schemas=True,
)

class Room_create(BaseModel):
    room_id:int
    status:str


@app.get("/")
def read_root(request :Request):
    return templates.TemplateResponse(
        request =request,
        name ="home.html"
    )

    # return {"msg":"首页正常，模板待测试"}



# @app.post("/room/set")
# def set_room(data:Room):
#     room_id = data.room_id
#     status = data.status
#     # 推荐key加前缀 room:
#     r.set(f"room:{room_id}", status)
#     return {"message":f"Room {room_id} set to {status}"}

@app.post("/room/set")
async def set_room(data:Room_create):
    room_id = data.room_id
    status = data.status
    # 推荐key加前缀 room:
    r.set(f"room:{room_id}", status)
    # 同步更新数据库
    room_obj, created = await Room.get_or_create(room_id=room_id, defaults={"status": status})
    if not created:
        room_obj.status = status
        await room_obj.save()
    return {"message":f"Room {room_id} set to {status}"}


# @app.post("/room/set")
# async def set_room(data:Room_create):
#     user =await Room.create(room_id= data.room_id, status= data.status)

#     return {
#         "message":f" {user.room_id} set to {user.status}"
#     }




@app.get("/room/{room_id}")
async def get_room(room_id:int):
    status = r.get(f"room:{room_id}")
    if status is None:
        return {"message":f"Room {room_id} not found"}
    return {"room_id":room_id,"status":status}


@app.get("/room")
def get_all_rooms():
    # 只获取 room: 开头的key，不要拿全部*
    rooms = r.keys("room:*")
    room_status = {}
    for room_key in rooms:
        room_id = room_key.split(":")[1]
        room_status[room_id] = r.get(room_key)
    return room_status

app.mount("/static", StaticFiles(directory="static"), name="static")



if __name__=="__main__":
    uvicorn.run(app,host="127.0.0.1",port=8001)
