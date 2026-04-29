# Databricks notebook source
# MAGIC %md
# MAGIC # Channel 2 — Partner Merchant Checkout
# MAGIC
# MAGIC BNPL widget embedded at partner stores. 100 originated loans →
# MAGIC `partner_checkout_loans` Delta table.

# COMMAND ----------

# MAGIC %run ./customer_pool

# COMMAND ----------

import random
from datetime import date, datetime, timedelta
from decimal import Decimal

from pyspark.sql import Row
from pyspark.sql.types import (
    DateType, DecimalType, IntegerType, StringType, StructField, StructType,
)

TABLE = f"{CATALOG}.{SCHEMA}.partner_checkout_loans"
ROW_COUNT = 100
SEED = 202

PARTNERS = [
    ("MercadoBuy", "marketplace"),
    ("ElektroMart", "electronics"),
    ("ModaPlus", "fashion"),
    ("HogarTotal", "home"),
    ("ViajaYa", "travel"),
    ("DeporteMax", "sports"),
    ("FarmaPlus", "pharmacy"),
]
INTEGRATIONS = ["widget", "redirect", "headless_api"]
TERMS_MONTHS = [3, 6, 9, 12, 18, 24]
APPROVAL_STATUSES = ["approved", "approved", "approved", "approved", "manual_review", "declined"]

rng = random.Random(SEED)
sampled = rng.sample(CUSTOMER_POOL, ROW_COUNT)
base_date = datetime(2025, 11, 1)

rows = []
for idx, cust in enumerate(sampled):
    partner_name, partner_segment = rng.choice(PARTNERS)
    principal = Decimal(str(round(rng.uniform(150.0, 6500.0), 2)))
    apr = Decimal(str(round(rng.uniform(0.0, 28.5), 2)))
    term = rng.choice(TERMS_MONTHS)
    monthly = (principal * (1 + apr / Decimal("100")) / Decimal(term)).quantize(Decimal("0.01"))
    rows.append(Row(
        loan_id=f"PRT-{cust['customer_id']}-{idx + 1:03d}",
        customer_id=cust["customer_id"],
        email=cust["email"],
        first_name=cust["first_name"],
        last_name=cust["last_name"],
        partner_name=partner_name,
        partner_segment=partner_segment,
        integration_type=rng.choice(INTEGRATIONS),
        principal_amount=principal,
        apr_pct=apr,
        term_months=term,
        monthly_payment=monthly,
        approval_status=rng.choice(APPROVAL_STATUSES),
        originated_date=(base_date + timedelta(days=rng.randint(0, 170))).date(),
    ))

schema = StructType([
    StructField("loan_id", StringType(), False),
    StructField("customer_id", StringType(), False),
    StructField("email", StringType(), False),
    StructField("first_name", StringType(), False),
    StructField("last_name", StringType(), False),
    StructField("partner_name", StringType(), False),
    StructField("partner_segment", StringType(), False),
    StructField("integration_type", StringType(), False),
    StructField("principal_amount", DecimalType(10, 2), False),
    StructField("apr_pct", DecimalType(5, 2), False),
    StructField("term_months", IntegerType(), False),
    StructField("monthly_payment", DecimalType(10, 2), False),
    StructField("approval_status", StringType(), False),
    StructField("originated_date", DateType(), False),
])

df = spark.createDataFrame(rows, schema=schema)

# COMMAND ----------

(df.write
   .mode("overwrite")
   .option("overwriteSchema", "true")
   .saveAsTable(TABLE))

spark.sql(
    f"COMMENT ON TABLE {TABLE} IS 'Partner merchant checkout BNPL loans — sales channel 2'"
)
print(f"Wrote {df.count()} rows to {TABLE}")
