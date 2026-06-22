import unittest
from unittest.mock import patch
from flask import Flask, Blueprint, session
from app.controllers.AdminDashboardController import AdminDashboardController


def make_test_app():
    """Builds a minimal Flask app with real blueprints so url_for() resolves correctly."""
    app = Flask(__name__)
    app.secret_key = "test-secret"
    bp = Blueprint("admin", __name__)
    bp.route("/dashboard", endpoint="dashboard")(lambda: "dashboard")
    app.register_blueprint(bp, url_prefix="/admin")
    return app


class TestGetStats(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()

    @patch("app.controllers.AdminDashboardController.ShipmentModel")
    @patch("app.controllers.AdminDashboardController.User")
    @patch("app.controllers.AdminDashboardController.DeliveryAgentModel")
    def test_get_stats_success_returns_all_six_kpis(self, mock_agent, mock_user, mock_shipment):
        """get_stats assembles all six KPI cards with value and change_pct/new_this_month."""
        mock_shipment.get_total_count.return_value          = 102
        mock_shipment.get_monthly_change.side_effect         = [10.0, 5.0, 0.0]
        mock_shipment.get_count_by_status.side_effect        = [20, 0]
        mock_user.admin_get_active_count.return_value        = 36
        mock_user.admin_get_new_this_month.return_value       = 4
        mock_agent.get_total_count.return_value               = 4
        mock_agent.get_new_agents_this_month.return_value     = 0
        mock_shipment.get_total_revenue.return_value          = 37550.0
        mock_shipment.get_revenue_change_this_month.return_value = 100.0

        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminDashboardController.get_stats()
            self.assertEqual(status, 200)
            body = response.get_json()
            self.assertTrue(body["success"])
            self.assertEqual(body["data"]["total_shipments"]["value"], 102)
            self.assertEqual(body["data"]["delivered"]["value"], 20)
            self.assertEqual(body["data"]["pending"]["value"], 0)
            self.assertEqual(body["data"]["active_users"]["value"], 36)
            self.assertEqual(body["data"]["delivery_agents"]["value"], 4)
            self.assertEqual(body["data"]["revenue_npr"]["value"], 37550.0)

    @patch("app.controllers.AdminDashboardController.ShipmentModel")
    def test_get_stats_revenue_is_cast_to_float(self, mock_shipment):
        """get_stats explicitly casts revenue_npr value to float."""
        mock_shipment.get_total_count.return_value   = 0
        mock_shipment.get_monthly_change.return_value = 0
        mock_shipment.get_count_by_status.return_value = 0
        mock_shipment.get_total_revenue.return_value   = 1000  # int, not float
        mock_shipment.get_revenue_change_this_month.return_value = 0

        with patch("app.controllers.AdminDashboardController.User") as mock_user, \
             patch("app.controllers.AdminDashboardController.DeliveryAgentModel") as mock_agent:
            mock_user.admin_get_active_count.return_value = 0
            mock_user.admin_get_new_this_month.return_value = 0
            mock_agent.get_total_count.return_value = 0
            mock_agent.get_new_agents_this_month.return_value = 0

            with self.app.test_request_context():
                session["admin_logged_in"] = True
                response, status = AdminDashboardController.get_stats()
                body = response.get_json()
                self.assertIsInstance(body["data"]["revenue_npr"]["value"], float)

    @patch("app.controllers.AdminDashboardController.ShipmentModel.get_total_count",
           side_effect=Exception("DB Error"))
    def test_get_stats_exception_returns_500_with_prefixed_message(self, mock_count):
        """Exception in get_stats returns 500 with a 'Failed to load stats:' prefix."""
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminDashboardController.get_stats()
            self.assertEqual(status, 500)
            body = response.get_json()
            self.assertFalse(body["success"])
            self.assertIn("Failed to load stats:", body["message"])

    def test_get_stats_blocked_without_admin_session(self):
        """Unauthenticated requests to get_stats receive a 401 JSON response."""
        with self.app.test_request_context():
            response, status = AdminDashboardController.get_stats()
            self.assertEqual(status, 401)
            body = response.get_json()
            self.assertFalse(body["success"])


class TestGetRecentShipments(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()

    @patch("app.controllers.AdminDashboardController.ShipmentModel.get_recent_shipments")
    def test_get_recent_shipments_formats_created_at_as_string(self, mock_recent):
        """get_recent_shipments converts datetime created_at fields to strings."""
        mock_recent.return_value = [
            {"id": 1, "tracking_id": "NXP-1", "created_at": "2026-06-20 10:00:00"}
        ]
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminDashboardController.get_recent_shipments()
            self.assertEqual(status, 200)
            body = response.get_json()
            self.assertEqual(body["data"][0]["created_at"], "2026-06-20 10:00:00")
            mock_recent.assert_called_once_with(limit=10)

    @patch("app.controllers.AdminDashboardController.ShipmentModel.get_recent_shipments")
    def test_get_recent_shipments_skips_none_created_at(self, mock_recent):
        """get_recent_shipments leaves created_at untouched if it's already None."""
        mock_recent.return_value = [{"id": 1, "created_at": None}]
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminDashboardController.get_recent_shipments()
            body = response.get_json()
            self.assertIsNone(body["data"][0]["created_at"])

    @patch("app.controllers.AdminDashboardController.ShipmentModel.get_recent_shipments",
           side_effect=Exception("DB Error"))
    def test_get_recent_shipments_exception_returns_500(self, mock_recent):
        """Exception in get_recent_shipments returns 500 with prefixed message."""
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminDashboardController.get_recent_shipments()
            self.assertEqual(status, 500)
            body = response.get_json()
            self.assertIn("Failed to load shipments:", body["message"])


class TestGetTopAgents(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()

    @patch("app.controllers.AdminDashboardController.DeliveryAgentModel.get_top_agents")
    def test_get_top_agents_returns_data_with_limit_five(self, mock_top):
        """get_top_agents requests exactly 5 agents from the model."""
        mock_top.return_value = [{"id": 40, "name": "agentsam", "delivery_count": 1}]
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminDashboardController.get_top_agents()
            self.assertEqual(status, 200)
            body = response.get_json()
            self.assertEqual(len(body["data"]), 1)
            mock_top.assert_called_once_with(limit=5)

    @patch("app.controllers.AdminDashboardController.DeliveryAgentModel.get_top_agents",
           side_effect=Exception("DB Error"))
    def test_get_top_agents_exception_returns_500(self, mock_top):
        """Exception in get_top_agents returns 500 with prefixed message."""
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminDashboardController.get_top_agents()
            self.assertEqual(status, 500)
            body = response.get_json()
            self.assertIn("Failed to load agents:", body["message"])


class TestGetDeliveryStatus(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()

    @patch("app.controllers.AdminDashboardController.ShipmentModel.get_status_breakdown")
    def test_get_delivery_status_returns_breakdown(self, mock_breakdown):
        """get_delivery_status returns the status breakdown list as-is."""
        mock_breakdown.return_value = [
            {"status": "delivered", "count": 20, "percentage": 50.0},
            {"status": "in_transit", "count": 20, "percentage": 50.0},
        ]
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminDashboardController.get_delivery_status()
            self.assertEqual(status, 200)
            body = response.get_json()
            self.assertEqual(len(body["data"]), 2)

    @patch("app.controllers.AdminDashboardController.ShipmentModel.get_status_breakdown",
           side_effect=Exception("DB Error"))
    def test_get_delivery_status_exception_returns_500(self, mock_breakdown):
        """Exception in get_delivery_status returns 500 with prefixed message."""
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminDashboardController.get_delivery_status()
            self.assertEqual(status, 500)
            body = response.get_json()
            self.assertIn("Failed to load delivery status:", body["message"])


class TestGetRecentUsers(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()

    @patch("app.controllers.AdminDashboardController.User.admin_get_recent_customers")
    def test_get_recent_users_formats_created_at_and_uses_limit_ten(self, mock_recent):
        """get_recent_users converts datetime fields and requests limit=10."""
        mock_recent.return_value = [{"id": 1, "name": "Samyog", "created_at": "2026-06-20"}]
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminDashboardController.get_recent_users()
            self.assertEqual(status, 200)
            body = response.get_json()
            self.assertEqual(body["data"][0]["created_at"], "2026-06-20")
            mock_recent.assert_called_once_with(limit=10)

    @patch("app.controllers.AdminDashboardController.User.admin_get_recent_customers",
           side_effect=Exception("DB Error"))
    def test_get_recent_users_exception_returns_500(self, mock_recent):
        """Exception in get_recent_users returns 500 with prefixed message."""
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminDashboardController.get_recent_users()
            self.assertEqual(status, 500)
            body = response.get_json()
            self.assertIn("Failed to load users:", body["message"])


class TestGetSystemAlerts(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()

    @patch("app.controllers.AdminDashboardController.AlertModel")
    def test_get_system_alerts_returns_alerts_and_unread_count(self, mock_alert):
        """get_system_alerts bundles alerts list with unread_count."""
        mock_alert.get_recent_alerts.return_value = [
            {"id": 1, "title": "Delivery Delayed", "created_at": "2026-06-20 09:00:00"}
        ]
        mock_alert.get_unread_count.return_value = 3
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminDashboardController.get_system_alerts()
            self.assertEqual(status, 200)
            body = response.get_json()
            self.assertEqual(len(body["data"]["alerts"]), 1)
            self.assertEqual(body["data"]["unread_count"], 3)
            mock_alert.get_recent_alerts.assert_called_once_with(limit=10)

    @patch("app.controllers.AdminDashboardController.AlertModel")
    def test_get_system_alerts_formats_created_at_as_string(self, mock_alert):
        """get_system_alerts converts each alert's created_at to a string."""
        mock_alert.get_recent_alerts.return_value = [
            {"id": 1, "created_at": "2026-06-20 09:00:00"}
        ]
        mock_alert.get_unread_count.return_value = 0
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminDashboardController.get_system_alerts()
            body = response.get_json()
            self.assertEqual(body["data"]["alerts"][0]["created_at"], "2026-06-20 09:00:00")

    @patch("app.controllers.AdminDashboardController.AlertModel.get_recent_alerts",
           side_effect=Exception("DB Error"))
    def test_get_system_alerts_exception_returns_500(self, mock_alerts):
        """Exception in get_system_alerts returns 500 with prefixed message."""
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminDashboardController.get_system_alerts()
            self.assertEqual(status, 500)
            body = response.get_json()
            self.assertIn("Failed to load alerts:", body["message"])


class TestMarkAlertRead(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()

    @patch("app.controllers.AdminDashboardController.AlertModel.mark_as_read")
    def test_mark_alert_read_success_returns_200(self, mock_mark):
        """mark_alert_read calls the model and returns a confirmation message."""
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminDashboardController.mark_alert_read(7)
            self.assertEqual(status, 200)
            body = response.get_json()
            self.assertTrue(body["success"])
            self.assertEqual(body["message"], "Alert marked as read")
            mock_mark.assert_called_once_with(7)

    @patch("app.controllers.AdminDashboardController.AlertModel.mark_as_read",
           side_effect=Exception("DB Error"))
    def test_mark_alert_read_exception_returns_500(self, mock_mark):
        """Exception in mark_alert_read returns 500 with the raw error message."""
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminDashboardController.mark_alert_read(7)
            self.assertEqual(status, 500)
            body = response.get_json()
            self.assertFalse(body["success"])
            self.assertEqual(body["message"], "DB Error")


if __name__ == "__main__":
    unittest.main()