from fastapi import APIRouter
add_room = APIRouter()

@add_room.get("/1")
async def set_room():
    return {"message":"add_room page"}