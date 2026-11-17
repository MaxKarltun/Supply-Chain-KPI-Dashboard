# Supply Chain KPI Dashboard

An interactive business analytics dashboard built with Streamlit,
Plotly, and Pandas to monitor supply chain performance.

## Project Status

Working MVP with synthetic sample data, interactive analytics, validated CSV
uploads, and downloadable reports. No external API or database is required.

## Key Features

- **Revenue:** Track sales totals and revenue trends.
- **Inventory:** Monitor stock levels and identify low-stock products.
- **Fill Rate:** Measure the percentage of ordered units fulfilled.
- **Shipping Times:** Analyze average transit time from shipment to delivery.
- **Top Products:** Rank products by revenue and units sold.
- **Interactive Filters:** Explore results by date, category, and region.
- **CSV Upload:** Analyze your own data or explore sample datasets.
- **Downloads:** Export filtered orders and point-in-time inventory snapshots.
- **Accessible Layout:** Large text, white cards, and a deep blue gradient.

## Tech Stack

- Python
- Streamlit
- Plotly
- Pandas

## KPI Definitions

| KPI | Definition |
| --- | --- |
| Revenue | Sum of units shipped by the end date × unit selling price, excluding taxes and shipping fees |
| Inventory | Latest available stock quantity per product at the reporting cutoff |
| Fill Rate | Fulfilled units ÷ ordered units × 100 |
| Average Shipping Time | Average calendar days between shipment and delivery for orders delivered by the end date |
| Top Products | Products ranked by revenue or fulfilled units |

## Data

The dashboard opens with 180 days of reproducible synthetic orders and inventory
snapshots across eight products, three categories, and three regions. The data
ends on the current date and is generated with a fixed random seed.

Sample data is illustrative: inventory balances are independently generated,
not reconciled to order movements. No real business or customer data is bundled.

### Reporting Rules

- The date range selects orders by **order date**, including both endpoints.
- Fulfillment, revenue, and deliveries are evaluated at the selected end date:
  future shipments do not count as fulfilled, and future deliveries do not
  contribute shipping times.
- Fill rate is unit-weighted: total fulfilled units / total ordered units.
- Inventory uses the latest snapshot on or before the end date for each
  product/region. It is not summed across dates, and the start date does not
  affect it. Older snapshots are flagged in the dashboard.
- Missing inventory and unavailable rates display `N/A`, not misleading zeros.
- Top product is ranked by revenue; the chart can also rank fulfilled units.
- All monetary values assume **USD**. No currency conversion is performed.
- Revenue is an operational sales measure, not an accounting revenue-recognition
  report. Taxes, shipping fees, returns, and discounts are not modeled.

### Upload Your Own CSVs

Select **Upload CSVs** in the sidebar and provide **both** datasets. Download
the sample CSVs from the sidebar for complete templates.

**Orders columns**

```text
order_id,order_date,product,category,region,ordered_units,fulfilled_units,unit_price,ship_date,delivery_date
```

**Inventory columns**

```text
snapshot_date,product,category,region,stock_quantity
```

Rules:

- UTF-8 CSVs with headers; up to 100,000 rows per file.
- Dates use `YYYY-MM-DD`. Shipment and delivery dates may be blank while pending.
- One product per order row, with a unique `order_id`. Multi-line order data
  should use a unique line identifier in this column.
- Quantities are finite, nonnegative whole units; `ordered_units` must exceed zero.
- Fulfilled units cannot exceed ordered units. Positive fulfilled units require
  a shipment date; an unfulfilled order must not have a shipment date.
- Dates follow `order_date <= ship_date <= delivery_date` when present.
- Unit prices must be finite and nonnegative.
- Inventory keys (`snapshot_date`, `product`, `region`) must be unique.
- Products must use one consistent category across both datasets.

Uploads are validated with explicit error messages. Uploaded data is processed
in memory and cached for the running application, not written to a database.
Use non-sensitive demonstration data for public deployments. Order exports
contain calculated revenue and shipping days; inventory exports include a
low-stock status based on the sidebar threshold.

## Project Goals

Demonstrate data cleaning, KPI modeling, interactive visualization,
and business-focused dashboard design.

## Getting Started

Python 3.11 or newer is recommended.

From the repository folder in Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the local URL printed by Streamlit, normally http://localhost:8501.
Leave the terminal running; press `Ctrl+C` to stop the app.

If PowerShell blocks activation, use the environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Run Tests

```powershell
python -m unittest discover -s tests -v
```

Tests cover historical cutoffs, weighted fill rates, inventory snapshot
selection, missing deliveries, invalid CSV data, repeatable sample data, and
dashboard rendering/empty states using Streamlit's application test runner.

## Project Structure

```text
app.py                  Streamlit interface, charts, and CSV workflows
dashboard_data.py       Sample data, validation, and KPI calculations
requirements.txt        Runtime dependencies
.streamlit/config.toml  Light theme and blue accent configuration
tests/                  Calculation and dashboard tests
```