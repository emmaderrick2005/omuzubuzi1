"""MOD-07: Notifications"""
from fastapi import APIRouter, Depends
from app.utils.auth import get_current_user

router = APIRouter()

@router.get("/")
async def get_notifications(user_data: dict = Depends(get_current_user)):
    """FR-07-02: In-app notifications — implement with WebSocket/SSE"""
    return {"notifications": [], "message": "Connect via WebSocket at /ws/notifications"}
