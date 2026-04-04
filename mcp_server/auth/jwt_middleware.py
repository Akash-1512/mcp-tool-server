from __future__ import annotations

import logging
import os

import jwt as pyjwt
from fastapi import Request

from mcp_server.exceptions import AuthenticationError

logger = logging.getLogger(__name__)

# LOCAL DEMO — PyJWT with local HS256 signing key
JWT_SECRET = os.getenv("JWT_SECRET", "local-dev-secret-minimum-32-chars-long-change-this")
JWT_ALGORITHM = "HS256"

# ─────────────────────────────────────────────────────────────────────────────
# [PRODUCTION] Azure AD token validation — uncomment to enable
# Requires: AZURE_AD_TENANT_ID, AZURE_AD_CLIENT_ID in .env
# Validates RS256 tokens issued by Azure AD against Microsoft's JWKS endpoint.
# ─────────────────────────────────────────────────────────────────────────────
# import httpx
# from jwt import PyJWKClient
# _AZURE_JWKS_URL = (
#     f"https://login.microsoftonline.com/"
#     f"{os.getenv('AZURE_AD_TENANT_ID')}/discovery/v2.0/keys"
# )
# def verify_token_azure(token: str) -> dict:
#     jwks_client = PyJWKClient(_AZURE_JWKS_URL)
#     signing_key = jwks_client.get_signing_key_from_jwt(token)
#     return pyjwt.decode(
#         token,
#         signing_key.key,
#         algorithms=["RS256"],
#         audience=os.getenv("AZURE_AD_CLIENT_ID"),
#     )


def verify_token(token: str) -> dict:
    """Verify a JWT token and return its decoded claims.

    Raises AuthenticationError on:
    - Expired token (ExpiredSignatureError)
    - Invalid signature or malformed token (InvalidTokenError)

    The returned claims dict contains at minimum: 'sub', 'exp'.
    Additional claims (e.g. 'role', 'client_id') can be added by
    the token generator and validated here.
    """
    try:
        jwt_claims = pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return jwt_claims
    except pyjwt.ExpiredSignatureError as e:
        raise AuthenticationError("Token has expired") from e
    except pyjwt.InvalidTokenError as e:
        raise AuthenticationError(f"Invalid token: {e}") from e


def extract_bearer_token(request: Request) -> str:
    """Extract Bearer token from the Authorization header.

    Raises AuthenticationError if:
    - Authorization header is missing
    - Header value does not start with 'Bearer '
    - Token string is empty after stripping
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise AuthenticationError("Authorization header is missing")
    if not auth_header.startswith("Bearer "):
        raise AuthenticationError(
            "Authorization header must use Bearer scheme: 'Bearer <token>'"
        )
    token = auth_header[len("Bearer "):