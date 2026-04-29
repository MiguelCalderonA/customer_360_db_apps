# Databricks notebook source
# MAGIC %md
# MAGIC # Customer 360 consolidation pipeline
# MAGIC
# MAGIC Reads the 4 channel tables, matches customers by email, and writes the
# MAGIC unified `customer_360` Delta table consumed by the Databricks App.

# COMMAND ----------

CATALOG = "miguel_usage_testing_catalog"
SCHEMA = "bnpl_customer_360"
TARGET = f"{CATALOG}.{SCHEMA}.customer_360"

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE TABLE {TARGET}
COMMENT 'Customer 360 view consolidated from all 4 BNPL sales channels'
AS
WITH all_customers AS (
    SELECT customer_id, email, first_name, last_name FROM {CATALOG}.{SCHEMA}.mobile_app_purchases
    UNION
    SELECT customer_id, email, first_name, last_name FROM {CATALOG}.{SCHEMA}.partner_checkout_loans
    UNION
    SELECT customer_id, email, first_name, last_name FROM {CATALOG}.{SCHEMA}.web_portal_signups
    UNION
    SELECT customer_id, email, first_name, last_name FROM {CATALOG}.{SCHEMA}.cobranded_card_accounts
),
identity AS (
    SELECT
        email,
        any_value(customer_id) AS customer_id,
        any_value(first_name)  AS first_name,
        any_value(last_name)   AS last_name
    FROM all_customers
    GROUP BY email
),
mobile AS (
    SELECT
        email,
        collect_list(named_struct(
            'order_id', order_id,
            'merchant_category', merchant_category,
            'bnpl_plan', bnpl_plan,
            'order_amount', order_amount,
            'status', status,
            'order_ts', cast(order_ts AS string)
        )) AS mobile_app_events,
        count(*) AS mobile_app_order_count,
        sum(order_amount) AS mobile_app_total_spend
    FROM {CATALOG}.{SCHEMA}.mobile_app_purchases
    GROUP BY email
),
partner AS (
    SELECT
        email,
        collect_list(named_struct(
            'loan_id', loan_id,
            'partner_name', partner_name,
            'principal_amount', principal_amount,
            'apr_pct', apr_pct,
            'term_months', term_months,
            'approval_status', approval_status,
            'originated_date', cast(originated_date AS string)
        )) AS partner_loan_events,
        count(*) AS partner_loan_count,
        sum(principal_amount) AS partner_total_principal
    FROM {CATALOG}.{SCHEMA}.partner_checkout_loans
    GROUP BY email
),
web AS (
    SELECT
        email,
        collect_list(named_struct(
            'application_id', application_id,
            'utm_source', utm_source,
            'loan_purpose', loan_purpose,
            'requested_amount', requested_amount,
            'funded_amount', funded_amount,
            'credit_score', credit_score,
            'kyc_status', kyc_status,
            'applied_date', cast(applied_date AS string)
        )) AS web_application_events,
        count(*) AS web_application_count,
        sum(funded_amount) AS web_total_funded,
        max(credit_score) AS web_max_credit_score
    FROM {CATALOG}.{SCHEMA}.web_portal_signups
    GROUP BY email
),
card AS (
    SELECT
        email,
        collect_list(named_struct(
            'account_id', account_id,
            'card_partner', card_partner,
            'credit_limit', credit_limit,
            'current_balance', current_balance,
            'utilization_pct', utilization_pct,
            'rewards_tier', rewards_tier,
            'payment_behavior', payment_behavior,
            'delinquency_days', delinquency_days,
            'account_status', account_status,
            'account_opened', cast(account_opened AS string)
        )) AS card_account_events,
        count(*) AS card_account_count,
        sum(credit_limit) AS card_total_credit_limit,
        sum(current_balance) AS card_total_balance,
        max(delinquency_days) AS card_max_delinquency_days
    FROM {CATALOG}.{SCHEMA}.cobranded_card_accounts
    GROUP BY email
)
SELECT
    i.customer_id,
    i.email,
    i.first_name,
    i.last_name,

    coalesce(m.mobile_app_events, array()) AS mobile_app_events,
    coalesce(p.partner_loan_events, array()) AS partner_loan_events,
    coalesce(w.web_application_events, array()) AS web_application_events,
    coalesce(c.card_account_events, array()) AS card_account_events,

    coalesce(m.mobile_app_order_count, 0)    AS mobile_app_order_count,
    coalesce(m.mobile_app_total_spend, 0)    AS mobile_app_total_spend,
    coalesce(p.partner_loan_count, 0)        AS partner_loan_count,
    coalesce(p.partner_total_principal, 0)   AS partner_total_principal,
    coalesce(w.web_application_count, 0)     AS web_application_count,
    coalesce(w.web_total_funded, 0)          AS web_total_funded,
    coalesce(w.web_max_credit_score, 0)      AS web_max_credit_score,
    coalesce(c.card_account_count, 0)        AS card_account_count,
    coalesce(c.card_total_credit_limit, 0)   AS card_total_credit_limit,
    coalesce(c.card_total_balance, 0)        AS card_total_balance,
    coalesce(c.card_max_delinquency_days, 0) AS card_max_delinquency_days,

    array_compact(array(
        CASE WHEN m.email IS NOT NULL THEN 'mobile_app' END,
        CASE WHEN p.email IS NOT NULL THEN 'partner_checkout' END,
        CASE WHEN w.email IS NOT NULL THEN 'web_portal' END,
        CASE WHEN c.email IS NOT NULL THEN 'cobranded_card' END
    )) AS channels_used,
    (
        CASE WHEN m.email IS NOT NULL THEN 1 ELSE 0 END +
        CASE WHEN p.email IS NOT NULL THEN 1 ELSE 0 END +
        CASE WHEN w.email IS NOT NULL THEN 1 ELSE 0 END +
        CASE WHEN c.email IS NOT NULL THEN 1 ELSE 0 END
    ) AS channel_count,
    current_timestamp() AS profile_last_updated
FROM identity i
LEFT JOIN mobile m  ON i.email = m.email
LEFT JOIN partner p ON i.email = p.email
LEFT JOIN web w     ON i.email = w.email
LEFT JOIN card c    ON i.email = c.email
""")

# COMMAND ----------

total = spark.table(TARGET).count()
multi = spark.sql(f"SELECT count(*) AS n FROM {TARGET} WHERE channel_count > 1").collect()[0]["n"]
print(f"customer_360 rows: {total} | multi-channel customers: {multi}")
