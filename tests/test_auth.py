"""
Unit & Integration Tests for Security, Auth, and Device Management
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from backend.app.database import Base, get_db
from backend.app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    sanitize_secrets
)
from backend.app.models.auth import User, DeviceNode
from backend.app.api.auth_router import router
from fastapi import FastAPI

from sqlalchemy.pool import StaticPool

# Test SQLite in-memory DB
TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()
app.include_router(router)
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

def test_password_hashing():
    plain = "SuperSecurePassword123!"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_jwt_token_lifecycle():
    data = {"sub": "user-12345", "type": "user", "username": "tony_stark"}
    token = create_access_token(data)
    assert isinstance(token, str)

    payload = decode_access_token(token)
    assert payload["sub"] == "user-12345"
    assert payload["username"] == "tony_stark"
    assert "exp" in payload

def test_secret_sanitization():
    raw_log = "Error connecting with api_key: 'sk-abcdef1234567890abcdef' or token=ghp_12345678901234567890"
    sanitized = sanitize_secrets(raw_log)
    assert "sk-abcdef1234567890abcdef" not in sanitized
    assert "ghp_12345678901234567890" not in sanitized
    assert "***REDACTED_SECRET***" in sanitized

def test_user_registration_and_login():
    client = TestClient(app)

    # Register Admin User
    reg_resp = client.post("/api/v1/auth/register", json={
        "username": "tony",
        "password": "StarkPassword2026!"
    })
    assert reg_resp.status_code == 200
    token_data = reg_resp.json()
    assert "access_token" in token_data
    assert token_data["username"] == "tony"

    # Login
    login_resp = client.post("/api/v1/auth/login", json={
        "username": "tony",
        "password": "StarkPassword2026!"
    })
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()

    # Invalid Login
    fail_resp = client.post("/api/v1/auth/login", json={
        "username": "tony",
        "password": "IncorrectPassword"
    })
    assert fail_resp.status_code == 401

def test_device_enrollment_and_revocation():
    client = TestClient(app)

    # First register user to get token
    reg_resp = client.post("/api/v1/auth/register", json={
        "username": "admin_user",
        "password": "StarkPassword2026!"
    })
    auth_header = {"Authorization": f"Bearer {reg_resp.json()['access_token']}"}

    # Register Android phone node
    phone_resp = client.post("/api/v1/auth/devices/register", json={
        "device_id": "phone-android-pixel-9",
        "name": "Tony's Pixel 9 Pro",
        "device_type": "phone",
        "platform": "Android 15",
        "capabilities": ["microphone", "speaker", "notifications"]
    }, headers=auth_header)

    assert phone_resp.status_code == 200
    phone_data = phone_resp.json()
    assert phone_data["device_id"] == "phone-android-pixel-9"
    assert "device_token" in phone_data
    assert "access_token" in phone_data

    # Register Laptop node
    laptop_resp = client.post("/api/v1/auth/devices/register", json={
        "device_id": "laptop-thinkpad-x1",
        "name": "Tony's Dev Laptop",
        "device_type": "laptop",
        "platform": "Windows 11",
        "capabilities": ["terminal", "filesystem", "build_tools"]
    }, headers=auth_header)
    assert laptop_resp.status_code == 200

    # List enrolled devices
    list_resp = client.get("/api/v1/auth/devices", headers=auth_header)
    assert list_resp.status_code == 200
    devices = list_resp.json()
    assert len(devices) == 2

    # Revoke laptop
    del_resp = client.delete("/api/v1/auth/devices/laptop-thinkpad-x1", headers=auth_header)
    assert del_resp.status_code == 200

    # Verify laptop is deactivated
    list_after = client.get("/api/v1/auth/devices", headers=auth_header).json()
    laptop_node = next(d for d in list_after if d["id"] == "laptop-thinkpad-x1")
    assert laptop_node["is_active"] is False
