from dataclasses import dataclass
from datetime import date
from random import Random

import pandas as pd


ORDER_COLUMNS = [
    "order_id", "order_date", "product", "category", "region",
    "ordered_units", "fulfilled_units", "unit_price", "ship_date", "delivery_date",
]
INVENTORY_COLUMNS = [
    "snapshot_date", "product", "category", "region", "stock_quantity",
]
MAX_ROWS = 100_000


@dataclass(frozen=True)
class Metrics:
    revenue: float
    inventory: int
    fill_rate: float | None
    shipping_days: float | None
    order_count: int
    fulfilled_units: int


def generate_sample_data(as_of: date) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = Random(42)
    products = [
        ("Wireless Headphones", "Electronics", 89.00),
        ("Smart Speaker", "Electronics", 65.00),
        ("USB-C Hub", "Electronics", 39.00),
        ("Desk Lamp", "Home & Office", 45.00),
        ("Ergonomic Chair", "Home & Office", 249.00),
        ("Standing Desk", "Home & Office", 399.00),
        ("Travel Backpack", "Lifestyle", 75.00),
        ("Insulated Bottle", "Lifestyle", 29.00),
    ]
    regions = ["East", "Central", "West"]
    cutoff = pd.Timestamp(as_of)
    orders = []
    inventory = []
    for day in pd.date_range(end=cutoff, periods=180):
        for _ in range(rng.randint(8, 16)):
            product, category, price = rng.choice(products)
            ordered = rng.randint(2, 35)
            fulfilled = max(1, ordered - rng.choices([0, 1, 3, 5], [75, 12, 8, 5])[0])
            ship = day + pd.Timedelta(days=rng.randint(0, 3))
            delivered = ship + pd.Timedelta(days=rng.randint(1, 7))
            if ship > cutoff:
                ship, delivered, fulfilled = pd.NaT, pd.NaT, 0
            elif delivered > cutoff:
                delivered = pd.NaT
            orders.append({
                "order_id": f"ORD-{len(orders) + 1:05d}",
                "order_date": day,
                "product": product,
                "category": category,
                "region": rng.choice(regions),
                "ordered_units": ordered,
                "fulfilled_units": fulfilled,
                "unit_price": price,
                "ship_date": ship,
                "delivery_date": delivered,
            })
        for product, category, _ in products:
            for region in regions:
                inventory.append({
                    "snapshot_date": day,
                    "product": product,
                    "category": category,
                    "region": region,
                    "stock_quantity": rng.randint(0, 450),
                })
    return pd.DataFrame(orders), pd.DataFrame(inventory)


def _validate_table(
    source: pd.DataFrame,
    columns: list[str],
    required_dates: list[str],
    optional_dates: list[str],
    numeric_columns: list[str],
    whole_numbers: list[str],
    name: str,
) -> pd.DataFrame:
    missing = sorted(set(columns) - set(source.columns))
    if missing:
        raise ValueError(f"{name}: missing columns: {', '.join(missing)}.")
    if source.empty or len(source) > MAX_ROWS:
        raise ValueError(f"{name}: provide between 1 and {MAX_ROWS:,} rows.")
    frame = source.loc[:, columns].copy()
    text_columns = ["product", "category", "region"]
    if "order_id" in columns:
        text_columns.append("order_id")
    for column in text_columns:
        text = frame[column].astype("string").str.strip()
        if text.isna().any() or text.eq("").any():
            raise ValueError(f"{name}: {column} cannot be blank.")
        frame[column] = text
    for column in required_dates + optional_dates:
        text = frame[column].astype("string").str.strip()
        blank = text.isna() | text.eq("")
        parsed = pd.to_datetime(text, format="%Y-%m-%d", errors="coerce")
        malformed = ~blank & (
            ~text.str.fullmatch(r"\d{4}-\d{2}-\d{2}", na=False) | parsed.isna()
        )
        if malformed.any() or (column in required_dates and blank.any()):
            raise ValueError(f"{name}: {column} must use valid YYYY-MM-DD dates.")
        frame[column] = parsed
    for column in numeric_columns:
        values = pd.to_numeric(frame[column], errors="coerce")
        if (
            values.isna().any()
            or values.isin([float("inf"), float("-inf")]).any()
            or values.lt(0).any()
        ):
            raise ValueError(f"{name}: {column} must contain finite, nonnegative numbers.")
        if column in whole_numbers and values.mod(1).ne(0).any():
            raise ValueError(f"{name}: {column} must contain whole units.")
        frame[column] = values
    return frame


def validate_data(
    orders: pd.DataFrame, inventory: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    orders = _validate_table(
        orders, ORDER_COLUMNS, ["order_date"], ["ship_date", "delivery_date"],
        ["ordered_units", "fulfilled_units", "unit_price"],
        ["ordered_units", "fulfilled_units"], "Orders",
    )
    inventory = _validate_table(
        inventory, INVENTORY_COLUMNS, ["snapshot_date"], [],
        ["stock_quantity"], ["stock_quantity"], "Inventory",
    )
    if orders["order_id"].duplicated().any():
        raise ValueError("Orders: order_id must be unique; use one product per order row.")
    if orders["ordered_units"].le(0).any():
        raise ValueError("Orders: ordered_units must be greater than zero.")
    if orders["fulfilled_units"].gt(orders["ordered_units"]).any():
        raise ValueError("Orders: fulfilled_units cannot exceed ordered_units.")
    shipped = orders["ship_date"].notna()
    delivered = orders["delivery_date"].notna()
    if (shipped != orders["fulfilled_units"].gt(0)).any():
        raise ValueError("Orders: positive fulfilled_units require ship_date, and vice versa.")
    if (
        (orders["ship_date"] < orders["order_date"]).any()
        or (delivered & ~shipped).any()
        or (orders["delivery_date"] < orders["ship_date"]).any()
    ):
        raise ValueError("Orders: dates must follow order_date <= ship_date <= delivery_date.")
    if inventory.duplicated(["snapshot_date", "product", "region"]).any():
        raise ValueError("Inventory: each snapshot_date/product/region must be unique.")
    dimensions = pd.concat([
        orders[["product", "category"]], inventory[["product", "category"]],
    ])
    if dimensions.groupby("product")["category"].nunique().gt(1).any():
        raise ValueError("Each product must have the same category in both datasets.")
    line_revenue = orders["fulfilled_units"] * orders["unit_price"]
    if line_revenue.isin([float("inf"), float("-inf")]).any():
        raise ValueError("Orders: revenue exceeds the supported numeric range.")
    return orders, inventory


def filter_orders(
    orders: pd.DataFrame,
    start: date,
    end: date,
    categories: list[str],
    regions: list[str],
) -> pd.DataFrame:
    cutoff = pd.Timestamp(end)
    mask = (
        orders["order_date"].between(pd.Timestamp(start), cutoff)
        & orders["category"].isin(categories)
        & orders["region"].isin(regions)
    )
    selected = orders.loc[mask].copy()
    not_shipped = selected["ship_date"].isna() | selected["ship_date"].gt(cutoff)
    selected.loc[not_shipped, "fulfilled_units"] = 0
    selected.loc[not_shipped, ["ship_date", "delivery_date"]] = pd.NaT
    selected.loc[selected["delivery_date"].gt(cutoff), "delivery_date"] = pd.NaT
    selected["revenue"] = selected["fulfilled_units"] * selected["unit_price"]
    selected["shipping_days"] = (
        selected["delivery_date"] - selected["ship_date"]
    ).dt.days
    return selected


def inventory_as_of(
    inventory: pd.DataFrame,
    end: date,
    categories: list[str],
    regions: list[str],
) -> pd.DataFrame:
    mask = (
        inventory["snapshot_date"].le(pd.Timestamp(end))
        & inventory["category"].isin(categories)
        & inventory["region"].isin(regions)
    )
    return (
        inventory.loc[mask]
        .sort_values("snapshot_date")
        .groupby(["product", "region"], sort=False)
        .tail(1)
        .reset_index(drop=True)
    )


def calculate_metrics(orders: pd.DataFrame, inventory: pd.DataFrame) -> Metrics:
    ordered = int(orders["ordered_units"].sum())
    fulfilled = int(orders["fulfilled_units"].sum())
    transit = orders["shipping_days"].dropna()
    return Metrics(
        revenue=float(orders["revenue"].sum()),
        inventory=int(inventory["stock_quantity"].sum()),
        fill_rate=100 * fulfilled / ordered if ordered else None,
        shipping_days=float(transit.mean()) if not transit.empty else None,
        order_count=len(orders),
        fulfilled_units=fulfilled,
    )
