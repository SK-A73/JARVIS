"""
Security, Cryptography, and Authentication Helper
Provides JWT generation/verification, password hashing, and sensitive data masking.
"""
import hashlib
import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Union
import bcrypt
from jose import JWTError, jwt
from fastapi import HTTPException, Security, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db

security_bearer = HTTPBearer(auto_error=False)

ALGORITHM = "HS256"

# Regex patterns for masking sensitive information in logs and agent outputs
SENSITIVE_PATTERNS = [
    re.compile(r'(?i)(?:api_key|token|secret|password|bearer|authorization)[\s:=]+([\'"]?)([a-zA-Z0-9_\-\.]{8,})\1'),
    re.compile(r'sk-[a-zA-Z0-9]{20,}'),
    re.compile(r'ghp_[a-zA-Z0-9]{20,}'),
]

def hash_password(password: str) -> str:
    """Hashes a plain text password using bcrypt."""
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain text password against a bcrypt hash."""
    pwd_bytes = plain_password.encode("utf-8")[:72]
    try:
        return bcrypt.checkpw(pwd_bytes, hashed_password.encode("utf-8"))
    except Exception:
        return False

def hash_token(token: str) -> str:
    """Hashes a device or API token using SHA-256 for storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generates a signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JARVIS_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, settings.JARVIS_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes and validates a JWT token."""
    try:
        payload = jwt.decode(token, settings.JARVIS_SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired authentication token: {str(exc)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

def sanitize_secrets(text: str) -> str:
    """Masks secret keys, tokens, and passwords from logs, messages, and model context."""
    if not text or not isinstance(text, str):
        return text
    sanitized = text
    for pattern in SENSITIVE_PATTERNS:
        sanitized = pattern.sub(r'***REDACTED_SECRET***', sanitized)
    return sanitized

def get_current_token_payload(credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer)) -> Dict[str, Any]:
    """FastAPI dependency to extract and validate the JWT token payload."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization Header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_access_token(credentials.credentials)

def get_current_user_or_device(
    payload: Dict[str, Any] = Depends(get_current_token_payload),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Authenticates either a user or an enrolled device node."""
    from backend.app.models.auth import User, DeviceNode

    sub = payload.get("sub")
    entity_type = payload.get("type", "user")

    if not sub:
        raise HTTPException(status_code=401, detail="Invalid token subject")

    if entity_type == "device":
        device = db.query(DeviceNode).filter(DeviceNode.id == sub, DeviceNode.is_active == True).first()
        if not device:
            raise HTTPException(status_code=401, detail="Device not found or deactivated")
        return {"type": "device", "entity": device, "device_id": device.id}
    else:
        user = db.query(User).filter(User.id == sub, User.is_active == True).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found or deactivated")
        return {"type": "user", "entity": user, "user_id": user.id}
