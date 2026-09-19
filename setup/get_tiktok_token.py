"""
Run this ONCE to authorize your TikTok account and generate an access/refresh token.

Unlike Google, TikTok's redirect_uri must be a real, pre-registered, verified URL
(usually your GitHub Pages URL) -- it can't be plain localhost. This script prints
the authorization URL for you to open in a browser; after you approve, TikTok
redirects your browser to that redirect_uri with a "?code=..." parameter. Paste
that full redirected URL back here to complete the exchange.
"""

import urllib.parse
import httpx

TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"

client_key = input("TIKTOK_CLIENT_KEY: ").strip()
client_secret = input("TIKTOK_CLIENT_SECRET: ").strip()
redirect_uri = input("Redirect URI (must match your TikTok app's registered redirect URI exactly): ").strip()

auth_url = (
    "https://www.tiktok.com/v2/auth/authorize/"
    f"?client_key={urllib.parse.quote(client_key)}"
    "&scope=user.info.basic,video.upload"
    "&response_type=code"
    f"&redirect_uri={urllib.parse.quote(redirect_uri)}"
    "&state=setup"
)

print("\n1) Open this URL in your browser and approve access with your TikTok account:\n")
print(auth_url)
print("\n2) After approving, your browser will redirect to a URL that starts with your redirect URI")
print("   and contains '?code=...'. Copy that FULL URL from the address bar and paste it below.\n")

redirected_url = input("Paste the full redirected URL here: ").strip()
parsed = urllib.parse.urlparse(redirected_url)
params = urllib.parse.parse_qs(parsed.query)
code = params.get("code", [None])[0]

if not code:
    raise SystemExit("Could not find '?code=' in that URL. Did you paste the full redirected address?")

resp = httpx.post(
    TOKEN_URL,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    data={
        "client_key": client_key,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    },
    timeout=30,
)
data = resp.json()

if "access_token" not in data:
    raise SystemExit(f"Token exchange failed: {data}")

print("\n=== COPY THESE — KEEP THEM SECRET ===\n")
print(f"TIKTOK_CLIENT_KEY={client_key}")
print(f"TIKTOK_CLIENT_SECRET={client_secret}")
print(f"TIKTOK_ACCESS_TOKEN={data['access_token']}")
print(f"TIKTOK_REFRESH_TOKEN={data['refresh_token']}")
print("\n=======================================")
print("Save these four as GitHub Secrets.")
