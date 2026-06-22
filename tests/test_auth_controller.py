import unittest
from unittest.mock import patch, MagicMock
from flask import Flask, Blueprint, session, get_flashed_messages
from app.controllers.authcontrollers import AuthController


def make_test_app():
    app = Flask(__name__)
    app.secret_key = "test-secret"

    auth_bp = Blueprint("auth", __name__)
    auth_bp.route("/login",           endpoint="login"          )(lambda: "login")
    auth_bp.route("/register",        endpoint="register"       )(lambda: "register")
    auth_bp.route("/forgot-password", endpoint="forgot_password")(lambda: "forgot_password")
    auth_bp.route("/settings",        endpoint="settings"       )(lambda: "settings")
    app.register_blueprint(auth_bp, url_prefix="/auth")

    user_bp = Blueprint("user", __name__)
    user_bp.route("/dashboard", endpoint="dashboard")(lambda: "dashboard")
    app.register_blueprint(user_bp, url_prefix="/user")

    agent_bp = Blueprint("agent", __name__)
    agent_bp.route("/dashboard", endpoint="dashboard")(lambda: "agent_dashboard")
    app.register_blueprint(agent_bp, url_prefix="/agent")

    @app.route("/admin/dashboard", endpoint="admin_dashboard")
    def admin_dashboard():
        return "admin dashboard"

    return app


# ── LOGIN ─────────────────────────────────────────────────────────────────── #

class TestLogin(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()
        self.controller = AuthController()

    @patch("app.controllers.authcontrollers.render_template", return_value="login_page")
    def test_login_get_shows_form(self, mock_render):
        """Visiting login with GET shows the login form."""
        with self.app.test_request_context(method="GET"):
            result = self.controller.login()
            self.assertEqual(result, "login_page")
            mock_render.assert_called_once_with("login.html")

    def test_login_already_logged_in_as_customer_redirects_to_dashboard(self):
        """Customer already in session is sent to user dashboard."""
        with self.app.test_request_context():
            session["user_id"] = 1
            session["user_role"] = "customer"
            response = self.controller.login()
            self.assertEqual(response.status_code, 302)
            self.assertIn("/user/dashboard", response.location)

    def test_login_already_logged_in_as_agent_redirects_to_agent_dashboard(self):
        """Agent already in session is sent to agent dashboard."""
        with self.app.test_request_context():
            session["user_id"] = 2
            session["user_role"] = "agent"
            response = self.controller.login()
            self.assertEqual(response.status_code, 302)
            self.assertIn("/agent/dashboard", response.location)

    def test_login_already_logged_in_as_admin_redirects_to_admin_dashboard(self):
        """Admin already in session is sent to admin dashboard."""
        with self.app.test_request_context():
            session["user_id"] = 3
            session["user_role"] = "admin"
            response = self.controller.login()
            self.assertEqual(response.status_code, 302)
            self.assertIn("/admin/dashboard", response.location)

    @patch("app.controllers.authcontrollers.render_template", return_value="login_page")
    def test_login_missing_fields_flashes_danger(self, mock_render):
        """Blank email and password are rejected immediately."""
        with self.app.test_request_context(method="POST", data={"email": "", "password": ""}):
            self.controller.login()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("danger", "Email and password are required."), flashes)

    @patch("app.controllers.authcontrollers.render_template", return_value="login_page")
    @patch("app.controllers.authcontrollers.User")
    def test_login_email_not_found_flashes_danger(self, mock_user_class, mock_render):
        """Unknown email shows a not-found error and stays on login."""
        mock_instance = MagicMock()
        mock_user_class.return_value = mock_instance
        mock_instance.find_by.return_value = None
        with self.app.test_request_context(method="POST", data={"email": "ghost@test.com", "password": "pass123"}):
            self.controller.login()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("danger", "Email not found. Please register."), flashes)

    @patch("app.controllers.authcontrollers.render_template", return_value="login_page")
    @patch("app.controllers.authcontrollers.User")
    def test_login_wrong_password_flashes_danger(self, mock_user_class, mock_render):
        """Correct email but wrong password is refused."""
        mock_instance = MagicMock()
        mock_user_class.return_value = mock_instance
        mock_instance.find_by.return_value = {
            "id": 1, "name": "Bob", "email": "bob@test.com",
            "role": "customer", "password": "hashed"
        }
        mock_instance.check_password.return_value = False
        with self.app.test_request_context(method="POST", data={"email": "bob@test.com", "password": "wrongpass"}):
            self.controller.login()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("danger", "Incorrect password. Please try again."), flashes)
            self.assertNotIn("user_id", session)

    @patch("app.controllers.authcontrollers.User")
    def test_login_successful_customer_sets_session_and_redirects(self, mock_user_class):
        """Valid customer credentials set session and redirect to user dashboard."""
        mock_instance = MagicMock()
        mock_user_class.return_value = mock_instance
        mock_instance.find_by.return_value = {
            "id": 42, "name": "Test User", "email": "user@test.com", "role": "customer"
        }
        mock_instance.check_password.return_value = True
        with self.app.test_request_context(method="POST", data={"email": "user@test.com", "password": "password123"}):
            response = self.controller.login()
            self.assertEqual(session["user_id"], 42)
            self.assertEqual(session["user_name"], "Test User")
            self.assertEqual(session["user_role"], "customer")
            self.assertEqual(response.status_code, 302)
            self.assertIn("/user/dashboard", response.location)
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("success", "Welcome, Test User!"), flashes)

    @patch("app.controllers.authcontrollers.User")
    def test_login_successful_agent_redirects_to_agent_dashboard(self, mock_user_class):
        """Valid agent credentials redirect to agent dashboard."""
        mock_instance = MagicMock()
        mock_user_class.return_value = mock_instance
        mock_instance.find_by.return_value = {
            "id": 7, "name": "Agent Ram", "email": "agent@test.com", "role": "agent"
        }
        mock_instance.check_password.return_value = True
        with self.app.test_request_context(method="POST", data={"email": "agent@test.com", "password": "pass123"}):
            response = self.controller.login()
            self.assertEqual(response.status_code, 302)
            self.assertIn("/agent/dashboard", response.location)

    @patch("app.controllers.authcontrollers.User")
    def test_login_successful_admin_redirects_to_admin_dashboard(self, mock_user_class):
        """Valid admin credentials redirect to admin dashboard."""
        mock_instance = MagicMock()
        mock_user_class.return_value = mock_instance
        mock_instance.find_by.return_value = {
            "id": 1, "name": "Admin", "email": "admin@test.com", "role": "admin"
        }
        mock_instance.check_password.return_value = True
        with self.app.test_request_context(method="POST", data={"email": "admin@test.com", "password": "pass123"}):
            response = self.controller.login()
            self.assertEqual(response.status_code, 302)
            self.assertIn("/admin/dashboard", response.location)


# ── REGISTER ──────────────────────────────────────────────────────────────── #

class TestRegister(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()
        self.controller = AuthController()

    @patch("app.controllers.authcontrollers.render_template", return_value="register_page")
    def test_register_get_shows_form(self, mock_render):
        """GET request shows the register form."""
        with self.app.test_request_context(method="GET"):
            result = self.controller.register()
            self.assertEqual(result, "register_page")
            mock_render.assert_called_once_with("register.html")

    def test_register_already_logged_in_redirects_to_dashboard(self):
        """User already in session is redirected away from register."""
        with self.app.test_request_context():
            session["user_id"] = 1
            response = self.controller.register()
            self.assertEqual(response.status_code, 302)
            self.assertIn("/user/dashboard", response.location)

    @patch("app.controllers.authcontrollers.render_template", return_value="register_page")
    def test_register_missing_fields_flashes_danger(self, mock_render):
        """Any empty required field blocks registration."""
        with self.app.test_request_context(method="POST", data={
            "fullName": "", "email": "", "password": "", "confirmPassword": "", "security_answer": ""
        }):
            self.controller.register()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("danger", "All fields are required."), flashes)

    @patch("app.controllers.authcontrollers.render_template", return_value="register_page")
    def test_register_mismatched_passwords_fails(self, mock_render):
        """Mismatched passwords are rejected before DB lookup."""
        with self.app.test_request_context(method="POST", data={
            "fullName": "Alice", "email": "alice@test.com",
            "password": "pass123", "confirmPassword": "different",
            "security_answer": "blue"
        }):
            self.controller.register()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("danger", "Passwords do not match."), flashes)

    @patch("app.controllers.authcontrollers.render_template", return_value="register_page")
    def test_register_short_password_flashes_danger(self, mock_render):
        """Passwords under 6 characters are rejected."""
        with self.app.test_request_context(method="POST", data={
            "fullName": "Alice", "email": "alice@test.com",
            "password": "123", "confirmPassword": "123",
            "security_answer": "blue"
        }):
            self.controller.register()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("danger", "Password must be at least 6 characters."), flashes)

    @patch("app.controllers.authcontrollers.render_template", return_value="register_page")
    def test_register_name_too_long_flashes_danger(self, mock_render):
        """Names over 100 characters are rejected."""
        with self.app.test_request_context(method="POST", data={
            "fullName": "A" * 101, "email": "alice@test.com",
            "password": "pass123", "confirmPassword": "pass123",
            "security_answer": "blue"
        }):
            self.controller.register()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("danger", "Name must be under 100 characters."), flashes)

    @patch("app.controllers.authcontrollers.render_template", return_value="register_page")
    @patch("app.controllers.authcontrollers.User")
    def test_register_email_already_exists(self, mock_user_class, mock_render):
        """Duplicate email is rejected before saving."""
        mock_instance = MagicMock()
        mock_user_class.return_value = mock_instance
        mock_instance.email_exists.return_value = True
        with self.app.test_request_context(method="POST", data={
            "fullName": "Alice", "email": "a@b.com",
            "password": "password123", "confirmPassword": "password123",
            "security_answer": "blue"
        }):
            self.controller.register()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("danger", "Email already registered. Please login or use a different email."), flashes)

    @patch("app.controllers.authcontrollers.User")
    def test_register_success_saves_user_and_redirects(self, mock_user_class):
        """Valid new user is saved and redirected to login."""
        mock_instance = MagicMock()
        mock_user_class.return_value = mock_instance
        mock_instance.email_exists.return_value = False
        with self.app.test_request_context(method="POST", data={
            "fullName": "Alice", "email": "alice@test.com",
            "password": "secret123", "confirmPassword": "secret123",
            "security_answer": "blue"
        }):
            response = self.controller.register()
            mock_instance.save.assert_called_once()
            self.assertEqual(response.status_code, 302)
            self.assertIn("/auth/login", response.location)
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("success", "Registration successful! Please login with your credentials."), flashes)

    @patch("app.controllers.authcontrollers.render_template", return_value="register_page")
    @patch("app.controllers.authcontrollers.User")
    def test_register_save_exception_flashes_danger(self, mock_user_class, mock_render):
        """DB exception during save shows a danger flash and re-renders form."""
        mock_instance = MagicMock()
        mock_user_class.return_value = mock_instance
        mock_instance.email_exists.return_value = False
        mock_instance.save.side_effect = Exception("DB connection failed")
        with self.app.test_request_context(method="POST", data={
            "fullName": "Alice", "email": "alice@test.com",
            "password": "secret123", "confirmPassword": "secret123",
            "security_answer": "blue"
        }):
            self.controller.register()
            flashes = get_flashed_messages(with_categories=True)
            self.assertTrue(any("Registration failed" in msg for _, msg in flashes))


# ── FORGOT PASSWORD ───────────────────────────────────────────────────────── #

class TestForgotPassword(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()
        self.controller = AuthController()

    @patch("app.controllers.authcontrollers.render_template", return_value="forgot_page")
    def test_forgot_password_get_shows_form(self, mock_render):
        """GET request shows the forgot-password form."""
        with self.app.test_request_context(method="GET"):
            result = self.controller.forgot_password()
            self.assertEqual(result, "forgot_page")
            mock_render.assert_called_once_with("forgot-password.html")

    @patch("app.controllers.authcontrollers.render_template", return_value="forgot_page")
    def test_forgot_password_missing_fields_flashes_danger(self, mock_render):
        """Empty fields are rejected before any DB lookup."""
        with self.app.test_request_context(method="POST", data={
            "email": "", "security_answer": "", "new_password": "", "confirm_password": ""
        }):
            self.controller.forgot_password()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("danger", "All fields are required."), flashes)

    @patch("app.controllers.authcontrollers.render_template", return_value="forgot_page")
    def test_forgot_password_mismatched_passwords(self, mock_render):
        """Password mismatch is caught before DB lookup."""
        with self.app.test_request_context(method="POST", data={
            "email": "a@b.com", "security_answer": "blue",
            "new_password": "abc123", "confirm_password": "xyz999"
        }):
            self.controller.forgot_password()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("danger", "Passwords do not match."), flashes)

    @patch("app.controllers.authcontrollers.render_template", return_value="forgot_page")
    def test_forgot_password_short_password_flashes_danger(self, mock_render):
        """New password under 6 characters is rejected."""
        with self.app.test_request_context(method="POST", data={
            "email": "a@b.com", "security_answer": "blue",
            "new_password": "abc", "confirm_password": "abc"
        }):
            self.controller.forgot_password()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("danger", "Password must be at least 6 characters."), flashes)

    @patch("app.controllers.authcontrollers.render_template", return_value="forgot_page")
    @patch("app.controllers.authcontrollers.User")
    def test_forgot_password_email_not_found_flashes_danger(self, mock_user_class, mock_render):
        """Unknown email shows no-account error."""
        mock_instance = MagicMock()
        mock_user_class.return_value = mock_instance
        mock_instance.find_by.return_value = None
        with self.app.test_request_context(method="POST", data={
            "email": "ghost@test.com", "security_answer": "blue",
            "new_password": "newpass1", "confirm_password": "newpass1"
        }):
            self.controller.forgot_password()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("danger", "No account found with that email."), flashes)

    @patch("app.controllers.authcontrollers.render_template", return_value="forgot_page")
    @patch("app.controllers.authcontrollers.User")
    def test_forgot_password_wrong_security_answer(self, mock_user_class, mock_render):
        """Wrong security answer is refused after email is found."""
        mock_instance = MagicMock()
        mock_user_class.return_value = mock_instance
        mock_instance.find_by.return_value = {"id": 1, "email": "a@b.com"}
        mock_instance.check_security_answer.return_value = False
        with self.app.test_request_context(method="POST", data={
            "email": "a@b.com", "security_answer": "wrong",
            "new_password": "newpass1", "confirm_password": "newpass1"
        }):
            self.controller.forgot_password()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("danger", "Incorrect security answer. Please try again."), flashes)

    @patch("app.controllers.authcontrollers.User")
    def test_forgot_password_success_resets_and_redirects(self, mock_user_class):
        """Correct details reset the password and redirect to login."""
        mock_instance = MagicMock()
        mock_user_class.return_value = mock_instance
        mock_instance.find_by.return_value = {"id": 1, "email": "a@b.com"}
        mock_instance.check_security_answer.return_value = True
        with self.app.test_request_context(method="POST", data={
            "email": "a@b.com", "security_answer": "blue",
            "new_password": "newpass1", "confirm_password": "newpass1"
        }):
            response = self.controller.forgot_password()
            mock_instance.update_password.assert_called_once_with("newpass1")
            self.assertEqual(response.status_code, 302)
            self.assertIn("/auth/login", response.location)
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("success", "Password reset successful! Please login with your new password."), flashes)


# ── SETTINGS + STATIC PAGES ───────────────────────────────────────────────── #

class TestAuthStaticPages(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()
        self.controller = AuthController()

    @patch("app.controllers.authcontrollers.render_template", return_value="settings_page")
    def test_settings_logged_in_renders_page(self, mock_render):
        """Logged-in user sees the settings page."""
        with self.app.test_request_context():
            session["user_id"] = 1
            result = self.controller.settings()
            self.assertEqual(result, "settings_page")
            mock_render.assert_called_once_with("settings.html")

    def test_settings_logged_out_redirects_to_login(self):
        """Guest is redirected to login when accessing settings."""
        with self.app.test_request_context():
            response = self.controller.settings()
            self.assertEqual(response.status_code, 302)
            self.assertIn("/auth/login", response.location)

    @patch("app.controllers.authcontrollers.render_template", return_value="base_page")
    def test_base_renders_template(self, mock_render):
        """base() renders base.html."""
        with self.app.test_request_context():
            result = self.controller.base()
            self.assertEqual(result, "base_page")
            mock_render.assert_called_once_with("base.html")

    @patch("app.controllers.authcontrollers.render_template", return_value="about_page")
    def test_about_us_renders_template(self, mock_render):
        """about_us() renders about-us.html."""
        with self.app.test_request_context():
            result = self.controller.about_us()
            self.assertEqual(result, "about_page")
            mock_render.assert_called_once_with("about-us.html")

    @patch("app.controllers.authcontrollers.render_template", return_value="contact_page")
    def test_contact_renders_template(self, mock_render):
        """contact() renders contact.html."""
        with self.app.test_request_context():
            result = self.controller.contact()
            self.assertEqual(result, "contact_page")
            mock_render.assert_called_once_with("contact.html")

    @patch("app.controllers.authcontrollers.render_template", return_value="privacy_page")
    def test_privacy_policy_renders_template(self, mock_render):
        """privacy_policy() renders privacy-policy.html."""
        with self.app.test_request_context():
            result = self.controller.privacy_policy()
            self.assertEqual(result, "privacy_page")
            mock_render.assert_called_once_with("privacy-policy.html")

    @patch("app.controllers.authcontrollers.render_template", return_value="terms_page")
    def test_terms_renders_template(self, mock_render):
        """terms() renders terms.html."""
        with self.app.test_request_context():
            result = self.controller.terms()
            self.assertEqual(result, "terms_page")
            mock_render.assert_called_once_with("terms.html")


if __name__ == "__main__":
    unittest.main()