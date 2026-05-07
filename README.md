# Customer 360 — Fintech BNPL on Databricks Apps

A Customer 360 view for a buy-now-pay-later fintech, served as a Databricks
App. Same data is reachable interactively through the bundled UI **and**
programmatically through a REST API.



## What's in here

```
customer_360_db_apps/
├── data_generation/             ← 4 channel-specific notebooks (100 rows each)
│   ├── customer_pool.py         ← shared 150-customer pool (%run-able)
│   ├── 01_mobile_app.py         ← Channel 1: PayLater Mobile App
│   ├── 02_partner_checkout.py   ← Channel 2: Partner Merchant Checkout
│   ├── 03_web_portal.py         ← Channel 3: Web Portal Direct Signups
│   └── 04_cobranded_card.py     ← Channel 4: Co-branded Credit Card
├── pipeline/
│   └── consolidate_customer_360.py  ← email-matched 360 view
├── server/                      ← FastAPI backend
│   ├── config.py                ← dual-mode auth (local CLI vs deployed App)
│   ├── database.py              ← SQL warehouse query helpers
│   └── routes.py                ← REST endpoints
├── frontend/                    ← React + TypeScript + Vite UI
│   ├── src/                     ← App, types, api client
│   └── dist/                    ← built bundle (committed for deploy)
├── app.py                       ← FastAPI entrypoint (serves API + SPA)
├── app.yaml                     ← Databricks App config
└── pyproject.toml               ← Python deps (uv-managed)
```

## The data model

Each of the four sales channels writes a Delta table under
`miguel_usage_testing_catalog.bnpl_customer_360`:

| Channel | Table | Domain shape |
|---|---|---|
| Mobile App | `mobile_app_purchases` | order, plan (pay-in-4, 6mo, 12mo), amount, status |
| Partner Checkout | `partner_checkout_loans` | partner, integration type, principal, APR, term |
| Web Portal | `web_portal_signups` | UTM, purpose, requested/funded, credit score, KYC |
| Co-branded Card | `cobranded_card_accounts` | partner, limit/balance/util, tier, behavior, delinquency |

The consolidation pipeline matches customers by **email** and produces a
single `customer_360` Delta table containing:

- Identity (`customer_id`, `email`, `first_name`, `last_name`)
- Per-channel `ARRAY<STRUCT>` event columns (full event history per channel)
- Roll-up metrics (`mobile_app_total_spend`, `partner_total_principal`,
  `web_total_funded`, `card_total_balance`, etc.)
- `channels_used` array and `channel_count` integer

The 4 channels each sample **100 rows** from a shared 150-customer pool with
different RNG seeds, so most customers appear in 2+ channels (137/150 in this
build) — making the 360 view actually interesting.

## REST API

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Liveness check |
| GET | `/api/stats` | Customer counts and channel totals |
| GET | `/api/customers?q=<text>&limit=<n>` | Search by email or full name (case-insensitive substring) |
| GET | `/api/customers/{email}` | Full 360 profile for one customer |
| GET | `/docs` | Interactive Swagger / OpenAPI explorer |

Programmatic access uses the same OAuth identity that authorises a user to
view the App:

```bash
APP_URL="https://customer-360-7474658851923715.aws.databricksapps.com"
TOKEN=$(databricks auth token --host https://fevm-miguel-usage-testing.cloud.databricks.com -p fe-vm-miguel-usage-testing -o json | jq -r .access_token)

# Stats
curl -sS -H "Authorization: Bearer $TOKEN" "$APP_URL/api/stats" | jq .

# Search
curl -sS -H "Authorization: Bearer $TOKEN" "$APP_URL/api/customers?q=sofia" | jq .

# Single profile
curl -sS -H "Authorization: Bearer $TOKEN" "$APP_URL/api/customers/sofia.rivera002@paylater-demo.com" | jq .
```

## How it was deployed

```bash
PROFILE=fe-vm-miguel-usage-testing
WAREHOUSE=27885d305b3ed2a9
USER_DIR=/Workspace/Users/miguel.calderon@databricks.com/customer_360_db_apps
APP_NAME=customer-360
SP_ID=d472113f-2aac-4d8b-8dac-656fdee7e480   # set after `apps create`

# 1. Schema for the demo
databricks api post /api/2.0/sql/statements -p $PROFILE --json '{
  "warehouse_id":"'"$WAREHOUSE"'",
  "statement":"CREATE SCHEMA IF NOT EXISTS miguel_usage_testing_catalog.bnpl_customer_360"
}'

# 2. Upload + run data generation + consolidation
databricks workspace import-dir data_generation $USER_DIR/data_generation -p $PROFILE --overwrite
databricks workspace import-dir pipeline        $USER_DIR/pipeline        -p $PROFILE --overwrite
databricks api post /api/2.2/jobs/runs/submit -p $PROFILE --json @run_pipeline_job.json

# 3. Build the frontend bundle (committed under frontend/dist/)
( cd frontend && npm install && npm run build )

# 4. Create the App, grant its SP read access to the data + warehouse
databricks apps create $APP_NAME --description "..." -p $PROFILE
databricks api post /api/2.0/sql/statements -p $PROFILE --json '{...GRANT USE_CATALOG / USE_SCHEMA / SELECT to '"$SP_ID"'...}'
databricks api patch /api/2.0/permissions/warehouses/$WAREHOUSE -p $PROFILE --json '{
  "access_control_list":[{"service_principal_name":"'"$SP_ID"'","permission_level":"CAN_USE"}]
}'

# 5. Sync source and deploy
databricks sync . $USER_DIR/source -p $PROFILE \
  --exclude '.git/**' --exclude 'frontend/node_modules/**' --exclude 'frontend/src/**' \
  --exclude 'data_generation/**' --exclude 'pipeline/**'
databricks apps deploy $APP_NAME --source-code-path $USER_DIR/source -p $PROFILE
```

## Running locally

The FastAPI backend authenticates via the `fe-vm-miguel-usage-testing`
Databricks CLI profile when not running in a deployed App.

```bash
# Backend
uv venv
uv pip install -e .
DATABRICKS_PROFILE=fe-vm-miguel-usage-testing uv run uvicorn app:app --reload --port 8000

# Frontend (separate terminal — proxies /api → :8000)
cd frontend && npm run dev
```

Visit `http://localhost:5173` for the dev UI, or `http://localhost:8000/docs`
for the API.
