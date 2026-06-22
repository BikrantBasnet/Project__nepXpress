import unittest
from flask import Flask, Blueprint
from app.auth import login_required, no_cache
from app.controllers.BaseController import admin_required


class TestLoginRequired(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.secret_key = "test-secret"

        bp = Blueprint("auth", __name__)

        @bp.route("/login")
        def login():
            return "this is the login page"

        @bp.route("/dashboard")
        @login_required
        def dashboard():
            return "welcome to dashboard"

        self.app.register_blueprint(bp)
        self.client = self.app.test_client()

    def test_locked_page_redirects_a_guest(self):
        """A NOT-logged-in user visiting /dashboard is redirected to /login."""
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.location)

    def test_locked_page_opens_for_logged_in_user(self):
        """A logged-in user CAN access /dashboard."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.decode(), "welcome to dashboard")

    def test_login_page_is_public(self):
        """Anyone can open the login page without being logged in."""
        response = self.client.get("/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn("this is the login page", response.data.decode())

    def test_locked_page_flashes_message_to_guest(self):
        """A guest redirected from a protected page sees a flash message."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess.clear()
            c.get("/dashboard")
            with c.session_transaction() as sess:
                flashes = sess.get("_flashes", [])
            self.assertTrue(any("login" in msg.lower() for _, msg in flashes))


class TestAdminRequired(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.secret_key = "test-secret"

        bp = Blueprint("admin", __name__)

        @bp.route("/public")
        def public():
            return "this is a public page"

        @bp.route("/admin-only")
        @admin_required
        def admin_only():
            return "welcome admin"

        self.app.register_blueprint(bp)
        self.client = self.app.test_client()

    def test_admin_page_blocks_guest_with_401(self):
        """A NOT-logged-in user visiting an admin page gets 401."""
        response = self.client.get("/admin-only")
        self.assertEqual(response.status_code, 401)

    def test_admin_page_opens_for_api_admin_session(self):
        """A user with admin_logged_in in session CAN access the admin page."""
        with self.client.session_transaction() as sess:
            sess["admin_logged_in"] = True
        response = self.client.get("/admin-only")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.decode(), "welcome admin")

    def test_admin_page_opens_for_form_admin_session(self):
        """A user with user_id and user_role=admin CAN access the admin page."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["user_role"] = "admin"
        response = self.client.get("/admin-only")
        self.assertEqual(response.status_code, 200)

    def test_admin_page_blocks_non_admin_role(self):
        """A regular logged-in customer is blocked from admin pages."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 5
            sess["user_role"] = "customer"
        response = self.client.get("/admin-only")
        self.assertEqual(response.status_code, 401)

    def test_public_page_is_accessible_to_everyone(self):
        """Anyone can open a public page."""
        response = self.client.get("/public")
        self.assertEqual(response.status_code, 200)
        self.assertIn("this is a public page", response.data.decode())


class TestNoCache(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.secret_key = "test-secret"

        bp = Blueprint("main", __name__)

        @bp.route("/sensitive")
        @no_cache
        def sensitive():
            return "sensitive page"

        self.app.register_blueprint(bp)
        self.client = self.app.test_client()

    def test_no_cache_sets_cache_control_header(self):
        """no_cache decorator sets Cache-Control to no-store."""
        response = self.client.get("/sensitive")
        self.assertIn("no-store", response.headers.get("Cache-Control", ""))

    def test_no_cache_sets_pragma_header(self):
        """no_cache decorator sets Pragma: no-cache."""
        response = self.client.get("/sensitive")
        self.assertEqual(response.headers.get("Pragma"), "no-cache")

    def test_no_cache_sets_expires_header(self):
        """no_cache decorator sets Expires to 0."""
        response = self.client.get("/sensitive")
        self.assertEqual(response.headers.get("Expires"), "0")

    def test_no_cache_page_still_returns_200(self):
        """no_cache decorator does not break the response."""
        response = self.client.get("/sensitive")
        self.assertEqual(response.status_code, 200)
        self.assertIn("sensitive page", response.data.decode())


if __name__ == "__main__":
    unittest.main()