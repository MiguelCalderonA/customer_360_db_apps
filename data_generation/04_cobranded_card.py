# Databricks notebook source
# MAGIC %md
# MAGIC # Channel 4 — Co-branded Credit Card
# MAGIC
# MAGIC PayLater + retail partner co-branded card accounts. 100 accounts →
# MAGIC `cobranded_card_accounts` Delta table.

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

TABLE = f"{CATALOG}.{SCHEMA}.cobranded_card_accounts"
ROW_COUNT = 100
SEED = 404

CARD_PARTNERS = [
    "PayLater MercadoBuy Visa",
    "PayLater ModaPlus Mastercard",
    "PayLater ElektroMart Visa",
    "PayLater ViajaYa World Elite",
]
REWARDS_TIERS = ["standard", "silver", "gold", "platinum"]
ACCOUNT_STATUSES = ["active", "active", "active", "active", "frozen", "closed"]
PAYMENT_BEHAVIORS = ["pays_full", "pays_minimum", "revolves", "behind"]

rng = random.Random(SEED)
sampled = rng.sample(CUSTOMER_POOL, ROW_COUNT)
base_date = datetime(2024, 6, 1)

rows = []
for idx, cust in enumerate(sampled):
    credit_limit = Decimal(rng.choice([1500, 3000, 5000, 7500, 10000, 15000, 25000]))
    utilization = Decimal(str(round(rng.uniform(0.0, 1.05), 4)))
    current_balance = (credit_limit * utilization).quantize(Decimal("0.01"))
    behavior = rng.choice(PAYMENT_BEHAVIORS)
    delinquency_days = rng.choice([30, 60, 90]) if behavior == "behind" else 0
    rows.append(Row(
        account_id=f"CARD-{cust['customer_id']}-{idx + 1:03d}",
        customer_id=cust["customer_id"],
        email=cust["email"],
        first_name=cust["first_name"],
        last_name=cust["last_name"],
        card_partner=rng.choice(CARD_PARTNERS),
        credit_limit=credit_limit,
        current_balance=current_balance,
        utilization_pct=(utilization * Decimal("100")).quantize(Decimal("0.01")),
        rewards_tier=rng.choice(REWARDS_TIERS),
        payment_behavior=behavior,
        delinquency_days=delinquency_days,
        account_status=rng.choice(ACCOUNT_STATUSES),
        account_opened=(base_date + timedelta(days=rng.randint(0, 600))).date(),
    ))

schema = StructType([
    StructField("account_id", StringType(), False),
    StructField("customer_id", StringType(), False),
    StructField("email", StringType(), False),
    StructField("first_name", StringType(), False),
    StructField("last_name", StringType(), False),
    StructField("card_partner", StringType(), False),
    StructField("credit_limit", DecimalType(12, 2), False),
    StructField("current_balance", DecimalType(12, 2), False),
    StructField("utilization_pct", DecimalType(5, 2), False),
    StructField("rewards_tier", StringType(), False),
    StructField("payment_behavior", StringType(), False),
    StructField("delinquency_days", IntegerType(), False),
    StructField("account_status", StringType(), False),
    StructField("account_opened", DateType(), False),
])

df = spark.createDataFrame(rows, schema=schema)

# COMMAND ----------

(df.write
   .mode("overwrite")
   .option("overwriteSchema", "true")
   .saveAsTable(TABLE))

spark.sql(
    f"COMMENT ON TABLE {TABLE} IS 'Co-branded credit card accounts — sales channel 4'"
)
print(f"Wrote {df.count()} rows to {TABLE}")
