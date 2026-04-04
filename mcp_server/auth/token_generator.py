from __future__ import annotations

import datetime
import os

import jwt as pyjwt

from mcp_server.auth.jwt_middleware import JWT_ALGORITHM, JWT_SECRET


def generate_token(
    subject: str = "mcp-agent-client",
    expires_in_minutes: int = 60,
) -> str:
    """Generate a signed JWT token for local testing.

    Not used in production — Azure AD issues tokens there.
    Use this to generate tokens for:
    - Manual curl testing of MCP endpoints
    - Integration test fixtures in conftest.py

    Args:
        subject: 'sub' claim — identifies the token holder
        expires_in_minutes: token lifetime in minutes (default 60)

    Returns:
        Signed JWT token string
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    jwt_payload = {
        "sub": subject,
        "iat": now,
        "exp": now + datetime.timedelta(minutes=expires_in_minutes),
        "role": "mcp-client",
    }
    return pyjwt.encode(jwt_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def generate_expired_token(subject: str = "expired-test-client") -> str:
    """Generate a token that is already expired — for testing auth rejection.

    Used in integration tests to verify the server correctly returns 401
    for expired tokens.
    """
    past = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=2)
    jwt_payload = {
        "sub": subject,
        "iat": past - datetime.timedelta(hours=1),
        "exp": past,
        "role": "mcp-client",
    }
    return pyjwt.encode(jwt_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


if __name__ == "__main__":
    # Run directly to generate a token for manual curl testing:
    #   python -m mcp_server.auth.token_generator
    token = generate_token()
    print("Bearer token (valid 60 min):")
    print(token)
    print()
    print("Use with curl:")
    print(f'  -H "Authorization: Bearer {token}"')