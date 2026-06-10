from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, Header
from jose import JWTError, jwt

from core.config import settings
from core.exceptions import AppException


PLAYER_TOKEN_AUDIENCE = "segmentflow-player"


def create_player_token(
    org_id: str,
    video_id: str,
    anonymous_user_key: str | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=12))
    payload: dict = {
        "orgId": org_id,
        "videoId": video_id,
        "aud": PLAYER_TOKEN_AUDIENCE,
        "exp": expire,
    }
    if anonymous_user_key:
        payload["anonymousUserKey"] = anonymous_user_key
    return jwt.encode(
        payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def decode_player_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        audience=PLAYER_TOKEN_AUDIENCE,
    )


def get_player_context(
    x_player_token: Annotated[str | None, Header(alias="X-Player-Token")] = None,
) -> dict:
    if not x_player_token:
        raise AppException(
            code="PLAYER_TOKEN_INVALID",
            message="X-Player-Token header is required.",
            status_code=401,
        )
    try:
        payload = decode_player_token(x_player_token)
    except JWTError:
        raise AppException(
            code="PLAYER_TOKEN_INVALID",
            message="Invalid or expired player token.",
            status_code=401,
        )
    if "orgId" not in payload or "videoId" not in payload:
        raise AppException(
            code="PLAYER_TOKEN_INVALID",
            message="Player token missing required claims.",
            status_code=401,
        )
    return payload


PlayerContext = Annotated[dict, Depends(get_player_context)]
