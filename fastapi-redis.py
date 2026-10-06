# from fastapi import FastAPI
# import redis
# import uvicorn
# app = FastAPI(title="fastapi-redis")
# r = redis.Redis(host='127.0.0.1', port=6379, db=0,decode_responses=True)

# @app.post('/room/{room_id}/set')
# def set_room(room_id: int, status: str):
#     r.set(room_id, status)
#     return {"message": f"Room {room_id} set to {status}"}

# @app.get('/room/{room_id}')
# def get_room(room_id: int):
#     status= r.get(room_id)
#     if status is None:
#         return {"message": f"Room {room_id} not found"} 

# @app.get('/room')
# def get_all_rooms():
#     rooms = r.keys()
#     return {"rooms": rooms}

# if __name__ == "__fastapi-redis__":
#     uvicorn.run("main:app", host="127.0.0.1", port=8000) 
from fastapi import FastAPI
from pydantic import BaseModel
import redis
import uvicorn

app = FastAPI(title="fastapi-redis")
r = redis.Redis(host='127.0.0.1', port=6379, db=0,decode_responses=True)

# 定义接收JSON的模型
class RoomStatusInput(BaseModel):
    status: str

@app.post('/room/{room_id}/set')
def set_room(room_id: int, data: RoomStatusInput):
    r.set(f"room:{room_id}", data.status)
    return {"message": f"Room {room_id} set to {data.status}"}

@app.get('/room/{room_id}')
def get_room(room_id: int):
    status = r.get(f"room:{room_id}")
    if status is None:
        return {"message": f"Room {room_id} not found"}
    return {"room_id":room_id, "status":status}

@app.get('/rooms')
def get_all_rooms():
    keys = r.keys("room:*")
    result = {}
    for k in keys:
        room_id = k.split(":")[1]
        result[room_id] = r.get(k)
    return {"rooms": result}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
