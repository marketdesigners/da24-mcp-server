import logging
from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel
from config import settings
from db.database import get_connection, release_connection
from db.models import ApiKeyRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin")


def _verify_admin(x_admin_secret: str | None) -> None:
    if x_admin_secret != settings.admin_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


class CreateKeyRequest(BaseModel):
    name: str

class PatchKeyRequest(BaseModel):
    is_active: bool


@router.post("/keys", status_code=status.HTTP_201_CREATED)
def create_key(body: CreateKeyRequest, x_admin_secret: str | None = Header(default=None)):
    _verify_admin(x_admin_secret)
    conn = get_connection()
    try:
        repo = ApiKeyRepository(conn)
        result = repo.create_key(body.name)
        logger.info("API key created for: %s", body.name)
        return result
    finally:
        release_connection(conn)


@router.get("/keys")
def list_keys(x_admin_secret: str | None = Header(default=None)):
    _verify_admin(x_admin_secret)
    conn = get_connection()
    try:
        return ApiKeyRepository(conn).list_keys()
    finally:
        release_connection(conn)


@router.patch("/keys/{key}")
def patch_key(key: str, body: PatchKeyRequest, x_admin_secret: str | None = Header(default=None)):
    _verify_admin(x_admin_secret)
    conn = get_connection()
    try:
        ApiKeyRepository(conn).set_active(key, body.is_active)
        return {"success": True, "key": key, "is_active": body.is_active}
    finally:
        release_connection(conn)


@router.delete("/keys/{key}")
def delete_key(key: str, x_admin_secret: str | None = Header(default=None)):
    _verify_admin(x_admin_secret)
    conn = get_connection()
    try:
        # Soft delete: is_active=0
        ApiKeyRepository(conn).set_active(key, False)
        logger.info("API key soft-deleted: %s", key)
        return {"success": True}
    finally:
        release_connection(conn)
