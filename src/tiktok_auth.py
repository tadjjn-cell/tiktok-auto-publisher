import logging

import httpx

logger = logging.getLogger(__name__)

TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"


def refresh_access_token(client_key: str, client_secret: str, refresh_token: str) -> dict:
    """
    Exchange a refresh_token for a fresh access_token (TikTok access tokens expire in ~24h).
    TikTok may rotate the refresh_token itself on each call -- callers must persist the
    returned refresh_token for next time, not just the access_token.
    """
    with httpx.Client(timeout=30) as client:
        resp = client.post(
            TOKEN_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "client_key": client_key,
                "client_secret": client_secret,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        if "access_token" not in data:
            raise Exception(f"TikTok token refresh failed: {data}")
        return data
