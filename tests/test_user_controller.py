import unittest
from unittest.mock import patch, MagicMock
from flask import Flask, Blueprint, session, get_flashed_messages
from app.controllers.UserController import UserController


def make_test_app():
    """Builds a minimal Flask app with real blueprints so url_for() resolves correctly."""
    app = Flask(__name__)
    app.secret_key = "user-secret"

    user_bp = Blueprint("user", __name__)
    user_bp.route("/dashboard",        endpoint="dashboard"       )(lambda: "dashboard")
    user_bp.route("/create-shipment",  endpoint="create_shipment" )(lambda: "create_shipment")
    user_bp.route("/shipment-history", endpoint="shipment_history")(lambda: "shipment_history")
    user_bp.route("/settings",         endpoint="settings"        )(lambda: "settings")
    user_bp.route("/delete-account",   endpoint="delete_account"  )(lambda: "delete_account")
    user_bp.route("/logout",           endpoint="logout"          )(lambda: "logout")
    app.register_blueprint(user_bp, url_prefix="/user")

    auth_bp = Blueprint("auth", __name__)
    auth_bp.route("/login",    endpoint="login"   )(lambda: "login")
    auth_bp.route("/about-us", endpoint="about_us")(lambda: "about_us")
    app.register_blueprint(auth_bp, url_prefix="/auth")

    return app


class TestHome(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()
        self.controller = UserController()

    def test_home_redirects_to_dashboard_if_logged_in(self):
        """Logged-in user is sent to dashboard."""
        with self.app.test_request_context():
            session["user_id"] = 1
            response = self.controller.home()
            self.assertEqual(response.status_code, 302)
            self.assertIn("/user/dashboard", response.location)

    def test_home_redirects_to_about_us_if_logged_out(self):
        """Guest user is sent to about-us page."""
        with self.app.test_request_context():
            response = self.controller.home()
            self.assertEqual(response.status_code, 302)
            self.assertIn("/auth/about-us", response.location)


class TestDashboard(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()
        self.controller = UserController()

    @patch("app.models.ShipmentModel.Shipment.find_recent_for_user")
    @patch("app.controllers.UserController.render_template")
    def test_dashboard_renders_with_user_details(self, mock_render, mock_find_recent):
        """Dashboard loads with session user details and recent shipments."""
        mock_find_recent.return_value = [{"id": 1}]
        with self.app.test_request_context():
            session["user_id"] = 10
            session["user_name"] = "Hari"
            session["user_role"] = "customer"
            self.controller.dashboard()
            mock_render.assert_called_once_with(
                "dashboard.html", user_name="Hari", user_role="customer", recent=[{"id": 1}]
            )


class TestCreateShipment(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()
        self.controller = UserController()

    @patch("app.controllers.UserController.render_template")
    @patch("app.models.UserModel.User.find_by")
    def test_create_shipment_get_renders_form(self, mock_find_by, mock_render):
        """GET request renders the create-shipment form."""
        mock_find_by.return_value = {"email": "test@test.com"}
        with self.app.test_request_context(method="GET"):
            session["user_email"] = "test@test.com"
            self.controller.create_shipment()
            mock_render.assert_called_once()

    def test_create_shipment_post_missing_names_flashes_danger(self):
        """Missing sender/receiver names shows danger flash."""
        with self.app.test_request_context(method="POST", data={"sender_name": ""}):
            response = self.controller.create_shipment()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("danger", "Sender and receiver names are required."), flashes)
            self.assertEqual(response.status_code, 302)

    def test_create_shipment_post_invalid_delivery_type(self):
        """Invalid delivery type shows danger flash."""
        form_data = {"sender_name": "A", "receiver_name": "B", "delivery_type": "Rocket"}
        with self.app.test_request_context(method="POST", data=form_data):
            self.controller.create_shipment()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("danger", "Please select a valid delivery type."), flashes)

    def test_create_shipment_post_invalid_weight(self):
        """Negative weight shows danger flash."""
        form_data = {"sender_name": "A", "receiver_name": "B", "delivery_type": "Standard", "weight": "-5"}
        with self.app.test_request_context(method="POST", data=form_data):
            self.controller.create_shipment()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("danger", "Package weight must be greater than 0 kg."), flashes)

    def test_create_shipment_post_zero_weight(self):
        """Zero weight shows danger flash."""
        form_data = {"sender_name": "A", "receiver_name": "B", "delivery_type": "Standard", "weight": "0"}
        with self.app.test_request_context(method="POST", data=form_data):
            self.controller.create_shipment()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("danger", "Package weight must be greater than 0 kg."), flashes)

    @patch("app.models.ShipmentModel.Shipment.create")
    def test_create_shipment_post_success(self, mock_create):
        """Valid payload creates shipment and redirects to history."""
        form_data = {
            "sender_name": "A", "receiver_name": "B", "delivery_type": "Standard",
            "weight": "2.5", "payment_method": "cod", "receiver_city": "Kathmandu"
        }
        with self.app.test_request_context(method="POST", data=form_data):
            session["user_id"] = 1
            response = self.controller.create_shipment()
            flashes = get_flashed_messages(with_categories=True)
            self.assertEqual(response.status_code, 302)
            self.assertIn("/user/shipment-history", response.location)
            self.assertTrue(len(flashes) > 0)
            self.assertEqual(flashes[0][0], "success")


class TestShipmentHistory(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()
        self.controller = UserController()

    @patch("app.models.ShipmentModel.Shipment.find_by_user")
    @patch("app.models.ShipmentModel.Shipment.get_stats_for_user")
    @patch("app.controllers.UserController.render_template")
    def test_shipment_history_with_status_filter(self, mock_render, mock_stats, mock_find):
        """History page filters by valid status query param."""
        mock_find.return_value = []
        mock_stats.return_value = {}
        with self.app.test_request_context("/?status=delivered"):
            session["user_id"] = 1
            self.controller.shipment_history()
            mock_render.assert_called_once()
            _, kwargs = mock_render.call_args
            self.assertEqual(kwargs["current_filter"], "delivered")

    @patch("app.models.ShipmentModel.Shipment.find_by_user")
    @patch("app.models.ShipmentModel.Shipment.get_stats_for_user")
    @patch("app.controllers.UserController.render_template")
    def test_shipment_history_invalid_filter_defaults_to_all(self, mock_render, mock_stats, mock_find):
        """Unknown status param falls back to 'all'."""
        mock_find.return_value = []
        mock_stats.return_value = {}
        with self.app.test_request_context("/?status=unknown"):
            session["user_id"] = 1
            self.controller.shipment_history()
            _, kwargs = mock_render.call_args
            self.assertEqual(kwargs["current_filter"], "all")


class TestSummary(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()
        self.controller = UserController()

    @patch("app.models.ShipmentModel.Shipment.get_summary_for_user")
    @patch("app.models.ShipmentModel.Shipment.find_recent_for_user")
    @patch("app.controllers.UserController.render_template")
    def test_summary_renders_correctly(self, mock_render, mock_find, mock_summary):
        """Summary page renders with aggregated stats and recent shipments."""
        mock_summary.return_value = {"total": 5}
        mock_find.return_value = [{"id": 1}]
        with self.app.test_request_context():
            session["user_id"] = 1
            self.controller.summary()
            mock_render.assert_called_once()


class TestSettings(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()
        self.controller = UserController()

    @patch("app.controllers.UserController.render_template")
    @patch("app.models.UserModel.User.find_by")
    def test_settings_get_renders_form(self, mock_find, mock_render):
        """GET request renders settings form with user data."""
        mock_find.return_value = {"name": "Hari"}
        with self.app.test_request_context(method="GET"):
            session["user_email"] = "a@b.com"
            self.controller.settings()
            mock_render.assert_called_once()

    @patch("app.models.UserModel.User.update_profile_info")
    def test_settings_post_profile_success(self, mock_update):
        """Valid profile update flashes success and redirects."""
        form_data = {"form_type": "profile", "name": "New Name", "phone": "9841", "address": "KTM"}
        with self.app.test_request_context(method="POST", data=form_data):
            session["user_email"] = "a@b.com"
            response = self.controller.settings()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("success", "Profile updated successfully!"), flashes)
            self.assertEqual(response.status_code, 302)

    def test_settings_post_profile_missing_name(self):
        """Empty name in profile update shows danger flash."""
        form_data = {"form_type": "profile", "name": "", "phone": "9841", "address": "KTM"}
        with self.app.test_request_context(method="POST", data=form_data):
            session["user_email"] = "a@b.com"
            self.controller.settings()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("danger", "Name cannot be empty."), flashes)

    def test_settings_post_password_missing_fields(self):
        """Empty password fields shows danger flash."""
        form_data = {"form_type": "password", "current_password": "", "new_password": "", "confirm_password": ""}
        with self.app.test_request_context(method="POST", data=form_data):
            session["user_email"] = "a@b.com"
            self.controller.settings()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("danger", "Please fill in all password fields."), flashes)

    @patch("app.models.UserModel.User.check_password", return_value=False)
    def test_settings_post_password_wrong_current(self, mock_check):
        """Wrong current password shows danger flash."""
        form_data = {"form_type": "password", "current_password": "wrong", "new_password": "newpass", "confirm_password": "newpass"}
        with self.app.test_request_context(method="POST", data=form_data):
            session["user_email"] = "a@b.com"
            self.controller.settings()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("danger", "Current password is incorrect."), flashes)

    @patch("app.models.UserModel.User.check_password", return_value=True)
    def test_settings_post_password_mismatch(self, mock_check):
        """Mismatched new/confirm passwords shows danger flash."""
        form_data = {"form_type": "password", "current_password": "old", "new_password": "aaaaaa", "confirm_password": "bbbbbb"}
        with self.app.test_request_context(method="POST", data=form_data):
            session["user_email"] = "a@b.com"
            self.controller.settings()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("danger", "New passwords do not match."), flashes)

    @patch("app.models.UserModel.User.check_password", return_value=True)
    def test_settings_post_password_too_short(self, mock_check):
        """Password under 6 characters shows danger flash."""
        form_data = {"form_type": "password", "current_password": "old", "new_password": "abc", "confirm_password": "abc"}
        with self.app.test_request_context(method="POST", data=form_data):
            session["user_email"] = "a@b.com"
            self.controller.settings()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("danger", "Password must be at least 6 characters."), flashes)

    @patch("app.models.UserModel.User.check_password", return_value=True)
    @patch("app.models.UserModel.User.update_password")
    def test_settings_post_password_success(self, mock_update, mock_check):
        """Valid password change flashes success and redirects."""
        form_data = {"form_type": "password", "current_password": "old", "new_password": "666666", "confirm_password": "666666"}
        with self.app.test_request_context(method="POST", data=form_data):
            session["user_email"] = "a@b.com"
            response = self.controller.settings()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("success", "Password updated successfully!"), flashes)
            self.assertEqual(response.status_code, 302)


class TestDeleteAccount(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()
        self.controller = UserController()

    @patch("app.controllers.UserController.render_template")
    def test_delete_account_get_renders_form(self, mock_render):
        """GET request renders the delete-account confirmation page."""
        with self.app.test_request_context(method="GET"):
            self.controller.delete_account()
            mock_render.assert_called_with("delete-account.html")

    @patch("app.controllers.UserController.render_template")
    def test_delete_account_post_missing_password(self, mock_render):
        """Missing password shows danger flash and re-renders form."""
        with self.app.test_request_context(method="POST", data={"password": ""}):
            self.controller.delete_account()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("danger", "Password is required to delete your account."), flashes)
            mock_render.assert_called_with("delete-account.html")

    @patch("app.models.UserModel.User.find_by", return_value=None)
    @patch("app.controllers.UserController.render_template")
    def test_delete_account_post_user_not_found(self, mock_render, mock_find):
        """User not found in DB shows danger flash and re-renders form."""
        with self.app.test_request_context(method="POST", data={"password": "pass"}):
            session["user_email"] = "ghost@test.com"
            self.controller.delete_account()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("danger", "User not found."), flashes)
            mock_render.assert_called_with("delete-account.html")

    @patch("app.models.UserModel.User.find_by", return_value={"id": 1})
    @patch("app.models.UserModel.User.check_password", return_value=False)
    @patch("app.controllers.UserController.render_template")
    def test_delete_account_post_wrong_password(self, mock_render, mock_check, mock_find):
        """Wrong password shows danger flash and re-renders form."""
        with self.app.test_request_context(method="POST", data={"password": "wrongpass"}):
            session["user_email"] = "a@b.com"
            self.controller.delete_account()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("danger", "Incorrect password. Please try again."), flashes)
            mock_render.assert_called_with("delete-account.html")

    @patch("app.models.UserModel.User.find_by", return_value={"id": 1})
    @patch("app.models.UserModel.User.check_password", return_value=True)
    @patch("app.models.UserModel.User.delete_account")
    def test_delete_account_post_success(self, mock_delete, mock_check, mock_find):
        """Correct password deletes account, clears session, and redirects."""
        with self.app.test_request_context(method="POST", data={"password": "correct_pass"}):
            session["user_email"] = "test@test.com"
            session["user_id"] = 1
            session["user_role"] = "customer"
            response = self.controller.delete_account()
            self.assertNotIn("user_email", session)
            self.assertNotIn("user_id", session)
            self.assertNotIn("user_role", session)
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("success", "Your account has been permanently deleted."), flashes)
            self.assertEqual(response.status_code, 302)
            self.assertIn("/auth/login", response.location)


class TestLogout(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()
        self.controller = UserController()

    @patch("app.controllers.UserController.render_template")
    def test_logout_get_renders_page(self, mock_render):
        """GET request renders the logout confirmation page."""
        with self.app.test_request_context(method="GET"):
            self.controller.logout()
            mock_render.assert_called_with("logout.html")

    def test_logout_post_clears_session_and_redirects(self):
        """POST clears session and redirects to login."""
        @self.app.route("/do-logout", methods=["POST"])
        def do_logout():
            return self.controller.logout()

        with self.app.test_client() as client:
            with client.session_transaction() as sess:
                sess["user_id"] = 42
                sess["user_name"] = "Hari"
                sess["user_role"] = "customer"
            response = client.post("/do-logout")
            self.assertEqual(response.status_code, 302)
            self.assertIn("/auth/login", response.location)
            with client.session_transaction() as sess:
                self.assertNotIn("user_id", sess)
                self.assertNotIn("user_name", sess)
                self.assertNotIn("user_role", sess)


if __name__ == "__main__":
    unittest.main()