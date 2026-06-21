import unittest
from unittest.mock import patch
from flask import Flask, Blueprint, session
from app.controllers.shipmentcontrollers import ShipmentController


def make_test_app():
    app = Flask(__name__)
    app.secret_key = "test-secret"
    bp = Blueprint("admin", __name__)
    bp.route("/shipments", endpoint="shipments")(lambda: "shipments")
    app.register_blueprint(bp, url_prefix="/admin")
    return app


class TestGetAll(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()

    @patch("app.models.AdminShipmentModel.ShipmentModel.get_all_paginated")
    def test_get_all_success_returns_paginated_data(self, mock_get_all):
        """get_all returns paginated shipment data with correct structure."""
        mock_get_all.return_value = ([{"id": 1, "tracking_id": "NX-1"}], 1)
        with self.app.test_request_context("/?page=2&limit=10&status=in_transit&search=ktm"):
            session["admin_logged_in"] = True
            response, status = ShipmentController.get_all()
            self.assertEqual(status, 200)
            body = response.get_json()
            self.assertTrue(body["success"])
            self.assertEqual(body["data"]["shipments"], [{"id": 1, "tracking_id": "NX-1"}])
            self.assertEqual(body["data"]["pagination"]["page"], 2)
            self.assertEqual(body["data"]["pagination"]["limit"], 10)
            self.assertEqual(body["data"]["pagination"]["total"], 1)
            self.assertEqual(body["data"]["pagination"]["total_pages"], 1)

    @patch("app.models.AdminShipmentModel.ShipmentModel.get_all_paginated")
    def test_get_all_uses_default_pagination_when_no_params(self, mock_get_all):
        """get_all falls back to page=1 and limit=20 when no query params are given."""
        mock_get_all.return_value = ([], 0)
        with self.app.test_request_context("/"):
            session["admin_logged_in"] = True
            response, status = ShipmentController.get_all()
            body = response.get_json()
            self.assertEqual(body["data"]["pagination"]["page"], 1)
            self.assertEqual(body["data"]["pagination"]["limit"], 20)

    @patch("app.models.AdminShipmentModel.ShipmentModel.get_all_paginated", side_effect=Exception("DB Error"))
    def test_get_all_exception_returns_500_error(self, mock_get_all):
        """Exception in get_all returns 500 with error message."""
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = ShipmentController.get_all()
            self.assertEqual(status, 500)
            body = response.get_json()
            self.assertFalse(body["success"])
            self.assertEqual(body["message"], "DB Error")

    def test_get_all_blocked_without_admin_session(self):
        """Unauthenticated requests to get_all receive a 401 JSON response."""
        with self.app.test_request_context("/"):
            response, status = ShipmentController.get_all()
            self.assertEqual(status, 401)
            body = response.get_json()
            self.assertFalse(body["success"])


class TestGetOne(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()

    @patch("app.models.AdminShipmentModel.ShipmentModel.get_by_id")
    def test_get_one_success_formats_dates(self, mock_get_by_id):
        """get_one retrieves shipment and converts datetime fields to strings."""
        mock_get_by_id.return_value = {"id": 1, "created_at": "2026-01-01", "updated_at": None}
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = ShipmentController.get_one(1)
            self.assertEqual(status, 200)
            body = response.get_json()
            self.assertTrue(body["success"])
            self.assertEqual(body["data"]["id"], 1)
            self.assertEqual(body["data"]["created_at"], "2026-01-01")
            self.assertIsNone(body["data"]["updated_at"])

    @patch("app.models.AdminShipmentModel.ShipmentModel.get_by_id", return_value=None)
    def test_get_one_not_found_returns_404(self, mock_get_by_id):
        """get_one returns 404 when no shipment matches the given id."""
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = ShipmentController.get_one(999)
            self.assertEqual(status, 404)
            body = response.get_json()
            self.assertFalse(body["success"])
            self.assertEqual(body["message"], "Shipment not found")


class TestCreate(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()

    def test_create_missing_customer_id_returns_400(self):
        """create rejects payload missing customer_id."""
        with self.app.test_request_context(
            method="POST", data="{}", content_type="application/json"
        ):
            session["admin_logged_in"] = True
            response, status = ShipmentController.create()
            self.assertEqual(status, 400)
            body = response.get_json()
            self.assertFalse(body["success"])
            self.assertIn("customer_id", body["message"])

    def test_create_missing_destination_returns_400(self):
        """create rejects payload missing destination."""
        with self.app.test_request_context(
            method="POST",
            data='{"customer_id": 1}',
            content_type="application/json"
        ):
            session["admin_logged_in"] = True
            response, status = ShipmentController.create()
            self.assertEqual(status, 400)
            body = response.get_json()
            self.assertEqual(body["message"], "Missing required field: destination")

    def test_create_missing_amount_returns_400(self):
        """create rejects payload missing amount."""
        with self.app.test_request_context(
            method="POST",
            data='{"customer_id": 1, "destination": "Pokhara"}',
            content_type="application/json"
        ):
            session["admin_logged_in"] = True
            response, status = ShipmentController.create()
            self.assertEqual(status, 400)
            body = response.get_json()
            self.assertEqual(body["message"], "Missing required field: amount")

    @patch("app.models.AdminShipmentModel.ShipmentModel.admin_create", return_value=(5, "NX-999"))
    def test_create_success_returns_201_with_tracking_id(self, mock_admin_create):
        """Valid payload creates shipment and returns 201 with id and tracking_id."""
        with self.app.test_request_context(
            method="POST",
            data='{"customer_id": 1, "destination": "Pokhara", "amount": 500}',
            content_type="application/json"
        ):
            session["admin_logged_in"] = True
            response, status = ShipmentController.create()
            self.assertEqual(status, 201)
            body = response.get_json()
            self.assertTrue(body["success"])
            self.assertEqual(body["data"]["id"], 5)
            self.assertEqual(body["data"]["tracking_id"], "NX-999")
            self.assertEqual(body["message"], "Shipment created")


class TestUpdateStatus(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()

    def test_update_status_invalid_value_returns_400(self):
        """update_status rejects statuses not in ALLOWED_STATUSES."""
        with self.app.test_request_context(
            method="PATCH",
            data='{"status": "invalid_status_value"}',
            content_type="application/json"
        ):
            session["admin_logged_in"] = True
            response, status = ShipmentController.update_status(1)
            self.assertEqual(status, 400)
            body = response.get_json()
            self.assertFalse(body["success"])
            self.assertIn("Invalid status", body["message"])

    @patch("app.models.AdminShipmentModel.ShipmentModel.update_status", return_value=0)
    def test_update_status_not_found_returns_404(self, mock_update):
        """update_status returns 404 when no rows are affected."""
        with self.app.test_request_context(
            method="PATCH",
            data='{"status": "delivered"}',
            content_type="application/json"
        ):
            session["admin_logged_in"] = True
            response, status = ShipmentController.update_status(1)
            self.assertEqual(status, 404)
            body = response.get_json()
            self.assertFalse(body["success"])
            self.assertEqual(body["message"], "Shipment not found")

    @patch("app.models.AdminShipmentModel.ShipmentModel.update_status", return_value=1)
    def test_update_status_success_returns_200(self, mock_update):
        """update_status returns 200 with confirmation message."""
        with self.app.test_request_context(
            method="PATCH",
            data='{"status": "delivered"}',
            content_type="application/json"
        ):
            session["admin_logged_in"] = True
            response, status = ShipmentController.update_status(1)
            self.assertEqual(status, 200)
            body = response.get_json()
            self.assertTrue(body["success"])
            self.assertEqual(body["message"], "Status updated to 'delivered'")


class TestDelete(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()

    @patch("app.models.AdminShipmentModel.ShipmentModel.delete", return_value=0)
    def test_delete_not_found_returns_404(self, mock_delete):
        """delete returns 404 when shipment does not exist."""
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = ShipmentController.delete(1)
            self.assertEqual(status, 404)
            body = response.get_json()
            self.assertFalse(body["success"])
            self.assertEqual(body["message"], "Shipment not found")

    @patch("app.models.AdminShipmentModel.ShipmentModel.delete", return_value=1)
    def test_delete_success_returns_200(self, mock_delete):
        """delete returns 200 with confirmation on successful removal."""
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = ShipmentController.delete(1)
            self.assertEqual(status, 200)
            body = response.get_json()
            self.assertTrue(body["success"])
            self.assertEqual(body["message"], "Shipment deleted")


class TestDropdowns(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()

    @patch("app.models.database.execute_query")
    def test_get_customers_returns_customer_list(self, mock_execute):
        """get_customers returns the correct payload from the DB."""
        mock_execute.return_value = [{"id": 2, "name": "Prabin"}]
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = ShipmentController.get_customers()
            self.assertEqual(status, 200)
            body = response.get_json()
            self.assertTrue(body["success"])
            self.assertEqual(body["data"], [{"id": 2, "name": "Prabin"}])

    @patch("app.models.database.execute_query")
    def test_get_agents_returns_agent_list(self, mock_execute):
        """get_agents returns the correct payload from the DB."""
        mock_execute.return_value = [{"id": 3, "name": "Agent-Ram"}]
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = ShipmentController.get_agents()
            self.assertEqual(status, 200)
            body = response.get_json()
            self.assertTrue(body["success"])
            self.assertEqual(body["data"], [{"id": 3, "name": "Agent-Ram"}])


if __name__ == "__main__":
    unittest.main()