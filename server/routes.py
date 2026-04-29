"""REST API routes for the Customer 360 app."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from .config import fully_qualified_table
from .database import fetchall, fetchone

router = APIRouter()

PROFILE_COLUMNS = """
    customer_id,
    email,
    first_name,
    last_name,
    channels_used,
    channel_count,
    mobile_app_order_count,
    mobile_app_total_spend,
    partner_loan_count,
    partner_total_principal,
    web_application_count,
    web_total_funded,
    web_max_credit_score,
    card_account_count,
    card_total_credit_limit,
    card_total_balance,
    card_max_delinquency_days,
    mobile_app_events,
    partner_loan_events,
    web_application_events,
    card_account_events,
    profile_last_updated
"""


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/stats")
def stats() -> dict:
    table = fully_qualified_table()
    row = fetchone(f"""
        SELECT
            count(*)                                          AS total_customers,
            sum(CASE WHEN channel_count > 1 THEN 1 ELSE 0 END) AS multi_channel_customers,
            sum(mobile_app_order_count)                       AS total_mobile_orders,
            sum(partner_loan_count)                           AS total_partner_loans,
            sum(web_application_count)                        AS total_web_applications,
            sum(card_account_count)                           AS total_card_accounts,
            sum(mobile_app_total_spend)                       AS total_mobile_spend,
            sum(partner_total_principal)                      AS total_partner_principal,
            sum(web_total_funded)                             AS total_web_funded,
            sum(card_total_balance)                           AS total_card_balance
        FROM {table}
    """)
    return row or {}


@router.get("/customers")
def list_customers(
    q: str | None = Query(None, description="Email substring to filter by"),
    limit: int = Query(50, ge=1, le=500),
) -> list[dict]:
    table = fully_qualified_table()
    if q:
        rows = fetchall(
            f"""
            SELECT customer_id, email, first_name, last_name,
                   channel_count, channels_used,
                   mobile_app_order_count, partner_loan_count,
                   web_application_count, card_account_count
            FROM {table}
            WHERE lower(email) LIKE lower(%(pattern)s)
               OR lower(first_name || ' ' || last_name) LIKE lower(%(pattern)s)
            ORDER BY email
            LIMIT {limit}
            """,
            {"pattern": f"%{q}%"},
        )
    else:
        rows = fetchall(
            f"""
            SELECT customer_id, email, first_name, last_name,
                   channel_count, channels_used,
                   mobile_app_order_count, partner_loan_count,
                   web_application_count, card_account_count
            FROM {table}
            ORDER BY channel_count DESC, email
            LIMIT {limit}
            """
        )
    return rows


@router.get("/customers/{email}")
def get_customer(email: str) -> dict:
    table = fully_qualified_table()
    row = fetchone(
        f"SELECT {PROFILE_COLUMNS} FROM {table} WHERE lower(email) = lower(%(email)s)",
        {"email": email},
    )
    if not row:
        raise HTTPException(status_code=404, detail=f"No customer with email {email}")
    return row
