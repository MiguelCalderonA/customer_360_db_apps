"""Dual-mode auth + config helpers (local CLI profile vs deployed Databricks App)."""
from __future__ import annotations

import os
from functools import lru_cache

from databricks.sdk import WorkspaceClient

IS_DATABRICKS_APP = bool(os.environ.get("DATABRICKS_APP_NAME"))

CATALOG = os.environ.get("DATABRICKS_CATALOG", "miguel_usage_testing_catalog")
SCHEMA = os.environ.get("DATABRICKS_SCHEMA", "bnpl_customer_360")
CUSTOMER_360_TABLE = os.environ.get("CUSTOMER_360_TABLE", "customer_360")

# Local default — overridden in the Databricks App by the SQL warehouse resource binding.
LOCAL_DEFAULT_WAREHOUSE_ID = "27885d305b3ed2a9"


@lru_cache(maxsize=1)
def get_workspace_client() -> WorkspaceClient:
    if IS_DATABRICKS_APP:
        return WorkspaceClient()
    profile = os.environ.get("DATABRICKS_PROFILE", "fe-vm-miguel-usage-testing")
    return WorkspaceClient(profile=profile)


def get_warehouse_id() -> str:
    # Resource bindings inject DATABRICKS_WAREHOUSE_ID when a SQL warehouse
    # resource is attached to the app.
    return os.environ.get("DATABRICKS_WAREHOUSE_ID", LOCAL_DEFAULT_WAREHOUSE_ID)


def get_workspace_host() -> str:
    if IS_DATABRICKS_APP:
        host = os.environ.get("DATABRICKS_HOST", "")
        if host and not host.startswith("http"):
            host = f"https://{host}"
        return host
    return get_workspace_client().config.host


def get_oauth_token() -> str:
    """Return a bearer token usable against the SQL warehouse."""
    auth_headers = get_workspace_client().config.authenticate()
    return auth_headers["Authorization"].replace("Bearer ", "")


def fully_qualified_table() -> str:
    return f"{CATALOG}.{SCHEMA}.{CUSTOMER_360_TABLE}"
