from fastapi import APIRouter, Depends, Request

from core.auth import create_access_token, hash_password, verify_password
from core.database import get_db
from core.exceptions import AppException
from models.core import OrganizationMember, User
from schemas.auth import LoginRequest, TokenData
from schemas.response import Meta, SuccessResponse
from sqlalchemy.orm import Session

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=SuccessResponse)
async def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise AppException(
            code="INVALID_CREDENTIALS",
            message="이메일 또는 비밀번호가 올바르지 않습니다.",
            status_code=401,
        )

    membership = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == user.id)
        .first()
    )
    if not membership:
        raise AppException(
            code="NO_ORGANIZATION",
            message="소속 조직이 없습니다.",
            status_code=403,
        )

    token = create_access_token(
        user_id=str(user.id),
        org_id=str(membership.organization_id),
        org_role=membership.org_role,
    )

    return SuccessResponse(
        data=TokenData(accessToken=token).model_dump(),
        meta=Meta(requestId=request.state.request_id),
    )
