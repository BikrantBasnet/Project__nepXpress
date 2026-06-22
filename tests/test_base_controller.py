import unittest
from flask import Flask, Blueprint, session, get_flashed_messages
from app.controllers.BaseController import BaseController, admin_required


def make_test_app():
    """Builds a minimal Flask app with real blueprints so url_for() resolves correctly."""
    app = Flask(__name__)
    app.secret_key = "test-secret"

    auth_bp = Blueprint("auth", __name__)
    auth_bp.route("/login", endpoint="login")(lambda: "login")
    app.register_blueprint(auth_bp, url_prefix="/auth")

    user_bp = Blueprint("user", __name__)
    user_bp.route("/dashboard", endpoint="dashboard")(lambda: "dashboard")
    app.register_blueprint(user_bp, url_prefix="/user")

    return app


class TestBaseController(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()
        self.controller = BaseController()

    # ── GET FORM DATA ─────────────────────────────────────────────────── #

    def test_get_form_data_strips_whitespace(self):
        """Ensures form parsing utilities extract and trim payload values cleanly."""
        with self.app.test_request_context(method="POST", data={
            "username": "  nepXpress_user  ", "city": "Kathmandu "
        }):
            username, city = self.controller.get_form_data("username", "city")
            self.assertEqual(username, "nepXpress_user")
            self.assertEqual(city, "Kathmandu")

    def test_get_form_data_missing_field_returns_empty_string(self):
        """Missing form fields return an empty string rather than raising an error."""
        with self.app.test_request_context(method="POST", data={}):
            (result,) = self.controller.get_form_data("nonexistent_field")
            self.assertEqual(result, "")

    # ── SESSION HELPERS ───────────────────────────────────────────────── #

    def test_is_logged_in_returns_true_when_session_has_user(self):
        """Validates is_logged_in returns True when user_id is in session."""
        with self.app.test_request_context():
            session["user_id"] = 505
            self.assertTrue(self.controller.is_logged_in())

    def test_is_logged_in_returns_false_when_no_session(self):
        """Validates is_logged_in returns False when session is empty."""
        with self.app.test_request_context():
            self.assertFalse(self.controller.is_logged_in())

    def test_get_current_user_id_returns_correct_id(self):
        """get_current_user_id reads the logged-in user's ID from session."""
        with self.app.test_request_context():
            session["user_id"] = 99
            self.assertEqual(self.controller.get_current_user_id(), 99)

    def test_get_current_user_id_returns_none_when_logged_out(self):
        """get_current_user_id returns None when no session exists."""
        with self.app.test_request_context():
            self.assertIsNone(self.controller.get_current_user_id())

    def test_get_current_role_returns_correct_role(self):
        """get_current_role reads the logged-in user's role from session."""
        with self.app.test_request_context():
            session["role"] = "agent"
            self.assertEqual(self.controller.get_current_role(), "agent")

    def test_get_current_role_returns_none_when_logged_out(self):
        """get_current_role returns None when no session exists."""
        with self.app.test_request_context():
            self.assertIsNone(self.controller.get_current_role())

    # ── FLASH AND REDIRECT ────────────────────────────────────────────── #

    def test_flash_and_redirect_flashes_message_and_redirects(self):
        """flash_and_redirect shows a flash message and returns a 302 to the endpoint."""
        with self.app.test_request_context():
            response = self.controller.flash_and_redirect("Welcome back!", "success", "auth.login")
            self.assertEqual(response.status_code, 302)
            self.assertIn("/auth/login", response.location)
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("success", "Welcome back!"), flashes)

    def test_flash_and_redirect_works_with_danger_category(self):
        """flash_and_redirect correctly passes danger category to flash."""
        with self.app.test_request_context():
            response = self.controller.flash_and_redirect("Access denied.", "danger", "auth.login")
            self.assertEqual(response.status_code, 302)
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("danger", "Access denied."), flashes)

    # ── JSON RESPONSE HELPERS ─────────────────────────────────────────── #

    def test_success_returns_200_with_correct_structure(self):
        """success() builds a JSON 200 response with success flag and data."""
        with self.app.test_request_context():
            response, status = BaseController.success(data={"key": "value"}, message="OK")
            self.assertEqual(status, 200)
            body = response.get_json()
            self.assertTrue(body["success"])
            self.assertEqual(body["message"], "OK")
            self.assertEqual(body["data"], {"key": "value"})

    def test_success_without_data_omits_data_key(self):
        """success() called without data should not include a data key in the response."""
        with self.app.test_request_context():
            response, status = BaseController.success(message="Done")
            body = response.get_json()
            self.assertTrue(body["success"])
            self.assertNotIn("data", body)

    def test_success_custom_status_code(self):
        """success() respects a custom status_code like 201."""
        with self.app.test_request_context():
            response, status = BaseController.success(message="Created", status_code=201)
            self.assertEqual(status, 201)

    def test_error_returns_400_with_failure_flag(self):
        """error() builds a JSON 400 response with success=False."""
        with self.app.test_request_context():
            response, status = BaseController.error("Something went wrong", 400)
            self.assertEqual(status, 400)
            body = response.get_json()
            self.assertFalse(body["success"])
            self.assertEqual(body["message"], "Something went wrong")

    def test_error_returns_500_for_server_errors(self):
        """error() correctly passes a 500 status code for server-side failures."""
        with self.app.test_request_context():
            response, status = BaseController.error("Internal server error", 500)
            self.assertEqual(status, 500)
            body = response.get_json()
            self.assertFalse(body["success"])

    def test_not_found_returns_404_with_failure_flag(self):
        """not_found() builds a JSON 404 response with success=False."""
        with self.app.test_request_context():
            response, status = BaseController.not_found("Resource not found")
            self.assertEqual(status, 404)
            body = response.get_json()
            self.assertFalse(body["success"])
            self.assertEqual(body["message"], "Resource not found")

    def test_not_found_uses_default_message(self):
        """not_found() falls back to a default message when none is provided."""
        with self.app.test_request_context():
            response, status = BaseController.not_found()
            body = response.get_json()
            self.assertEqual(body["message"], "Resource not found")


# ── ADMIN REQUIRED DECORATOR ──────────────────────────────────────────────── #

class TestAdminRequired(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()

        # Register a dummy protected route using the decorator
        @self.app.route("/admin/test")
        @admin_required
        def protected():
            return "admin only", 200

        self.client = self.app.test_client()

    def test_admin_required_blocks_unauthenticated_request(self):
        """Unauthenticated requests to admin routes receive a 401 JSON response."""
        response = self.client.get("/admin/test")
        self.assertEqual(response.status_code, 401)
        body = response.get_json()
        self.assertFalse(body["success"])
        self.assertIn("Unauthorized", body["message"])

    def test_admin_required_allows_api_admin_session(self):
        """Requests with admin_logged_in in session are allowed through."""
        with self.client.session_transaction() as sess:
            sess["admin_logged_in"] = True
        response = self.client.get("/admin/test")
        self.assertEqual(response.status_code, 200)

    def test_admin_required_allows_form_admin_session(self):
        """Requests with user_id + user_role=admin in session are allowed through."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["user_role"] = "admin"
        response = self.client.get("/admin/test")
        self.assertEqual(response.status_code, 200)

    def test_admin_required_blocks_non_admin_role(self):
        """Logged-in users with a non-admin role are still blocked."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 5
            sess["user_role"] = "customer"
        response = self.client.get("/admin/test")
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()