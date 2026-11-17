import unittest
from datetime import date

import pandas as pd

from dashboard_data import (
    calculate_metrics,
    filter_orders,
    generate_sample_data,
    inventory_as_of,
    validate_data,
)


class DashboardDataTests(unittest.TestCase):
    def setUp(self):
        self.orders = pd.DataFrame([
            ["A", "2026-01-01", "Desk", "Office", "East", 10, 8, 20, "2026-01-02", "2026-01-04"],
            ["B", "2026-01-02", "Desk", "Office", "East", 30, 30, 10, "2026-01-05", "2026-01-06"],
            ["C", "2026-01-02", "Lamp", "Office", "West", 5, 5, 12, "2026-01-02", None],
        ], columns=[
            "order_id", "order_date", "product", "category", "region",
            "ordered_units", "fulfilled_units", "unit_price", "ship_date", "delivery_date",
        ])
        self.inventory = pd.DataFrame([
            ["2025-12-30", "Desk", "Office", "East", 100],
            ["2026-01-03", "Desk", "Office", "East", 70],
            ["2026-01-07", "Desk", "Office", "East", 50],
            ["2026-01-01", "Lamp", "Office", "West", 20],
        ], columns=["snapshot_date", "product", "category", "region", "stock_quantity"])

    def test_weighted_fill_rate_and_historical_cutoff(self):
        orders, stock = validate_data(self.orders, self.inventory)
        cohort = filter_orders(orders, date(2026, 1, 1), date(2026, 1, 4), ["Office"], ["East"])
        snapshot = inventory_as_of(stock, date(2026, 1, 4), ["Office"], ["East"])
        metrics = calculate_metrics(cohort, snapshot)
        self.assertEqual(metrics.revenue, 160)
        self.assertEqual(metrics.fill_rate, 20)
        self.assertEqual(metrics.shipping_days, 2)
        self.assertEqual(metrics.inventory, 70)
        self.assertEqual(metrics.order_count, 2)
        self.assertEqual(cohort.loc[cohort["order_id"].eq("B"), "fulfilled_units"].iloc[0], 0)

    def test_undelivered_orders_do_not_contribute_transit_time(self):
        orders, stock = validate_data(self.orders, self.inventory)
        cohort = filter_orders(orders, date(2026, 1, 2), date(2026, 1, 3), ["Office"], ["West"])
        snapshot = inventory_as_of(stock, date(2026, 1, 3), ["Office"], ["West"])
        metrics = calculate_metrics(cohort, snapshot)
        self.assertEqual(metrics.revenue, 60)
        self.assertEqual(metrics.fill_rate, 100)
        self.assertIsNone(metrics.shipping_days)
        self.assertEqual(metrics.inventory, 20)

    def test_empty_selection_and_no_snapshot(self):
        orders, stock = validate_data(self.orders, self.inventory)
        cohort = filter_orders(orders, date(2026, 1, 1), date(2026, 1, 2), [], ["East"])
        snapshot = inventory_as_of(stock, date(2025, 1, 1), ["Office"], ["East"])
        metrics = calculate_metrics(cohort, snapshot)
        self.assertEqual(metrics.revenue, 0)
        self.assertEqual(metrics.inventory, 0)
        self.assertIsNone(metrics.fill_rate)
        self.assertIsNone(metrics.shipping_days)

    def test_delivery_after_cutoff_is_excluded(self):
        orders, stock = validate_data(self.orders, self.inventory)
        cohort = filter_orders(orders, date(2026, 1, 1), date(2026, 1, 2), ["Office"], ["East"])
        self.assertEqual(calculate_metrics(cohort, stock).revenue, 160)
        self.assertTrue(cohort["delivery_date"].isna().all())
        self.assertIsNone(calculate_metrics(cohort, stock).shipping_days)

    def test_invalid_uploads_have_explicit_errors(self):
        cases = [
            ("fulfilled_units", 11, "cannot exceed"),
            ("ordered_units", 0, "greater than zero"),
            ("ordered_units", 1.5, "whole units"),
            ("unit_price", float("inf"), "finite"),
            ("unit_price", -1, "nonnegative"),
            ("ship_date", "2025-12-31", "dates must follow"),
            ("ship_date", None, "require ship_date"),
            ("delivery_date", "not-a-date", "YYYY-MM-DD"),
            ("category", "", "cannot be blank"),
        ]
        for column, value, message in cases:
            with self.subTest(column=column, value=value):
                orders = self.orders.astype(object)
                orders.loc[0, column] = value
                with self.assertRaisesRegex(ValueError, message):
                    validate_data(orders, self.inventory)

    def test_duplicate_keys_and_inconsistent_categories_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "order_id must be unique"):
            validate_data(pd.concat([self.orders, self.orders]), self.inventory)
        with self.assertRaisesRegex(ValueError, "must be unique"):
            validate_data(self.orders, pd.concat([self.inventory, self.inventory]))
        inventory = self.inventory.copy()
        inventory.loc[0, "category"] = "Other"
        with self.assertRaisesRegex(ValueError, "same category"):
            validate_data(self.orders, inventory)
        with self.assertRaisesRegex(ValueError, "missing columns"):
            validate_data(self.orders.drop(columns="region"), self.inventory)

    def test_sample_data_is_repeatable_and_valid_after_csv_roundtrip(self):
        from io import StringIO

        first = generate_sample_data(date(2026, 11, 17))
        second = generate_sample_data(date(2026, 11, 17))
        for left, right in zip(first, second):
            pd.testing.assert_frame_equal(left, right)
        orders, stock = validate_data(
            pd.read_csv(StringIO(first[0].to_csv(index=False))),
            pd.read_csv(StringIO(first[1].to_csv(index=False))),
        )
        self.assertGreater(len(orders), 1000)
        self.assertEqual(len(stock), 180 * 8 * 3)
        self.assertLessEqual(orders["delivery_date"].max(), pd.Timestamp("2026-11-17"))


if __name__ == "__main__":
    unittest.main()
