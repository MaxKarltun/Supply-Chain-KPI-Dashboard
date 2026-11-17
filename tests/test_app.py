import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import streamlit as st
from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


class DashboardAppTests(unittest.TestCase):
    def test_sample_dashboard_renders_all_kpis_and_charts(self):
        app = AppTest.from_file(str(APP_PATH), default_timeout=60).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(
            [metric.label for metric in app.metric],
            ["Revenue", "Inventory", "Fill Rate", "Avg. Shipping", "Top Product"],
        )
        self.assertEqual(len(app.get("plotly_chart")), 5)
        self.assertNotEqual(app.metric[0].value, "$0")

    def test_empty_category_selection_is_explained(self):
        app = AppTest.from_file(str(APP_PATH), default_timeout=60).run()
        app.sidebar.multiselect[0].set_value([]).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.metric[2].value, "N/A")
        self.assertEqual(len(app.get("plotly_chart")), 0)
        self.assertTrue(any("Select at least one" in warning.value for warning in app.warning))

    def test_upload_mode_requires_both_files_instead_of_showing_demo_metrics(self):
        app = AppTest.from_file(str(APP_PATH), default_timeout=60).run()
        app.sidebar.radio[0].set_value("Upload CSVs").run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.metric), 0)
        self.assertTrue(any("Upload both" in notice.value for notice in app.info))

    def test_csv_exports_match_displayed_kpis(self):
        with patch("streamlit.download_button", wraps=st.download_button) as downloads:
            app = AppTest.from_file(str(APP_PATH), default_timeout=60).run()
        self.assertEqual(len(app.exception), 0)
        payloads = {call.args[0]: call.args[1] for call in downloads.call_args_list}
        orders = pd.read_csv(StringIO(payloads["Download filtered orders"]))
        inventory = pd.read_csv(StringIO(payloads["Download inventory snapshot"]))
        self.assertGreater(len(orders), 0)
        self.assertEqual(app.metric[0].value, f"${orders['revenue'].sum():,.0f}")
        self.assertEqual(app.metric[1].value, f"{inventory['stock_quantity'].sum():,}")
        self.assertFalse(inventory.duplicated(["product", "region"]).any())
        self.assertIn("status", inventory.columns)


if __name__ == "__main__":
    unittest.main()
