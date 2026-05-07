"""
Customer 360 API client — authenticates with a Databricks service principal
and calls the app's REST API.

Usage:
    python call_api.py                        # stats + first 5 customers
    python call_api.py --email ada@example.com  # single customer profile
    python call_api.py --search lopez --limit 10
"""
import argparse
import json
import os
import sys

import requests

# ---------------------------------------------------------------------------
# Config — override with env vars or edit the defaults below
# ---------------------------------------------------------------------------
WORKSPACE_HOST = os.getenv(
    "DATABRICKS_HOST",
    "https://xxx-xx-xx-xxcloud.databricks.com",
)
CLIENT_ID = os.getenv("DATABRICKS_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("DATABRICKS_CLIENT_SECRET", "")  # always pass via env var

APP_URL = "https://xxx-xxx-xx.xxx-xxx-xx.aws.databricksapps.com"


def get_token() -> str:
    resp = requests.post(
        f"{WORKSPACE_HOST}/oidc/v1/token",
        auth=(CLIENT_ID, CLIENT_SECRET),
        data={"grant_type": "client_credentials", "scope": "all-apis"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


class Customer360Client:
    def __init__(self, token: str):
        self._session = requests.Session()
        self._session.headers["Authorization"] = f"Bearer {token}"
        self._base = APP_URL

    def _get(self, path: str, **params) -> dict | list:
        resp = self._session.get(f"{self._base}{path}", params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def health(self) -> dict:
        return self._get("/api/health")

    def stats(self) -> dict:
        return self._get("/api/stats")

    def list_customers(self, q: str | None = None, limit: int = 50) -> list[dict]:
        params = {"limit": limit}
        if q:
            params["q"] = q
        return self._get("/api/customers", **params)

    def get_customer(self, email: str) -> dict:
        return self._get(f"/api/customers/{email}")


def pretty(data) -> str:
    return json.dumps(data, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Customer 360 API client")
    parser.add_argument("--email", help="Fetch a single customer by email")
    parser.add_argument("--search", help="Search customers by name or email substring")
    parser.add_argument("--limit", type=int, default=5, help="Max rows to return (default 5)")
    args = parser.parse_args()

    if not CLIENT_SECRET:
        sys.exit(
            "Set DATABRICKS_CLIENT_SECRET env var before running.\n"
            "  export DATABRICKS_CLIENT_SECRET='your-secret'"
        )

    print("Minting OAuth token...")
    token = get_token()
    print("Token acquired.\n")

    client = Customer360Client(token)

    if args.email:
        print(f"--- Customer profile: {args.email} ---")
        print(pretty(client.get_customer(args.email)))
    elif args.search:
        print(f"--- Search: '{args.search}' (limit={args.limit}) ---")
        rows = client.list_customers(q=args.search, limit=args.limit)
        print(pretty(rows))
        print(f"\n{len(rows)} result(s)")
    else:
        print("--- Health ---")
        print(pretty(client.health()))

        print("\n--- Stats ---")
        print(pretty(client.stats()))

        print(f"\n--- Top {args.limit} customers by channel count ---")
        rows = client.list_customers(limit=args.limit)
        print(pretty(rows))
        print(f"\n{len(rows)} customer(s)")


if __name__ == "__main__":
    main()
