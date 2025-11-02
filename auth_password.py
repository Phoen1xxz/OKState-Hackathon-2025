"""
auth_password.py

Simple Auth0 Resource Owner Password Grant (username/password) example.

WARNING: Exchanging raw usernames and passwords for tokens is insecure for public clients
and is generally discouraged. Prefer Authorization Code + PKCE for user-facing apps.

Use cases: quick testing, legacy systems, or trusted backend scripts where secret storage is secure.

Usage:
  - copy `.env.example` to `.env` and set AUTH0_DOMAIN, AUTH0_CLIENT_ID and optionally AUTH0_CLIENT_SECRET
  - set AUTH0_AUDIENCE if you want an access token for an API
  - optionally set AUTH0_REALM to use a database connection (Auth0 realm / connection name)
  - python auth_password.py

Dependencies: requests, python-dotenv, python-jose[cryptography]

This script accepts username/password via prompt (no echo for password) and prints tokens on success.
"""
import os
import getpass
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")  # optional; required for some app types
AUDIENCE = os.getenv("AUTH0_AUDIENCE")  # optional
REALM = os.getenv("AUTH0_REALM")  # optional: name of database connection / realm
SCOPE = os.getenv("AUTH0_SCOPES", "openid profile email offline_access")

if not AUTH0_DOMAIN or not CLIENT_ID:
    raise SystemExit("Please set AUTH0_DOMAIN and AUTH0_CLIENT_ID in your .env file")


def perform_password_grant(username: str, password: str) -> Optional[dict]:
    token_url = f"https://{AUTH0_DOMAIN}/oauth/token"

    # Choose grant type depending on whether a realm is used
    if REALM:
        grant_type = "http://auth0.com/oauth/grant-type/password-realm"
    else:
        grant_type = "password"

    payload = {
        "grant_type": grant_type,
        "username": username,
        "password": password,
        "client_id": CLIENT_ID,
        "scope": SCOPE,
    }

    if AUDIENCE:
        payload["audience"] = AUDIENCE
    if CLIENT_SECRET:
        payload["client_secret"] = CLIENT_SECRET
    if REALM:
        payload["realm"] = REALM

    headers = {"Content-Type": "application/json"}

    resp = requests.post(token_url, json=payload, headers=headers)

    try:
        body = resp.json()
    except Exception:
        print("Unexpected response from token endpoint (non-json)")
        print(resp.text)
        return None

    if resp.status_code == 200:
        domain = AUTH0_DOMAIN
        access = body.get("access_token")
        id_token = body.get("id_token")
        if access and domain:
            try:
                resp = requests.get(f"https://{domain}/userinfo", headers={"Authorization": f"Bearer {access}"}, timeout=5)
                if resp.ok:
                    data = resp.json()
                    return data.get("sub")
            except Exception:
                pass
        return 

    # Common errors: invalid_grant (bad credentials), unauthorized_client, invalid_request
    print("Error from Auth0 token endpoint:")
    print(body)
    return None


def try_decode_id_token(id_token: str) -> Optional[dict]:
    try:
        from jose import jwt
        return jwt.get_unverified_claims(id_token)
    except Exception:
        return None


def main():
    print("Auth0 username/password token exchange (Resource Owner Password Grant)")
    print("WARNING: this will send raw passwords to Auth0. Only use for trusted scripts/tests.")

    username = input("username: ")
    password = getpass.getpass("password: ")

    print("Requesting token from Auth0...")
    tokens = perform_password_grant(username, password)
    if not tokens:
        print("Authentication failed.")
        return

    access_token = tokens.get("access_token")
    id_token = tokens.get("id_token")
    refresh_token = tokens.get("refresh_token")

    print("\nTokens received:")
    if access_token:
        print("Access token:", access_token[:40] + "...")
    if id_token:
        print("ID token:", id_token[:40] + "...")
    if refresh_token:
        print("Refresh token:", refresh_token[:40] + "...")

    if id_token:
        claims = try_decode_id_token(id_token)
        if claims:
            print("\nID token claims (unverified):")
            for k, v in claims.items():
                print(f"  {k}: {v}")

    # Optional: show full response if you want to copy tokens
    print("\nFull token response:")
    print(tokens)


if __name__ == "__main__":
    main()
