# Databricks notebook source
# MAGIC %md
# MAGIC # Channel 1 — PayLater Mobile App
# MAGIC
# MAGIC Generates 100 rows of in-app BNPL purchases and writes
# MAGIC `mobile_app_purchases` Delta table.

# COMMAND ----------

# MAGIC %run ./customer_pool

# COMMAND ----------

import random
from datetime import datetime, timedelta
from decimal import Decimal

from pyspark.sql import Row
from pyspark.sql.types import (
    DecimalType, IntegerType, StringType, StructField, StructType, TimestampType,
)

TABLE = f"{CATALOG}.{SCHEMA}.mobile_app_purchases"
ROW_COUNT = 100
SEED = 101

PLATFORMS = ["iOS", "Android"]
APP_VERSIONS = ["6.4.1", "6.5.0", "6.6.2", "7.0.0"]
MERCHANT_CATEGORIES = ["Electronics", "Apparel", "Home Goods", "Beauty", "Sports", "Travel"]
BNPL_PLANS = ["pay_in_4", "6mo_installments", "12mo_installments"]
STATUSES = ["completed", "completed", "completed", "active", "late_payment"]
INSTALLMENTS_BY_PLAN = {"pay_in_4": 4, "6mo_installments": 6, "12mo_installments": 12}

rng = random.Random(SEED)
sampled = rng.sample(CUSTOMER_POOL, ROW_COUNT)
base_date = datetime(2026, 1, 1)

rows = []
for idx, cust in enumerate(sampled):
    plan = rng.choice(BNPL_PLANS)
    installments = INSTALLMENTS_BY_PLAN[plan]
    order_amount = Decimal(str(round(rng.uniform(35.0, 1800.0), 2)))
    installment_amount = (order_amount / installments).quantize(Decimal("0.01"))
    rows.append(Row(
        order_id=f"MOB-{cust['customer_id']}-{idx + 1:03d}",
        customer_id=cust["customer_id"],
        email=cust["email"],
        first_name=cust["first_name"],
        last_name=cust["last_name"],
        device_platform=rng.choice(PLATFORMS),
        app_version=rng.choice(APP_VERSIONS),
        merchant_category=rng.choice(MERCHANT_CATEGORIES),
        bnpl_plan=plan,
        installments=installments,
        order_amount=order_amount,
        installment_amount=installment_amount,
        status=rng.choice(STATUSES),
        order_ts=base_date + timedelta(days=rng.randint(0, 110), minutes=rng.randint(0, 1440)),
    ))

schema = StructType([
    StructField("order_id", StringType(), False),
    StructField("customer_id", StringType(), False),
    StructField("email", StringType(), False),
    StructField("first_name", StringType(), False),
    StructField("last_name", StringType(), False),
    StructField("device_platform", StringType(), False),
    StructField("app_version", StringType(), False),
    StructField("merchant_category", StringType(), False),
    StructField("bnpl_plan", StringType(), False),
    StructField("installments", IntegerType(), False),
    StructField("order_amount", DecimalType(10, 2), False),
    StructField("installment_amount", DecimalType(10, 2), False),
    StructField("status", StringType(), False),
    StructField("order_ts", TimestampType(), False),
])

df = spark.createDataFrame(rows, schema=schema)

# COMMAND ----------

(df.write
   .mode("overwrite")
   .option("overwriteSchema", "true")
   .saveAsTable(TABLE))

spark.sql(
    f"COMMENT ON TABLE {TABLE} IS 'Mobile app BNPL purchases — sales channel 1'"
)
print(f"Wrote {df.count()} rows to {TABLE}")
