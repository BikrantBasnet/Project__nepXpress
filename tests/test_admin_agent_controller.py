import unittest
from unittest.mock import patch
from flask import Flask, Blueprint, session
from app.controllers.AdminAgentController import AdminAgentController


def make_test_app():
    """Builds a minimal Flask app with real blueprints so url_for() resolves correctly."""
    app = Flask(__name__)
    app.secret_key = "test-secret"
    bp = Blueprint("admin", __name__)
    bp.route("/delivery-agents", endpoint="delivery_agents")(lambda: "delivery_agents")
    app.register_blueprint(bp, url_prefix="/admin")
    return app


class TestGetAll(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()

    @patch("app.controllers.AdminAgentController.execute_query")
    def test_get_all_success_returns_paginated_data(self, mock_execute):
        """get_all returns paginated agent data with computed total_pages."""
        mock_execute.side_effect = [
            {"cnt": 1},
            [{"id": 40, "name": "agentsam", "email": "agentsam@gmail.com",
              "phone": "9842907443", "status": "active", "created_at": "2026-06-20",
              "total_deliveries": 1, "completed": 0, "delayed": 0}]
        ]
        with self.app.test_request_context("/?page=1&limit=10&status=active&search=sam"):
            session["admin_logged_in"] = True
            response, status = AdminAgentController.get_all()
            self.assertEqual(status, 200)
            body = response.get_json()
            self.assertTrue(body["success"])
            self.assertEqual(len(body["data"]["agents"]), 1)
            self.assertEqual(body["data"]["pagination"]["total"], 1)
            self.assertEqual(body["data"]["pagination"]["total_pages"], 1)

    @patch("app.controllers.AdminAgentController.execute_query")
    def test_get_all_adds_empty_zone_key_for_frontend_compatibility(self, mock_execute):
        """get_all attaches a blank zone field since users table has no zone column."""
        mock_execute.side_effect = [
            {"cnt": 1},
            [{"id": 1, "name": "A", "created_at": "2026-06-20"}]
        ]
        with self.app.test_request_context("/"):
            session["admin_logged_in"] = True
            response, status = AdminAgentController.get_all()
            body = response.get_json()
            self.assertEqual(body["data"]["agents"][0]["zone"], "")

    @patch("app.controllers.AdminAgentController.execute_query")
    def test_get_all_uses_default_pagination_when_no_params(self, mock_execute):
        """get_all falls back to page=1 and limit=10 when no query params are given."""
        mock_execute.side_effect = [{"cnt": 0}, []]
        with self.app.test_request_context("/"):
            session["admin_logged_in"] = True
            response, status = AdminAgentController.get_all()
            body = response.get_json()
            self.assertEqual(body["data"]["pagination"]["page"], 1)
            self.assertEqual(body["data"]["pagination"]["limit"], 10)

    @patch("app.controllers.AdminAgentController.execute_query", side_effect=Exception("DB Error"))
    def test_get_all_exception_returns_500_error(self, mock_execute):
        """Exception in get_all returns 500 with error message."""
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminAgentController.get_all()
            self.assertEqual(status, 500)
            body = response.get_json()
            self.assertFalse(body["success"])
            self.assertEqual(body["message"], "DB Error")

    def test_get_all_blocked_without_admin_session(self):
        """Unauthenticated requests to get_all receive a 401 JSON response."""
        with self.app.test_request_context("/"):
            response, status = AdminAgentController.get_all()
            self.assertEqual(status, 401)
            body = response.get_json()
            self.assertFalse(body["success"])


class TestGetOne(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()

    @patch("app.controllers.AdminAgentController.execute_query")
    def test_get_one_success_returns_agent_and_shipments(self, mock_execute):
        """get_one retrieves agent performance stats and recent shipments."""
        mock_execute.side_effect = [
            {"id": 40, "name": "agentsam", "email": "agentsam@gmail.com",
             "phone": "9842907443", "status": "active", "created_at": "2026-06-20",
             "total_deliveries": 1, "completed": 0, "delayed": 0, "in_transit": 1},
            [{"tracking_id": "NXP-1599-5500", "customer_name": "Samyog Rai",
              "destination": "Biratnagar", "status": "in_transit",
              "amount": 1500, "created_at": "2026-06-20"}]
        ]
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminAgentController.get_one(40)
            self.assertEqual(status, 200)
            body = response.get_json()
            self.assertTrue(body["success"])
            self.assertEqual(body["data"]["agent"]["id"], 40)
            self.assertEqual(body["data"]["agent"]["zone"], "")
            self.assertEqual(len(body["data"]["shipments"]), 1)

    @patch("app.controllers.AdminAgentController.execute_query", return_value=None)
    def test_get_one_not_found_returns_404(self, mock_execute):
        """get_one returns 404 when no agent matches the given id."""
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminAgentController.get_one(999)
            self.assertEqual(status, 404)
            body = response.get_json()
            self.assertFalse(body["success"])
            self.assertEqual(body["message"], "Agent not found")


class TestCreate(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()

    def test_create_missing_name_returns_400(self):
        """create rejects payload missing name."""
        with self.app.test_request_context(
            method="POST", data='{"email": "a@b.com"}', content_type="application/json"
        ):
            session["admin_logged_in"] = True
            response, status = AdminAgentController.create()
            self.assertEqual(status, 400)
            body = response.get_json()
            self.assertEqual(body["message"], "Missing required field: name")

    def test_create_missing_email_returns_400(self):
        """create rejects payload missing email."""
        with self.app.test_request_context(
            method="POST", data='{"name": "Ram"}', content_type="application/json"
        ):
            session["admin_logged_in"] = True
            response, status = AdminAgentController.create()
            self.assertEqual(status, 400)
            body = response.get_json()
            self.assertEqual(body["message"], "Missing required field: email")

    @patch("app.controllers.AdminAgentController.execute_query")
    def test_create_duplicate_email_returns_400(self, mock_execute):
        """create rejects an email already registered to another user."""
        mock_execute.return_value = {"id": 5}
        with self.app.test_request_context(
            method="POST",
            data='{"name": "Ram", "email": "existing@test.com"}',
            content_type="application/json"
        ):
            session["admin_logged_in"] = True
            response, status = AdminAgentController.create()
            self.assertEqual(status, 400)
            body = response.get_json()
            self.assertEqual(body["message"], "Email already registered")

    @patch("app.controllers.AdminAgentController.execute_query")
    def test_create_success_returns_201_with_new_id(self, mock_execute):
        """Valid payload creates a new agent user and returns 201."""
        mock_execute.side_effect = [None, 55]
        with self.app.test_request_context(
            method="POST",
            data='{"name": "Ram Thapa", "email": "ram@test.com", "phone": "98000000"}',
            content_type="application/json"
        ):
            session["admin_logged_in"] = True
            response, status = AdminAgentController.create()
            self.assertEqual(status, 201)
            body = response.get_json()
            self.assertTrue(body["success"])
            self.assertEqual(body["data"]["id"], 55)
            self.assertEqual(body["message"], "Agent created successfully")


class TestUpdate(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()

    def test_update_no_fields_returns_400(self):
        """update rejects an empty payload with no updatable fields."""
        with self.app.test_request_context(
            method="PUT", data='{}', content_type="application/json"
        ):
            session["admin_logged_in"] = True
            response, status = AdminAgentController.update(40)
            self.assertEqual(status, 400)
            body = response.get_json()
            self.assertEqual(body["message"], "No fields to update")

    @patch("app.controllers.AdminAgentController.execute_query")
    def test_update_success_returns_200(self, mock_execute):
        """update accepts name, email, phone, and status fields."""
        mock_execute.return_value = 1
        with self.app.test_request_context(
            method="PUT",
            data='{"name": "Ram Updated", "phone": "9811111111", "status": "offline"}',
            content_type="application/json"
        ):
            session["admin_logged_in"] = True
            response, status = AdminAgentController.update(40)
            self.assertEqual(status, 200)
            body = response.get_json()
            self.assertTrue(body["success"])
            self.assertEqual(body["message"], "Agent updated successfully")

    @patch("app.controllers.AdminAgentController.execute_query", side_effect=Exception("DB Error"))
    def test_update_exception_returns_500(self, mock_execute):
        """Exception during update returns 500 with error message."""
        with self.app.test_request_context(
            method="PUT", data='{"name": "Ram"}', content_type="application/json"
        ):
            session["admin_logged_in"] = True
            response, status = AdminAgentController.update(40)
            self.assertEqual(status, 500)
            body = response.get_json()
            self.assertFalse(body["success"])


class TestUpdateStatus(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()

    def test_update_status_invalid_value_returns_400(self):
        """update_status rejects statuses outside active/inactive/offline."""
        with self.app.test_request_context(
            method="PATCH", data='{"status": "on_break"}', content_type="application/json"
        ):
            session["admin_logged_in"] = True
            response, status = AdminAgentController.update_status(40)
            self.assertEqual(status, 400)
            body = response.get_json()
            self.assertIn("Status must be", body["message"])

    @patch("app.controllers.AdminAgentController.execute_query", return_value=0)
    def test_update_status_not_found_returns_404(self, mock_execute):
        """update_status returns 404 when no rows are affected."""
        with self.app.test_request_context(
            method="PATCH", data='{"status": "offline"}', content_type="application/json"
        ):
            session["admin_logged_in"] = True
            response, status = AdminAgentController.update_status(999)
            self.assertEqual(status, 404)
            body = response.get_json()
            self.assertEqual(body["message"], "Agent not found")

    @patch("app.controllers.AdminAgentController.execute_query", return_value=1)
    def test_update_status_success_returns_200_for_each_valid_status(self, mock_execute):
        """update_status returns 200 with confirmation for active/inactive/offline."""
        for st in ("active", "inactive", "offline"):
            with self.app.test_request_context(
                method="PATCH", data=f'{{"status": "{st}"}}', content_type="application/json"
            ):
                session["admin_logged_in"] = True
                response, status = AdminAgentController.update_status(40)
                self.assertEqual(status, 200)
                body = response.get_json()
                self.assertEqual(body["message"], f"Status updated to '{st}'")


class TestDelete(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()

    @patch("app.controllers.AdminAgentController.execute_query")
    def test_delete_unassigns_shipments_before_deleting(self, mock_execute):
        """delete sets agent_id to NULL on shipments before removing the agent."""
        mock_execute.side_effect = [None, 1]
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminAgentController.delete(40)
            self.assertEqual(status, 200)
            first_call_sql = mock_execute.call_args_list[0][0][0]
            self.assertIn("UPDATE shipments SET agent_id = NULL", first_call_sql)

    @patch("app.controllers.AdminAgentController.execute_query")
    def test_delete_not_found_returns_404(self, mock_execute):
        """delete returns 404 when agent does not exist."""
        mock_execute.side_effect = [None, 0]
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminAgentController.delete(999)
            self.assertEqual(status, 404)
            body = response.get_json()
            self.assertEqual(body["message"], "Agent not found")

    @patch("app.controllers.AdminAgentController.execute_query")
    def test_delete_success_returns_200(self, mock_execute):
        """delete returns 200 with confirmation on successful removal."""
        mock_execute.side_effect = [None, 1]
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminAgentController.delete(40)
            self.assertEqual(status, 200)
            body = response.get_json()
            self.assertTrue(body["success"])
            self.assertEqual(body["message"], "Agent deleted successfully")


class TestGetStats(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()

    @patch("app.controllers.AdminAgentController.execute_query")
    def test_get_stats_success_returns_all_counts(self, mock_execute):
        """get_stats aggregates total, active, offline, inactive, new_this_month, total_deliveries."""
        mock_execute.side_effect = [
            {"cnt": 4}, {"cnt": 3}, {"cnt": 1},
            {"cnt": 0}, {"cnt": 1}, {"cnt": 20}
        ]
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminAgentController.get_stats()
            self.assertEqual(status, 200)
            body = response.get_json()
            self.assertTrue(body["success"])
            self.assertEqual(body["data"]["total"], 4)
            self.assertEqual(body["data"]["active"], 3)
            self.assertEqual(body["data"]["offline"], 1)
            self.assertEqual(body["data"]["inactive"], 0)
            self.assertEqual(body["data"]["new_this_month"], 1)
            self.assertEqual(body["data"]["total_deliveries"], 20)

    @patch("app.controllers.AdminAgentController.execute_query", side_effect=Exception("DB Error"))
    def test_get_stats_exception_returns_500(self, mock_execute):
        """Exception in get_stats returns 500 with error message."""
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminAgentController.get_stats()
            self.assertEqual(status, 500)
            body = response.get_json()
            self.assertFalse(body["success"])


if __name__ == "__main__":
    unittest.main()
    