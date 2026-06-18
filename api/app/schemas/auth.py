"""
Authentication schemas.
"""

from pydantic import BaseModel

# ------------------------------------------------------
# Token response
# ------------------------------------------------------


class TokenResponse(BaseModel):
    """
    Schema returned on successful login or refresh.
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # access token lifetime in seconds


# ------------------------------------------------------
# Refresh request
# ------------------------------------------------------


class RefreshRequest(BaseModel):
    """
    Schema for the refresh endpoint.
    """

    refresh_token: str


# ------------------------------------------------------
# Token payload (decoded claims)
# ------------------------------------------------------


class TokenPayload(BaseModel):
    """
    Decoded JWT claims. Used for token verification (Phase 2).
    """

    sub: str
    email: str | None = None
    roles: list[str] = []
    type: str | None = None
    exp: int | None = None
