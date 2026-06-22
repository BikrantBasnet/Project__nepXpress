import unittest
from unittest.mock import patch
from flask import Flask, Blueprint, session
from app.controllers.AdminUserController import AdminUserController


def make_test_app():
    """Builds a minimal Flask app with real blueprints so url_for() resolves correctly."""
    app = Flask(__name__)
    app.secret_key = "test-secret"
    bp = Blueprint("admin", __name__)
    bp.route("/users", endpoint="users")(lambda: "users")
    app.register_blueprint(bp, url_prefix="/admin")
    return app


class TestGetAll(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()

    @patch("app.controllers.AdminUserController.execute_query")
    def test_get_all_success_returns_paginated_data(self, mock_execute):
        """get_all returns paginated user data with correct structure."""
        mock_execute.side_effect = [
            {"cnt": 1},
            [{"id": 1, "name": "Samyog", "email": "samyog@test.com",
              "role": "customer", "status": "active", "created_at": "2026-06-20"}]
        ]
        with self.app.test_request_context("/?page=2&limit=10&role=customer&status=active&search=sam"):
            session["admin_logged_in"] = True
            response, status = AdminUserController.get_all()
            self.assertEqual(status, 200)
            body = response.get_json()
            self.assertTrue(body["success"])
            self.assertEqual(len(body["data"]["users"]), 1)
            self.assertEqual(body["data"]["pagination"]["page"], 2)
            self.assertEqual(body["data"]["pagination"]["limit"], 10)
            self.assertEqual(body["data"]["pagination"]["total"], 1)
            self.assertEqual(body["data"]["pagination"]["total_pages"], 1)

    @patch("app.controllers.AdminUserController.execute_query")
    def test_get_all_uses_default_pagination_when_no_params(self, mock_execute):
        """get_all falls back to page=1 and limit=10 when no query params are given."""
        mock_execute.side_effect = [{"cnt": 0}, []]
        with self.app.test_request_context("/"):
            session["admin_logged_in"] = True
            response, status = AdminUserController.get_all()
            body = response.get_json()
            self.assertEqual(body["data"]["pagination"]["page"], 1)
            self.assertEqual(body["data"]["pagination"]["limit"], 10)

    @patch("app.controllers.AdminUserController.execute_query")
    def test_get_all_formats_created_at_as_string(self, mock_execute):
        """get_all converts datetime created_at fields to strings."""
        mock_execute.side_effect = [
            {"cnt": 1},
            [{"id": 1, "name": "A", "created_at": "2026-06-20 10:00:00"}]
        ]
        with self.app.test_request_context("/"):
            session["admin_logged_in"] = True
            response, status = AdminUserController.get_all()
            body = response.get_json()
            self.assertEqual(body["data"]["users"][0]["created_at"], "2026-06-20 10:00:00")

    @patch("app.controllers.AdminUserController.execute_query", side_effect=Exception("DB Error"))
    def test_get_all_exception_returns_500_error(self, mock_execute):
        """Exception in get_all returns 500 with error message."""
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminUserController.get_all()
            self.assertEqual(status, 500)
            body = response.get_json()
            self.assertFalse(body["success"])
            self.assertEqual(body["message"], "DB Error")

    def test_get_all_blocked_without_admin_session(self):
        """Unauthenticated requests to get_all receive a 401 JSON response."""
        with self.app.test_request_context("/"):
            response, status = AdminUserController.get_all()
            self.assertEqual(status, 401)
            body = response.get_json()
            self.assertFalse(body["success"])


class TestGetOne(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()

    @patch("app.controllers.AdminUserController.execute_query")
    def test_get_one_success_returns_user_stats_and_shipments(self, mock_execute):
        """get_one retrieves user, shipment stats, and recent shipments."""
        mock_execute.side_effect = [
            {"id": 1, "name": "Samyog", "email": "samyog@test.com",
             "role": "customer", "status": "active", "created_at": "2026-06-20"},
            {"total": 3, "delivered": 1, "pending": 0, "in_transit": 1,
             "delayed": 1, "total_spent": 4500},
            [{"tracking_id": "NX-1", "destination": "Pokhara",
              "status": "delivered", "amount": 1500, "created_at": "2026-06-20"}]
        ]
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminUserController.get_one(1)
            self.assertEqual(status, 200)
            body = response.get_json()
            self.assertTrue(body["success"])
            self.assertEqual(body["data"]["user"]["id"], 1)
            self.assertEqual(body["data"]["stats"]["total"], 3)
            self.assertEqual(len(body["data"]["shipments"]), 1)

    @patch("app.controllers.AdminUserController.execute_query", return_value=None)
    def test_get_one_not_found_returns_404(self, mock_execute):
        """get_one returns 404 when no user matches the given id."""
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminUserController.get_one(999)
            self.assertEqual(status, 404)
            body = response.get_json()
            self.assertFalse(body["success"])
            self.assertEqual(body["message"], "User not found")


class TestUpdateStatus(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()

    def test_update_status_invalid_value_returns_400(self):
        """update_status rejects statuses not in the allowed set."""
        with self.app.test_request_context(
            method="PATCH", data='{"status": "banned"}', content_type="application/json"
        ):
            session["admin_logged_in"] = True
            response, status = AdminUserController.update_status(2)
            self.assertEqual(status, 400)
            body = response.get_json()
            self.assertFalse(body["success"])
            self.assertIn("Status must be", body["message"])

    def test_update_status_blocks_deactivating_own_account_via_admin_id(self):
        """update_status refuses to let an admin deactivate their own session admin_id."""
        with self.app.test_request_context(
            method="PATCH", data='{"status": "inactive"}', content_type="application/json"
        ):
            session["admin_logged_in"] = True
            session["admin_id"] = 7
            response, status = AdminUserController.update_status(7)
            self.assertEqual(status, 400)
            body = response.get_json()
            self.assertIn("cannot deactivate your own account", body["message"])

    def test_update_status_blocks_deactivating_own_account_via_user_id(self):
        """update_status refuses to let an admin deactivate their own session user_id."""
        with self.app.test_request_context(
            method="PATCH", data='{"status": "inactive"}', content_type="application/json"
        ):
            session["admin_logged_in"] = True
            session["user_id"] = 3
            response, status = AdminUserController.update_status(3)
            self.assertEqual(status, 400)
            body = response.get_json()
            self.assertIn("cannot deactivate your own account", body["message"])

    @patch("app.controllers.AdminUserController.execute_query", return_value=0)
    def test_update_status_not_found_returns_404(self, mock_execute):
        """update_status returns 404 when no rows are affected."""
        with self.app.test_request_context(
            method="PATCH", data='{"status": "active"}', content_type="application/json"
        ):
            session["admin_logged_in"] = True
            response, status = AdminUserController.update_status(999)
            self.assertEqual(status, 404)
            body = response.get_json()
            self.assertEqual(body["message"], "User not found")

    @patch("app.controllers.AdminUserController.execute_query", return_value=1)
    def test_update_status_success_returns_200(self, mock_execute):
        """update_status returns 200 with confirmation message."""
        with self.app.test_request_context(
            method="PATCH", data='{"status": "active"}', content_type="application/json"
        ):
            session["admin_logged_in"] = True
            response, status = AdminUserController.update_status(2)
            self.assertEqual(status, 200)
            body = response.get_json()
            self.assertTrue(body["success"])
            self.assertEqual(body["message"], "User status updated to 'active'")


class TestUpdateRole(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()

    def test_update_role_invalid_value_returns_400(self):
        """update_role rejects roles outside customer/admin/agent."""
        with self.app.test_request_context(
            method="PATCH", data='{"role": "superuser"}', content_type="application/json"
        ):
            session["admin_logged_in"] = True
            response, status = AdminUserController.update_role(2)
            self.assertEqual(status, 400)
            body = response.get_json()
            self.assertIn("Role must be", body["message"])

    def test_update_role_blocks_changing_own_role(self):
        """update_role refuses to let an admin change their own session role."""
        with self.app.test_request_context(
            method="PATCH", data='{"role": "customer"}', content_type="application/json"
        ):
            session["admin_logged_in"] = True
            session["admin_id"] = 7
            response, status = AdminUserController.update_role(7)
            self.assertEqual(status, 400)
            body = response.get_json()
            self.assertIn("cannot change your own role", body["message"])

    @patch("app.controllers.AdminUserController.execute_query", return_value=0)
    def test_update_role_not_found_returns_404(self, mock_execute):
        """update_role returns 404 when no rows are affected."""
        with self.app.test_request_context(
            method="PATCH", data='{"role": "agent"}', content_type="application/json"
        ):
            session["admin_logged_in"] = True
            response, status = AdminUserController.update_role(999)
            self.assertEqual(status, 404)
            body = response.get_json()
            self.assertEqual(body["message"], "User not found")

    @patch("app.controllers.AdminUserController.execute_query", return_value=1)
    def test_update_role_success_returns_200(self, mock_execute):
        """update_role returns 200 with confirmation message for each valid role."""
        for role in ("customer", "admin", "agent"):
            with self.app.test_request_context(
                method="PATCH", data=f'{{"role": "{role}"}}', content_type="application/json"
            ):
                session["admin_logged_in"] = True
                response, status = AdminUserController.update_role(2)
                self.assertEqual(status, 200)
                body = response.get_json()
                self.assertEqual(body["message"], f"User role updated to '{role}'")


class TestDelete(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()

    def test_delete_blocks_deleting_own_account(self):
        """delete refuses to let an admin delete their own session account."""
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            session["admin_id"] = 7
            response, status = AdminUserController.delete(7)
            self.assertEqual(status, 400)
            body = response.get_json()
            self.assertIn("cannot delete your own account", body["message"])

    @patch("app.controllers.AdminUserController.execute_query", return_value=0)
    def test_delete_not_found_returns_404(self, mock_execute):
        """delete returns 404 when user does not exist."""
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminUserController.delete(999)
            self.assertEqual(status, 404)
            body = response.get_json()
            self.assertEqual(body["message"], "User not found")

    @patch("app.controllers.AdminUserController.execute_query", return_value=1)
    def test_delete_success_returns_200(self, mock_execute):
        """delete returns 200 with confirmation on successful removal."""
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminUserController.delete(2)
            self.assertEqual(status, 200)
            body = response.get_json()
            self.assertTrue(body["success"])
            self.assertEqual(body["message"], "User deleted successfully")


class TestGetStats(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()

    @patch("app.controllers.AdminUserController.execute_query")
    def test_get_stats_success_returns_all_counts(self, mock_execute):
        """get_stats aggregates total, active, inactive, admins, customers, new_this_month."""
        mock_execute.side_effect = [
            {"cnt": 39}, {"cnt": 35}, {"cnt": 4},
            {"cnt": 3}, {"cnt": 30}, {"cnt": 5}
        ]
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminUserController.get_stats()
            self.assertEqual(status, 200)
            body = response.get_json()
            self.assertTrue(body["success"])
            self.assertEqual(body["data"]["total"], 39)
            self.assertEqual(body["data"]["active"], 35)
            self.assertEqual(body["data"]["inactive"], 4)
            self.assertEqual(body["data"]["admins"], 3)
            self.assertEqual(body["data"]["customers"], 30)
            self.assertEqual(body["data"]["new_this_month"], 5)

    @patch("app.controllers.AdminUserController.execute_query", side_effect=Exception("DB Error"))
    def test_get_stats_exception_returns_500(self, mock_execute):
        """Exception in get_stats returns 500 with error message."""
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            response, status = AdminUserController.get_stats()
            self.assertEqual(status, 500)
            body = response.get_json()
            self.assertFalse(body["success"])


if __name__ == "__main__":
    unittest.main()