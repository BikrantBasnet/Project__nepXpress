import unittest
from unittest.mock import patch
from flask import Flask, Blueprint, session
from app.controllers.AdminReportsController import AdminReportsController


def make_test_app():
    """Builds a minimal Flask app with real blueprints so url_for() resolves correctly."""
    app = Flask(__name__)
    app.secret_key = "test-secret"
    bp = Blueprint("admin", __name__)
    bp.route("/reports", endpoint="reports")(lambda: "reports")
    app.register_blueprint(bp, url_prefix="/admin")
    return app


class TestGetRevenueMonthly(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()

    @patch("app.controllers.AdminReportsController.execute_query")
    def test_get_revenue_monthly_casts_revenue_to_float(self, mock_execute):
        """get_revenue_monthly converts each row's revenue to a float."""
        mock_execute.return_value = [
            {"month": "Jun 2026", "month_key": "2026-06", "revenue": 37550, "shipments": 20}
        ]
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminReportsController.get_revenue_monthly()
            self.assertEqual(status, 200)
            body = response.get_json()
            self.assertTrue(body["success"])
            self.assertIsInstance(body["data"][0]["revenue"], float)
            self.assertEqual(body["data"][0]["revenue"], 37550.0)

    @patch("app.controllers.AdminReportsController.execute_query")
    def test_get_revenue_monthly_empty_result_returns_empty_list(self, mock_execute):
        """get_revenue_monthly returns an empty list when no delivered shipments exist."""
        mock_execute.return_value = []
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminReportsController.get_revenue_monthly()
            body = response.get_json()
            self.assertEqual(body["data"], [])

    @patch("app.controllers.AdminReportsController.execute_query", side_effect=Exception("DB Error"))
    def test_get_revenue_monthly_exception_returns_500(self, mock_execute):
        """Exception in get_revenue_monthly returns 500 with the raw error message."""
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminReportsController.get_revenue_monthly()
            self.assertEqual(status, 500)
            body = response.get_json()
            self.assertFalse(body["success"])
            self.assertEqual(body["message"], "DB Error")

    def test_get_revenue_monthly_blocked_without_admin_session(self):
        """Unauthenticated requests receive a 401 JSON response."""
        with self.app.test_request_context():
            response, status = AdminReportsController.get_revenue_monthly()
            self.assertEqual(status, 401)
            body = response.get_json()
            self.assertFalse(body["success"])


class TestGetShipmentsMonthly(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()

    @patch("app.controllers.AdminReportsController.execute_query")
    def test_get_shipments_monthly_returns_rows_grouped_by_status(self, mock_execute):
        """get_shipments_monthly returns the per-month per-status breakdown as-is."""
        mock_execute.return_value = [
            {"month": "Jun 2026", "month_key": "2026-06", "status": "delivered", "count": 20},
            {"month": "Jun 2026", "month_key": "2026-06", "status": "in_transit", "count": 20},
        ]
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminReportsController.get_shipments_monthly()
            self.assertEqual(status, 200)
            body = response.get_json()
            self.assertEqual(len(body["data"]), 2)

    @patch("app.controllers.AdminReportsController.execute_query", side_effect=Exception("DB Error"))
    def test_get_shipments_monthly_exception_returns_500(self, mock_execute):
        """Exception in get_shipments_monthly returns 500."""
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminReportsController.get_shipments_monthly()
            self.assertEqual(status, 500)
            body = response.get_json()
            self.assertFalse(body["success"])


class TestGetAgentPerformance(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()

    @patch("app.controllers.AdminReportsController.execute_query")
    def test_get_agent_performance_computes_success_pct(self, mock_execute):
        """get_agent_performance calculates success_pct from delivered/total."""
        mock_execute.return_value = [
            {"name": "agentsam", "total": 4, "delivered": 2, "delayed": 1,
             "in_transit": 1, "revenue": 3000}
        ]
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminReportsController.get_agent_performance()
            self.assertEqual(status, 200)
            body = response.get_json()
            self.assertEqual(body["data"][0]["success_pct"], 50.0)
            self.assertIsInstance(body["data"][0]["revenue"], float)

    @patch("app.controllers.AdminReportsController.execute_query")
    def test_get_agent_performance_zero_total_avoids_division_error(self, mock_execute):
        """get_agent_performance returns success_pct=0 when an agent has zero shipments."""
        mock_execute.return_value = [
            {"name": "new_agent", "total": 0, "delivered": 0, "delayed": 0,
             "in_transit": 0, "revenue": 0}
        ]
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminReportsController.get_agent_performance()
            self.assertEqual(status, 200)
            body = response.get_json()
            self.assertEqual(body["data"][0]["success_pct"], 0)

    @patch("app.controllers.AdminReportsController.execute_query")
    def test_get_agent_performance_rounds_to_one_decimal(self, mock_execute):
        """get_agent_performance rounds success_pct to one decimal place."""
        mock_execute.return_value = [
            {"name": "agentsam", "total": 3, "delivered": 1, "delayed": 1,
             "in_transit": 1, "revenue": 1500}
        ]
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminReportsController.get_agent_performance()
            body = response.get_json()
            self.assertEqual(body["data"][0]["success_pct"], 33.3)

    @patch("app.controllers.AdminReportsController.execute_query", side_effect=Exception("DB Error"))
    def test_get_agent_performance_exception_returns_500(self, mock_execute):
        """Exception in get_agent_performance returns 500."""
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminReportsController.get_agent_performance()
            self.assertEqual(status, 500)
            body = response.get_json()
            self.assertFalse(body["success"])


class TestGetCustomerActivity(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()

    @patch("app.controllers.AdminReportsController.execute_query")
    def test_get_customer_activity_formats_total_spent_and_last_order(self, mock_execute):
        """get_customer_activity casts total_spent to float and last_order to string."""
        mock_execute.return_value = [
            {"name": "Bikrant Bhattarai", "total_shipments": 6,
             "total_spent": 9300, "last_order": "2026-06-14 10:05:33"}
        ]
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminReportsController.get_customer_activity()
            self.assertEqual(status, 200)
            body = response.get_json()
            self.assertIsInstance(body["data"][0]["total_spent"], float)
            self.assertEqual(body["data"][0]["last_order"], "2026-06-14 10:05:33")

    @patch("app.controllers.AdminReportsController.execute_query")
    def test_get_customer_activity_handles_null_last_order(self, mock_execute):
        """get_customer_activity sets last_order to None for customers with no shipments."""
        mock_execute.return_value = [
            {"name": "New Customer", "total_shipments": 0, "total_spent": 0, "last_order": None}
        ]
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminReportsController.get_customer_activity()
            body = response.get_json()
            self.assertIsNone(body["data"][0]["last_order"])

    @patch("app.controllers.AdminReportsController.execute_query", side_effect=Exception("DB Error"))
    def test_get_customer_activity_exception_returns_500(self, mock_execute):
        """Exception in get_customer_activity returns 500."""
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminReportsController.get_customer_activity()
            self.assertEqual(status, 500)
            body = response.get_json()
            self.assertFalse(body["success"])


class TestGetSummary(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()

    @patch("app.controllers.AdminReportsController.execute_query")
    def test_get_summary_returns_all_four_kpis_as_correct_types(self, mock_execute):
        """get_summary returns revenue and avg_order_value as floats, counts as-is."""
        mock_execute.side_effect = [
            {"v": 37550},
            {"v": 102},
            {"v": 35},
            {"v": 1878.04},
        ]
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminReportsController.get_summary()
            self.assertEqual(status, 200)
            body = response.get_json()
            self.assertTrue(body["success"])
            self.assertIsInstance(body["data"]["total_revenue"], float)
            self.assertEqual(body["data"]["total_revenue"], 37550.0)
            self.assertEqual(body["data"]["total_shipments"], 102)
            self.assertEqual(body["data"]["total_customers"], 35)
            self.assertIsInstance(body["data"]["avg_order_value"], float)

    @patch("app.controllers.AdminReportsController.execute_query", side_effect=Exception("DB Error"))
    def test_get_summary_exception_returns_500(self, mock_execute):
        """Exception in get_summary returns 500 with the raw error message."""
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminReportsController.get_summary()
            self.assertEqual(status, 500)
            body = response.get_json()
            self.assertFalse(body["success"])
            self.assertEqual(body["message"], "DB Error")


if __name__ == "__main__":
    unittest.main()