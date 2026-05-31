from flask import Flask, render_template, session, redirect, url_for, flash, request, get_flashed_messages, make_response
from app.routes.authroutes import Authroutes
from app.models.database import Database
from app.models.UserModel import User
from functools import wraps
import config
import os


def no_cache(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = make_response(f(*args, **kwargs))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, public, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    return decorated_function


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.", "danger")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function


def create_app():
    app_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(app_dir)

    template_folder = os.path.join(project_root, 'templates')
    static_folder = os.path.join(project_root, 'static')

    app = Flask(
        __name__,
        template_folder=template_folder,
        static_folder=static_folder
    )

    app.secret_key = config.SECRET_KEY

    with app.app_context():
        Database.create_tables()

    auth_routes = Authroutes()
    app.register_blueprint(auth_routes.login())

    # ── PUBLIC ──────────────────────────────────────────────

    @app.route("/")
    def home():
        if "user_id" in session:
            return redirect(url_for("dashboard"))
        return redirect(url_for("auth.login"))

    # ── PROTECTED ───────────────────────────────────────────
    
    @app.route("/delete-account", methods=["GET", "POST"])
    @login_required
    @no_cache
    def delete_account():
        if request.method == "GET":
            return render_template("delete-account.html")

        password = request.form.get("password", "").strip()
        if not password:
            flash("Password is required to delete your account.", "danger")
            return render_template("delete-account.html")

        user_email = session.get("user_email")
        user = User(email=user_email)
        user_data = user.find_by("email", user_email)
        if not user_data:
            flash("User not found.", "danger")
            return render_template("delete-account.html")

        if not user.check_password(password):
            flash("Incorrect password. Please try again.", "danger")
            return render_template("delete-account.html")

        user.delete_account()
        session.clear()
        flash("Your account has been permanently deleted.", "success")
        return redirect(url_for("auth.login"))

    @app.route("/dashboard")
    @login_required
    @no_cache
    def dashboard():
        return render_template("dashboard.html")

    @app.route("/create-shipment")
    @login_required
    @no_cache
    def create_shipment():
        get_flashed_messages()
        return render_template("create-shipment.html")

    @app.route("/shipment-history")
    @login_required
    @no_cache
    def shipment_history():
        get_flashed_messages()
        return render_template("shipment-history.html")

    @app.route("/settings")
    @login_required
    @no_cache
    def settings():
        get_flashed_messages()
        return render_template("settings.html")

    @app.route("/admin-dashboard")
    @login_required
    @no_cache
    def admin_dashboard():
        if session.get("user_role") != "admin":
            flash("You don't have permission to access this page.", "danger")
            return redirect(url_for("dashboard"))
        get_flashed_messages()
        return render_template("admin-dashboard.html")

    @app.route("/logout", methods=["GET", "POST"])
    @login_required
    def logout():
        get_flashed_messages()
        if request.method == "GET":
            return render_template("logout.html")
        if request.method == "POST":
            password = request.form.get("password", "").strip()
            if not password:
                flash("Password is required to logout.", "danger")
                return render_template("logout.html")
            user_email = session.get("user_email")
            user = User(email=user_email)
            user_data = user.find_by("email", user_email)
            if not user_data:
                flash("User not found.", "danger")
                return render_template("logout.html")
            if not user.check_password(password):
                flash("Incorrect password. Please try again.", "danger")
                return render_template("logout.html")
            session.clear()
            flash("You have been logged out successfully.", "success")
            return redirect(url_for("auth.login"))
        
    @app.route("/forgot-password", methods=["GET", "POST"])
    def forgot_password():
            if request.method == "GET":
                return render_template("forgot-password.html")

            email = request.form.get("email", "").strip()
            security_answer = request.form.get("security_answer", "").strip()
            new_password = request.form.get("new_password", "").strip()
            confirm_password = request.form.get("confirm_password", "").strip()

            if not email or not security_answer or not new_password or not confirm_password:
                flash("All fields are required.", "danger")
                return render_template("forgot-password.html")

            if new_password != confirm_password:
                flash("Passwords do not match.", "danger")
                return render_template("forgot-password.html")

            if len(new_password) < 6:
                flash("Password must be at least 6 characters.", "danger")
                return render_template("forgot-password.html")

            user = User(email=email)
            user_data = user.find_by("email", email)
            if not user_data:
                flash("No account found with that email.", "danger")
                return render_template("forgot-password.html")

            if not user.check_security_answer(security_answer):
                flash("Incorrect security answer. Please try again.", "danger")
                return render_template("forgot-password.html")

            user.update_password(new_password)
            flash("Password reset successful! Please login with your new password.", "success")
            return redirect(url_for("auth.login"))

    @app.errorhandler(404)
    def error(e):
        return render_template("error.html"), 404

    return app