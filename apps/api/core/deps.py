import uuid
from typing import Annotated

from fastapi import Depends, Header, Path, Request
from jose import JWTError

from core.auth import decode_access_token
from core.exceptions import AppException


def get_current_user(request: Request, authorization: str | None = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise AppException(
            code="INVALID_TOKEN", message="Bearer token required.", status_code=401
        )
    token = authorization.removeprefix("Bearer ")
    try:
        payload = decode_access_token(token)
    except JWTError:
        raise AppException(
            code="INVALID_TOKEN", message="Invalid or expired token.", status_code=401
        )
    request.state.user_id = payload["sub"]
    request.state.org_id = payload.get("orgId")
    request.state.org_role = payload.get("orgRole")
    return payload


CurrentUser = Annotated[dict, Depends(get_current_user)]


def require_org_context(
    user: CurrentUser,
    orgId: uuid.UUID = Path(...),
) -> uuid.UUID:
    if str(user.get("orgId")) != str(orgId):
        raise AppException(
            code="FORBIDDEN",
            message="Organization context mismatch.",
            status_code=403,
        )
    return orgId


OrgContext = Annotated[uuid.UUID, Depends(require_org_context)]


class RoleGuard:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: CurrentUser) -> dict:
        if user.get("orgRole") not in self.allowed_roles:
            raise AppException(
                code="FORBIDDEN",
                message=f"Role must be one of: {', '.join(self.allowed_roles)}",
                status_code=403,
            )
        return user


require_admin = RoleGuard(["admin"])
require_operator = RoleGuard(["admin", "operator"])
require_analyst = RoleGuard(["admin", "operator", "analyst"])
