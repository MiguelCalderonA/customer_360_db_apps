# Databricks notebook source
# MAGIC %md
# MAGIC # Channel 3 — Web Portal Direct Signups
# MAGIC
# MAGIC paylater.com self-service installment loans. 100 applications →
# MAGIC `web_portal_signups` Delta table.

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

TABLE = f"{CATALOG}.{SCHEMA}.web_portal_signups"
ROW_COUNT = 100
SEED = 303

UTM_SOURCES = ["google_ads", "meta_ads", "tiktok", "organic", "email", "referral"]
LOAN_PURPOSES = [
    "debt_consolidation", "home_improvement", "auto_repair", "medical",
    "education", "wedding", "travel", "small_business",
]
KYC_STATUSES = ["passed", "passed", "passed", "passed", "manual_review", "failed"]
EMPLOYMENT = ["full_time", "self_employed", "part_time", "contractor", "unemployed"]

rng = random.Random(SEED)
sampled = rng.sample(CUSTOMER_POOL, ROW_COUNT)
base_date = datetime(2025, 9, 1)

rows = []
for idx, cust in enumerate(sampled):
    requested = Decimal(str(round(rng.uniform(500.0, 25000.0), 2)))
    credit_score = rng.randint(540, 820)
    kyc = rng.choice(KYC_STATUSES)
    funded = (requested * Decimal(str(round(rng.uniform(0.6, 1.0), 4)))).quantize(Decimal("0.01")) if kyc == "passed" else Decimal("0")
    rows.append(Row(
        application_id=f"WEB-{cust['customer_id']}-{idx + 1:03d}",
        customer_id=cust["customer_id"],
        email=cust["email"],
        first_name=cust["first_name"],
        last_name=cust["last_name"],
        utm_source=rng.choice(UTM_SOURCES),
        loan_purpose=rng.choice(LOAN_PURPOSES),
        requested_amount=requested,
        funded_amount=funded,
        credit_score=credit_score,
        employment_status=rng.choice(EMPLOYMENT),
        annual_income=Decimal(str(round(rng.uniform(18000.0, 180000.0), 2))),
        kyc_status=kyc,
        applied_date=(base_date + timedelta(days=rng.randint(0, 230))).date(),
    ))

schema = StructType([
    StructField("application_id", StringType(), False),
    StructField("customer_id", StringType(), False),
    StructField("email", StringType(), False),
    StructField("first_name", StringType(), False),
    StructField("last_name", StringType(), False),
    StructField("utm_source", StringType(), False),
    StructField("loan_purpose", StringType(), False),
    StructField("requested_amount", DecimalType(12, 2), False),
    StructField("funded_amount", DecimalType(12, 2), False),
    StructField("credit_score", IntegerType(), False),
    StructField("employment_status", StringType(), False),
    StructField("annual_income", DecimalType(12, 2), False),
    StructField("kyc_status", StringType(), False),
    StructField("applied_date", DateType(), False),
])

df = spark.createDataFrame(rows, schema=schema)

# COMMAND ----------

(df.write
   .mode("overwrite")
   .option("overwriteSchema", "true")
   .saveAsTable(TABLE))

spark.sql(
    f"COMMENT ON TABLE {TABLE} IS 'Web portal direct loan signups — sales channel 3'"
)
print(f"Wrote {df.count()} rows to {TABLE}")
