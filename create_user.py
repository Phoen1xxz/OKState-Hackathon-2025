"""
create_user.py

Create a new Auth0 database (username/password) user from a script using Auth0's
/dbconnections/signup endpoint.

Usage:
  - copy `.env.example` to `.env` and set AUTH0_DOMAIN and AUTH0_CLIENT_ID
  - set AUTH0_REALM to your DB connection name (default: Username-Password-Authentication)
  - python create_user.py

This is a backend-only operation. Do NOT run this from browser/SPA code or commit secrets.

Notes:
  - This endpoint accepts client_id (no management-token required), which makes it easy for
    backend scripts to create users. For more control (roles, metadata, email verification),
    use the Management API (requires client credentials and proper scopes).
  - The connection name is the Auth0 Database Connection name (check Dashboard → Authentication → Database).
"""
import os
import getpass
import requests
from dotenv import load_dotenv

load_dotenv()

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
CONNECTION = os.getenv("AUTH0_REALM", "Username-Password-Authentication")

if not AUTH0_DOMAIN or not CLIENT_ID:
    raise SystemExit("Please set AUTH0_DOMAIN and AUTH0_CLIENT_ID in your .env file")


class Auth0Error(Exception):
    """Exception raised when Auth0 returns an error response.

    The .info attribute contains the parsed JSON body returned by Auth0 (if any).
    """

    def __init__(self, info):
        super().__init__(info)
        self.info = info


def create_user(email: str, password: str, connection: str) -> dict:
    """Create a user in an Auth0 Database Connection via /dbconnections/signup.

    Raises Auth0Error on failure with the response body attached to the exception.
    """
    url = f"https://{AUTH0_DOMAIN}/dbconnections/signup"
    payload = {
        "client_id": CLIENT_ID,
        "email": email,
        "password": password,
        "connection": connection,
    }
    resp = requests.post(url, json=payload)
    try:
        body = resp.json()
    except Exception:
        # Non-JSON response
        raise Auth0Error({"message": "Non-JSON response from Auth0", "text": resp.text, "status": resp.status_code})

    if resp.status_code in (200, 201):
        return body

    # Raise structured error for the caller to handle
    raise Auth0Error(body)


def main():
    print("Create Auth0 DB user (username/password)")
    email = input("email: ")
    password = getpass.getpass("password: ")

    print(f"Creating user in connection '{CONNECTION}'...")
    result = create_user(email, password, CONNECTION)
    print("Success:", result)


if __name__ == "__main__":
    main()
