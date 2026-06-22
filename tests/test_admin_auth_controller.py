import unittest
from unittest.mock import patch
from flask import Flask, session
from app.controllers.AdminAuthController import AdminAuthController


def make_test_app():
    """Builds a minimal Flask app for session/request context."""
    app = Flask(__name__)
    app.secret_key = "test-secret"
    return app


class TestLogin(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()

    def test_login_missing_email_returns_400(self):
        """login rejects payload missing email."""
        with self.app.test_request_context(
            method="POST", data='{"password": "pass123"}', content_type="application/json"
        ):
            response, status = AdminAuthController.login()
            self.assertEqual(status, 400)
            body = response.get_json()
            self.assertFalse(body["success"])
            self.assertEqual(body["message"], "Email and password are required")

    def test_login_missing_password_returns_400(self):
        """login rejects payload missing password."""
        with self.app.test_request_context(
            method="POST", data='{"email": "admin@test.com"}', content_type="application/json"
        ):
            response, status = AdminAuthController.login()
            self.assertEqual(status, 400)
            body = response.get_json()
            self.assertEqual(body["message"], "Email and password are required")

    @patch("app.controllers.AdminAuthController.User.admin_verify_login", return_value=None)
    def test_login_invalid_credentials_returns_401(self, mock_verify):
        """login rejects wrong credentials or non-admin accounts."""
        with self.app.test_request_context(
            method="POST",
            data='{"email": "ghost@test.com", "password": "wrongpass"}',
            content_type="application/json"
        ):
            response, status = AdminAuthController.login()
            self.assertEqual(status, 401)
            body = response.get_json()
            self.assertFalse(body["success"])
            self.assertEqual(body["message"], "Invalid credentials or not an admin account")

    @patch("app.controllers.AdminAuthController.User.admin_verify_login")
    def test_login_success_sets_admin_session_keys(self, mock_verify):
        """Valid admin credentials set all four admin_* session keys."""
        mock_verify.return_value = {
            "id": 1, "name": "Admin", "email": "admin@test.com", "role": "admin"
        }
        with self.app.test_request_context(
            method="POST",
            data='{"email": "admin@test.com", "password": "correctpass"}',
            content_type="application/json"
        ):
            response, status = AdminAuthController.login()
            self.assertEqual(status, 200)
            self.assertTrue(session["admin_logged_in"])
            self.assertEqual(session["admin_id"], 1)
            self.assertEqual(session["admin_name"], "Admin")
            self.assertEqual(session["admin_role"], "admin")
            self.assertTrue(session.permanent)

    @patch("app.controllers.AdminAuthController.User.admin_verify_login")
    def test_login_success_returns_admin_data_in_response(self, mock_verify):
        """Successful login returns id, name, email, and role in the response body."""
        mock_verify.return_value = {
            "id": 2, "name": "Super Admin", "email": "super@test.com", "role": "superadmin"
        }
        with self.app.test_request_context(
            method="POST",
            data='{"email": "super@test.com", "password": "correctpass"}',
            content_type="application/json"
        ):
            response, status = AdminAuthController.login()
            body = response.get_json()
            self.assertTrue(body["success"])
            self.assertEqual(body["data"]["id"], 2)
            self.assertEqual(body["data"]["name"], "Super Admin")
            self.assertEqual(body["data"]["email"], "super@test.com")
            self.assertEqual(body["data"]["role"], "superadmin")
            self.assertEqual(body["message"], "Admin login successful")

    @patch("app.controllers.AdminAuthController.User.admin_verify_login")
    def test_login_strips_whitespace_from_email_and_password(self, mock_verify):
        """login trims surrounding whitespace before verifying credentials."""
        mock_verify.return_value = {
            "id": 1, "name": "Admin", "email": "admin@test.com", "role": "admin"
        }
        with self.app.test_request_context(
            method="POST",
            data='{"email": "  admin@test.com  ", "password": "  pass123  "}',
            content_type="application/json"
        ):
            AdminAuthController.login()
            mock_verify.assert_called_once_with("admin@test.com", "pass123")


class TestLogout(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()

    def test_logout_clears_all_admin_session_keys(self):
        """logout removes admin_logged_in, admin_id, admin_name, and admin_role."""
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            session["admin_id"]        = 1
            session["admin_name"]      = "Admin"
            session["admin_role"]      = "admin"

            response, status = AdminAuthController.logout()

            self.assertEqual(status, 200)
            self.assertNotIn("admin_logged_in", session)
            self.assertNotIn("admin_id", session)
            self.assertNotIn("admin_name", session)
            self.assertNotIn("admin_role", session)

    def test_logout_does_not_touch_teammate_session_keys(self):
        """logout leaves user_id/user_name/user_role untouched (separate namespaces)."""
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            session["user_id"]   = 99
            session["user_name"] = "Customer Bob"
            session["user_role"] = "customer"

            AdminAuthController.logout()

            self.assertEqual(session["user_id"], 99)
            self.assertEqual(session["user_name"], "Customer Bob")
            self.assertEqual(session["user_role"], "customer")

    def test_logout_success_returns_200(self):
        """logout returns 200 with a confirmation message even with no active session."""
        with self.app.test_request_context():
            response, status = AdminAuthController.logout()
            self.assertEqual(status, 200)
            body = response.get_json()
            self.assertTrue(body["success"])
            self.assertEqual(body["message"], "Logged out successfully")


class TestMe(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()

    def test_me_unauthenticated_returns_401(self):
        """me() rejects requests with no active admin session."""
        with self.app.test_request_context():
            response, status = AdminAuthController.me()
            self.assertEqual(status, 401)
            body = response.get_json()
            self.assertFalse(body["success"])
            self.assertEqual(body["message"], "Not authenticated")

    def test_me_authenticated_returns_session_info(self):
        """me() returns id, name, and role from the active admin session."""
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            session["admin_id"]        = 5
            session["admin_name"]      = "Ops Admin"
            session["admin_role"]      = "admin"

            response, status = AdminAuthController.me()

            self.assertEqual(status, 200)
            body = response.get_json()
            self.assertTrue(body["success"])
            self.assertEqual(body["data"]["id"], 5)
            self.assertEqual(body["data"]["name"], "Ops Admin")
            self.assertEqual(body["data"]["role"], "admin")

    def test_me_does_not_leak_other_session_keys(self):
        """me() only returns id, name, and role - no email or password fields."""
        with self.app.test_request_context():
            session["admin_logged_in"] = True
            session["admin_id"]        = 5
            session["admin_name"]      = "Ops Admin"
            session["admin_role"]      = "admin"

            response, status = AdminAuthController.me()
            body = response.get_json()
            self.assertNotIn("email", body["data"])
            self.assertNotIn("password", body["data"])


if __name__ == "__main__":
    unittest.main()