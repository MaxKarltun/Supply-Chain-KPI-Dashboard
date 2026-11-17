<h1 align="center">📦 Supply Chain KPI Dashboard</h1>

<p align="center">
  An interactive dashboard for exploring revenue, inventory, fulfillment, and shipping performance.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white" alt="Python 3.11 or newer">
  <img src="https://img.shields.io/badge/Streamlit-1.67.0-FF4B4B?logo=streamlit&logoColor=white" alt="Streamlit 1.67.0">
  <img src="https://img.shields.io/badge/Plotly-7.1.0-3F4F75?logo=plotly&logoColor=white" alt="Plotly 7.1.0">
  <img src="https://img.shields.io/badge/Pandas-3.1.1-150458?logo=pandas&logoColor=white" alt="Pandas 3.1.1">
  <img src="https://img.shields.io/badge/HTML5-E34F26?logo=html5&logoColor=white" alt="HTML5">
  <img src="https://img.shields.io/badge/CSS3-1572B6?logo=css3&logoColor=white" alt="CSS3">
</p>

<p align="center">
  <a href="https://supply-chain-kpi-dashboard-lfyffsckm5zgequxh7konf.streamlit.app/">🚀 Live demo</a> ·
  <a href="#features">Features</a> ·
  <a href="#getting-started">Get started</a> ·
  <a href="#data--kpi-definitions">Data &amp; KPIs</a> ·
  <a href="#tests">Tests</a>
</p>

## Dashboard preview

![Supply Chain KPI Dashboard showing revenue, inventory, fill rate, shipping, and top products](assets/supply-chain-kpi-dashboard.png)

## Overview

Explore supply chain performance with interactive charts, configurable filters,
CSV uploads, and downloadable reports. The dashboard starts with reproducible
synthetic data, so it runs locally without an external API or database.

## Features

- **Revenue & product performance** — follow sales trends and rank products by revenue or fulfilled units.
- **Inventory monitoring** — review current stock and identify products below a configurable threshold.
- **Fulfillment & shipping** — track unit-weighted fill rate and average delivery transit time.
- **Interactive exploration** — filter by order date, category, and region.
- **Bring your own data** — upload validated orders and inventory CSVs, or download sample templates.
- **Export results** — download filtered orders and inventory snapshots.
- **Custom styling** — responsive Streamlit layout with HTML/CSS styling.

## Technology

| Technology | Use |
| --- | --- |
| Python | Application logic and KPI calculations |
| Streamlit | Interactive dashboard and CSV workflows |
| Plotly | Interactive charts |
| Pandas | Data validation and transformation |
| HTML & CSS | Custom dashboard styling rendered through Streamlit |
| Markdown | Project documentation |

## Data & KPI definitions

The dashboard generates 180 days of repeatable synthetic orders and inventory
snapshots across eight products, three categories, and three regions. The data
is illustrative: inventory is generated independently and is not reconciled
against order movements. No real customer or business data is bundled.

| KPI | Definition |
| --- | --- |
| Revenue | Fulfilled units by the end date × unit price; excludes taxes and shipping fees |
| Inventory | Latest available stock quantity per product and region at the reporting cutoff |
| Fill rate | Total fulfilled units ÷ total ordered units |
| Average shipping time | Average calendar days from shipment to delivery for orders delivered by the end date |
| Top products | Products ranked by revenue or fulfilled units |

### Reporting rules

- The selected date range filters orders by **order date**, including both endpoints.
- Fulfillment, revenue, and delivery are evaluated as of the selected end date. Future shipments and deliveries are excluded.
- Inventory uses the latest snapshot on or before the end date for each product and region. It is not summed across dates; the start date does not affect it.
- Missing inventory and unavailable rates display as `N/A`, not zero.
- Monetary values are in **USD**. Revenue is an operational sales measure; taxes, shipping fees, returns, discounts, and currency conversion are not modeled.

### Use your own CSVs

Choose **Upload CSVs** in the sidebar and provide both datasets. Download the
sample CSVs from the app for complete templates.

**Orders**

```csv
order_id,order_date,product,category,region,ordered_units,fulfilled_units,unit_price,ship_date,delivery_date
```

**Inventory**

```csv
snapshot_date,product,category,region,stock_quantity
```

Uploads must be UTF-8 CSVs with headers (up to 100,000 rows per file). Dates use
`YYYY-MM-DD`; shipment and delivery dates may be blank while pending. Each order
row represents one product and requires a unique `order_id` (use a unique line
identifier for multi-line orders). Quantities must be nonnegative whole units,
with `ordered_units` greater than zero and `fulfilled_units` no greater than
ordered. Positive fulfillment requires a shipment date; unfulfilled orders must
not have one. Dates must follow
`order_date <= ship_date <= delivery_date` when present. Unit prices must be
finite and nonnegative. Inventory quantities must be nonnegative whole units;
inventory keys (`snapshot_date`, `product`, `region`) must be unique. Each
product must have the same category in both files.

Uploads are validated with explicit errors and processed in memory; they are
not written to a database. Use non-sensitive demo data for public deployments.
Order exports include calculated revenue and shipping days. Inventory exports
include low-stock status based on the sidebar threshold.

## Getting started

Python 3.11 or newer is recommended. From the repository directory:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

On Windows PowerShell, activate the environment with
`.\.venv\Scripts\Activate.ps1` instead. Open the local URL printed by Streamlit
(usually <http://localhost:8501>). Press `Ctrl+C` in the terminal to stop the app.

## Tests

```bash
python -m unittest discover -s tests -v
```

The suite covers historical cutoffs, weighted fill rates, inventory snapshot
selection, missing deliveries, CSV validation, repeatable sample data, and
dashboard rendering and empty states.

## Project structure

```text
app.py                  Streamlit interface, charts, and CSV workflows
dashboard_data.py       Sample data, validation, and KPI calculations
requirements.txt        Pinned runtime dependencies
.streamlit/config.toml  Streamlit theme configuration
tests/                  Calculation and dashboard tests
assets/                 README dashboard preview
```
