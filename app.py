from datetime import date, timedelta
from io import BytesIO

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard_data import (
    MAX_ROWS,
    calculate_metrics,
    filter_orders,
    generate_sample_data,
    inventory_as_of,
    validate_data,
)

st.set_page_config(
    page_title="Supply Chain KPI Dashboard",
    page_icon="📦",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp {
        color: #111827;
        background: linear-gradient(120deg, #2c73c2 0%, #286ebb 45%, #2468b0 100%);
    }
    .stApp [data-testid="stHeader"] {
        color: #111827;
        background: #ffffffee;
        border-bottom: 1px solid #dbeafe;
    }
    .stApp [data-testid="stSidebar"] {
        color: #111827;
        background: #ffffff;
        border-right: 1px solid #bfdbfe;
    }
    .stApp h1 {
        color: #111827;
        font-size: clamp(2.5rem, 4vw, 4rem);
        line-height: 1.2;
        overflow-wrap: anywhere;
    }
    .stApp h2 {
        color: #111827;
        font-size: 2rem;
    }
    .stApp p, .stApp label {
        color: #111827;
        font-size: 1.375rem;
        line-height: 1.6;
    }
    .stApp [data-testid="stCaptionContainer"] {
        color: #111827;
    }
    .stApp main h1,
    .stApp main [data-testid="stCaptionContainer"] p {
        color: #ffffff;
    }
    .stApp main h2 {
        color: #ffffff;
    }
    .stApp [data-testid="stMetric"] {
        background: #ffffff;
        color: #111827;
        padding: 22px;
        border: 1px solid #bfdbfe;
        border-radius: 18px;
        box-shadow: 0 8px 24px #17255426;
        height: 100%;
    }
    .stApp [data-testid="stMetricLabel"] p {
        font-size: 1.125rem;
    }
    .stApp [data-testid="stMetricValue"],
    .stApp [data-testid="stMetricValue"] p {
        color: #111827;
        font-size: 1.75rem;
        line-height: 1.3;
        white-space: normal;
        overflow-wrap: anywhere;
    }
    .stApp [data-testid="stTabs"] {
        background: #ffffff;
        color: #111827;
        border: 1px solid #bfdbfe;
        border-radius: 20px;
        padding: 24px;
        margin-top: 24px;
        box-shadow: 0 8px 24px #17255426;
    }
    .stApp [data-testid="stTabs"] h2,
    .stApp [data-testid="stTabs"] [data-testid="stCaptionContainer"] p {
        color: #111827;
    }
    .stApp button {
        border-radius: 10px;
    }
    .stApp [data-baseweb="tab-list"] {
        gap: 20px;
    }
    .stApp main [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap;
    }
    .stApp main [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        flex: 1 1 350px;
        min-width: min(100%, 350px);
    }
    .stApp main [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"])
        > [data-testid="stColumn"] {
        flex-basis: 190px;
        min-width: min(100%, 190px);
    }
    @media (max-width: 1200px) {
        .stApp [data-testid="stMainBlockContainer"] {
            padding-left: 1.5rem;
            padding-right: 1.5rem;
        }
    }
    .stApp [data-testid="stAlert"] {
        color: #111827;
        background: #ffffff;
        border: 1px solid #bfdbfe;
        border-left: 5px solid #2563eb;
        border-radius: 16px;
        box-shadow: 0 8px 24px #1e40af0d;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📦 Supply Chain KPI Dashboard")
st.caption("OPERATIONS INTELLIGENCE  /  Revenue · Inventory · Fulfillment · Shipping")


@st.cache_data
def sample_data(as_of: date) -> tuple[pd.DataFrame, pd.DataFrame]:
    return generate_sample_data(as_of)


@st.cache_data
def read_upload(content: bytes) -> pd.DataFrame:
    return pd.read_csv(BytesIO(content), nrows=MAX_ROWS + 1, dtype="string")


def show_chart(figure: go.Figure) -> None:
    figure.update_layout(
        template="plotly_white",
        font={"family": "Arial, sans-serif", "size": 18, "color": "#111827"},
        title_font_size=23,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        margin={"l": 16, "r": 16, "t": 65, "b": 35},
        legend_title_text="",
        height=390,
    )
    st.plotly_chart(figure, width="stretch", config={"displaylogo": False})


demo_orders, demo_inventory = sample_data(date.today())

with st.sidebar:
    st.header("Control Center")
    source = st.radio("Data source", ["Sample data", "Upload CSVs"])
    with st.expander("Download sample CSVs"):
        st.caption("Use these files as templates for your own data.")
        st.download_button(
            "Orders template", demo_orders.to_csv(index=False),
            "sample_orders.csv", "text/csv", key="sample-orders",
        )
        st.download_button(
            "Inventory template", demo_inventory.to_csv(index=False),
            "sample_inventory.csv", "text/csv", key="sample-inventory",
        )
    if source == "Upload CSVs":
        orders_file = st.file_uploader("Orders CSV", type="csv")
        inventory_file = st.file_uploader("Inventory snapshots CSV", type="csv")
    else:
        orders_file = inventory_file = None

if source == "Upload CSVs":
    if orders_file is None or inventory_file is None:
        st.info(
            "Upload both an orders CSV and an inventory snapshots CSV in the sidebar. "
            "Download the sample files there to see the required format. "
            "Use YYYY-MM-DD dates and one currency (USD)."
        )
        st.stop()
    try:
        orders, inventory = validate_data(
            read_upload(orders_file.getvalue()),
            read_upload(inventory_file.getvalue()),
        )
    except (ValueError, pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeDecodeError) as error:
        st.error(f"Cannot load your CSVs: {error}")
        st.stop()
else:
    orders, inventory = demo_orders, demo_inventory

with st.sidebar:
    st.divider()
    st.header("Dashboard Filters")
    first_date = orders["order_date"].min().date()
    last_date = orders["order_date"].max().date()
    period = st.date_input(
        "Order date range",
        value=(max(first_date, last_date - timedelta(days=59)), last_date),
        min_value=first_date,
        max_value=last_date,
        key=f"period-{source}",
    )
    categories = sorted(set(orders["category"]) | set(inventory["category"]))
    regions = sorted(set(orders["region"]) | set(inventory["region"]))
    selected_categories = st.multiselect("Categories", categories, default=categories)
    selected_regions = st.multiselect("Regions", regions, default=regions)
    low_stock = st.number_input("Low-stock threshold (units)", min_value=0, value=50, step=10)
    st.caption("Inventory uses the latest snapshot per product and region on or before the end date.")

if not isinstance(period, tuple) or len(period) != 2:
    st.info("Choose both a start date and an end date to view the dashboard.")
    st.stop()

start, end = period
cohort = filter_orders(orders, start, end, selected_categories, selected_regions)
stock = inventory_as_of(inventory, end, selected_categories, selected_regions)
metrics = calculate_metrics(cohort, stock)
product_totals = (
    cohort.groupby("product", as_index=False)[["revenue", "fulfilled_units"]]
    .sum()
    .sort_values("revenue", ascending=False)
)
top_product = (
    str(product_totals.iloc[0]["product"]) if metrics.revenue > 0 else "N/A"
)

st.caption(
    f"{'SYNTHETIC DEMO DATA' if source == 'Sample data' else 'UPLOADED DATA'}"
    f"  ·  {start:%b %d, %Y} – {end:%b %d, %Y}"
    f"  ·  {metrics.order_count:,} orders  ·  USD"
)

cards = st.columns(5)
cards[0].metric(
    "Revenue", f"${metrics.revenue:,.0f}",
    help="Fulfilled units shipped by the end date × unit price, for orders in the selected period.",
)
cards[1].metric(
    "Inventory", f"{metrics.inventory:,}" if not stock.empty else "N/A",
    help="On-hand units from the latest snapshot per product/region at the end date.",
)
cards[2].metric(
    "Fill Rate", f"{metrics.fill_rate:.1f}%" if metrics.fill_rate is not None else "N/A",
    help="Total fulfilled units ÷ total ordered units. This is unit-weighted, not an average of percentages.",
)
cards[3].metric(
    "Avg. Shipping", f"{metrics.shipping_days:.1f} days" if metrics.shipping_days is not None else "N/A",
    help="Average shipment-to-delivery days for selected orders delivered by the end date.",
)
cards[4].metric("Top Product", top_product, help="Highest revenue product in the selected order cohort.")

if not selected_categories or not selected_regions:
    st.warning("Select at least one category and one region to display data.")
elif cohort.empty:
    st.warning("No orders match these filters. Inventory can still be available at the selected end date.")
if stock.empty:
    st.warning("No inventory snapshots are available for this selection on or before the end date.")
else:
    stale = stock["snapshot_date"].lt(pd.Timestamp(end))
    if stale.any():
        st.info(
            f"{int(stale.sum()):,} product/region snapshots predate the end date. "
            "Check snapshot dates in the Inventory tab."
        )

performance, order_tab, inventory_tab, guide = st.tabs(
    ["Performance", "Order Explorer", "Inventory", "KPI Guide"]
)

with performance:
    if not cohort.empty:
        daily = cohort.groupby("order_date")[["revenue", "ordered_units", "fulfilled_units"]].sum()
        daily = daily.reindex(pd.date_range(start, end), fill_value=0)
        daily.index.name = "order_date"
        daily = daily.reset_index()
        daily["fill_rate"] = (
            100 * daily["fulfilled_units"]
            / daily["ordered_units"].where(daily["ordered_units"].gt(0))
        )
        left, right = st.columns(2)
        with left:
            figure = px.area(
                daily, x="order_date", y="revenue", title="Revenue by Order Date",
                labels={"order_date": "Order date", "revenue": "Revenue (USD)"},
                color_discrete_sequence=["#2563eb"],
            )
            figure.update_yaxes(tickprefix="$")
            show_chart(figure)
        with right:
            ranking = st.radio("Rank products by", ["Revenue", "Fulfilled units"], horizontal=True)
            measure = "revenue" if ranking == "Revenue" else "fulfilled_units"
            top = product_totals.nlargest(8, measure).sort_values(measure)
            figure = px.bar(
                top, x=measure, y="product", orientation="h",
                title="Top Products",
                labels={"product": "", measure: "Revenue (USD)" if measure == "revenue" else "Fulfilled units"},
                color_discrete_sequence=["#2563eb"],
            )
            show_chart(figure)
        left, right = st.columns(2)
        with left:
            figure = px.line(
                daily, x="order_date", y="fill_rate", title="Daily Fill Rate",
                labels={"order_date": "Order date", "fill_rate": "Fill rate (%)"},
                color_discrete_sequence=["#2563eb"],
            )
            figure.update_yaxes(range=[0, 105], ticksuffix="%")
            show_chart(figure)
        with right:
            transit = cohort.dropna(subset=["shipping_days"])
            if transit.empty:
                st.info("No delivered orders in this selection. Shipping time is unavailable.")
            else:
                by_region = transit.groupby("region", as_index=False)["shipping_days"].mean()
                figure = px.bar(
                    by_region, x="region", y="shipping_days",
                    title="Shipping Time by Region",
                    labels={"region": "Region", "shipping_days": "Days in transit"},
                    color_discrete_sequence=["#60a5fa"],
                )
                show_chart(figure)
    else:
        st.info("Choose a date range, category, and region with orders to see performance charts.")

with order_tab:
    st.subheader("Order-level detail")
    st.caption(
        f"{metrics.fulfilled_units:,} units fulfilled across {metrics.order_count:,} orders. "
        "Fulfillment and delivery reflect the selected end date."
    )
    st.dataframe(
        cohort.sort_values("order_date", ascending=False),
        hide_index=True, width="stretch",
        column_config={
            "unit_price": st.column_config.NumberColumn("Unit price (USD)", format="$%.2f"),
            "revenue": st.column_config.NumberColumn("Revenue (USD)", format="$%.2f"),
        },
    )
    st.download_button(
        "Download filtered orders", cohort.to_csv(index=False, date_format="%Y-%m-%d"),
        "filtered_orders.csv", "text/csv",
    )

with inventory_tab:
    st.subheader("Inventory at Reporting Cutoff")
    if not stock.empty:
        low_count = int(stock["stock_quantity"].le(low_stock).sum())
        st.caption(
            f"{low_count:,} of {len(stock):,} product/region positions have "
            f"{low_stock:,} units or fewer. Snapshot dates may differ."
        )
        levels = stock.groupby("product", as_index=False)["stock_quantity"].sum()
        figure = px.bar(
            levels.sort_values("stock_quantity"), x="stock_quantity", y="product",
            orientation="h", title="On-hand Units by Product",
            labels={"product": "", "stock_quantity": "Units on hand"},
            color_discrete_sequence=["#2563eb"],
        )
        show_chart(figure)
        stock_display = stock.assign(
            status=stock["stock_quantity"].map(lambda quantity: "Low stock" if quantity <= low_stock else "Healthy")
        )
        st.dataframe(
            stock_display.sort_values("stock_quantity"), hide_index=True, width="stretch",
        )
        st.download_button(
            "Download inventory snapshot", stock_display.to_csv(index=False, date_format="%Y-%m-%d"),
            "inventory_at_cutoff.csv", "text/csv",
        )
    else:
        st.info("No inventory snapshots match the selected reporting cutoff and filters.")

with guide:
    st.subheader("How to Read This Dashboard")
    st.markdown(
        """
        - **Revenue:** Fulfilled units multiplied by unit selling price, excluding taxes,
          shipping fees, returns, and discounts. All prices are assumed to be USD.
        - **Inventory:** Latest stock snapshot for each product and region on or before
          the end date. This is a point-in-time balance, never a sum across snapshot dates.
        - **Fill rate:** Total fulfilled units divided by total ordered units, multiplied
          by 100. Pending shipments count as unfulfilled at the cutoff.
        - **Shipping time:** Average calendar days from shipment to delivery, considering
          only orders delivered by the end date. Pending deliveries are excluded.
        - **Top product:** Product with the highest revenue in the selected order cohort.
          Ties show one of the tied products.

        Date filters select orders by **order date**, not shipment date. Revenue is an
        operational sales measure, not an accounting revenue-recognition report.
        The same cohort is used for revenue, fill rate, top products, and shipping time.
        Inventory is independent of the order start date.

        **CSV uploads:** Upload both files. Use the sidebar downloads as templates.
        Dates must use `YYYY-MM-DD`; shipment and delivery may be blank while pending.
        Each order row represents one product, with a unique `order_id`.
        Unit quantities must be whole, nonnegative numbers; ordered units must exceed zero.
        The app rejects invalid values, duplicate keys, and inconsistent product categories.
        Each file supports up to 100,000 rows. Uploaded data is processed in memory,
        cached for the running application, and is not written to a database.
        """
    )

st.caption("Built with Streamlit · Plotly · Pandas  |  Supply Chain Operations")