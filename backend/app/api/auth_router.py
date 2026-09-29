"""
Authentication and Device Registration API Router
"""
import uuid
import secrets
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.config import settings
from backend.app.models.auth import User, DeviceNode
from backend.app.core.security import (
    hash_password,
    verify_password,
    hash_token,
    create_access_token,
    get_current_token_payload,
    get_current_user_or_device
)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication & Devices"])

class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=8)
    admin_secret: Optional[str] = None

class UserLoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: Optional[str] = None
    username: Optional[str] = None

class DeviceRegisterRequest(BaseModel):
    device_id: str = Field(..., min_length=4, max_length=64, description="Unique client identifier (UUID or hardware ID)")
    name: str = Field(..., min_length=2, max_length=128)
    device_type: str = Field("phone", description="phone | laptop | desktop | server | smart_device")
    platform: Optional[str] = "Android"
    capabilities: List[str] = Field(default_factory=list)

class DeviceRegisterResponse(BaseModel):
    device_id: str
    name: str
    device_token: str
    access_token: str
    capabilities: List[str]

class DeviceResponse(BaseModel):
    id: str
    name: str
    device_type: str
    platform: Optional[str]
    is_active: bool
    is_online: bool
    capabilities: List[str]
    last_seen: Optional[datetime]

@router.post("/register", response_model=TokenResponse)
def register_user(req: UserRegisterRequest, db: Session = Depends(get_db)):
    """Registers a new user or the root admin user."""
    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    is_admin = False
    if req.admin_secret and req.admin_secret == settings.ADMIN_PASSWORD:
        is_admin = True
    elif db.query(User).count() == 0:
        # First registered user is automatically admin
        is_admin = True

    new_user = User(
        username=req.username,
        hashed_password=hash_password(req.password),
        is_admin=is_admin,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"sub": new_user.id, "type": "user", "username": new_user.username, "is_admin": new_user.is_admin})
    return TokenResponse(
        access_token=token,
        expires_in=settings.JARVIS_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=new_user.id,
        username=new_user.username
    )

@router.post("/login", response_model=TokenResponse)
def login_user(req: UserLoginRequest, db: Session = Depends(get_db)):
    """Authenticates a user and returns an access token."""
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is deactivated")

    token = create_access_token({"sub": user.id, "type": "user", "username": user.username, "is_admin": user.is_admin})
    return TokenResponse(
        access_token=token,
        expires_in=settings.JARVIS_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user.id,
        username=user.username
    )

@router.post("/devices/register", response_model=DeviceRegisterResponse)
def register_device(
    req: DeviceRegisterRequest,
    db: Session = Depends(get_db),
    auth_data: Optional[dict] = Depends(get_current_user_or_device)
):
    """Enrolls a client device (Android phone or Windows laptop) and issues a long-lived device token."""
    if not settings.ALLOW_DEVICE_REGISTRATION:
        raise HTTPException(status_code=403, detail="Device registration is disabled")

    user_id = auth_data.get("user_id") if auth_data and auth_data.get("type") == "user" else None

    # Generate a cryptographically secure device secret token
    raw_device_token = f"jarvis_dev_{secrets.token_urlsafe(32)}"
    token_hash = hash_token(raw_device_token)

    device = db.query(DeviceNode).filter(DeviceNode.id == req.device_id).first()
    if device:
        device.name = req.name
        device.device_type = req.device_type
        device.platform = req.platform
        device.capabilities = req.capabilities
        device.api_token_hash = token_hash
        device.is_active = True
        device.last_seen = datetime.now(timezone.utc)
        if user_id:
            device.user_id = user_id
    else:
        device = DeviceNode(
            id=req.device_id,
            user_id=user_id,
            name=req.name,
            device_type=req.device_type,
            platform=req.platform,
            capabilities=req.capabilities,
            api_token_hash=token_hash,
            is_active=True,
            is_online=True,
            last_seen=datetime.now(timezone.utc)
        )
        db.add(device)

    db.commit()
    db.refresh(device)

    # Generate JWT for the device
    access_token = create_access_token({
        "sub": device.id,
        "type": "device",
        "device_type": device.device_type,
        "capabilities": device.capabilities
    })

    return DeviceRegisterResponse(
        device_id=device.id,
        name=device.name,
        device_token=raw_device_token,
        access_token=access_token,
        capabilities=device.capabilities or []
    )

@router.get("/devices", response_model=List[DeviceResponse])
def list_devices(db: Session = Depends(get_db), auth_data: dict = Depends(get_current_user_or_device)):
    """Lists all enrolled devices."""
    devices = db.query(DeviceNode).all()
    return [
        DeviceResponse(
            id=d.id,
            name=d.name,
            device_type=d.device_type,
            platform=d.platform,
            is_active=d.is_active,
            is_online=d.is_online,
            capabilities=d.capabilities or [],
            last_seen=d.last_seen
        )
        for d in devices
    ]

@router.delete("/devices/{device_id}")
def revoke_device(device_id: str, db: Session = Depends(get_db), auth_data: dict = Depends(get_current_user_or_device)):
    """Revokes a device's access to JARVIS."""
    device = db.query(DeviceNode).filter(DeviceNode.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    device.is_active = False
    device.is_online = False
    db.commit()
    return {"status": "success", "message": f"Device {device_id} revoked"}

@router.get("/me")
def get_current_profile(auth_data: dict = Depends(get_current_user_or_device)):
    """Returns the authenticated entity's profile information."""
    if auth_data["type"] == "user":
        u = auth_data["entity"]
        return {"type": "user", "id": u.id, "username": u.username, "is_admin": u.is_admin}
    else:
        d = auth_data["entity"]
        return {
            "type": "device",
            "id": d.id,
            "name": d.name,
            "device_type": d.device_type,
            "capabilities": d.capabilities,
            "is_online": d.is_online
        }
