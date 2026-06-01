from flask import Flask, app, render_template, session, redirect, url_for, flash, request, get_flashed_messages, make_response
from app.routes.authroutes import Authroutes
from app.models.database import Database
from app.models.ShipmentModel import Shipment
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
    static_folder   = os.path.join(project_root, 'static')

    app = Flask(
        __name__,
        template_folder=template_folder,
        static_folder=static_folder
    )

    app.secret_key = config.SECRET_KEY

    with app.app_context():
        Database.create_tables()          # ← now creates all 4 tables

    # ── Teammate's auth blueprint (untouched) ──────────────────────────── #
    auth_routes = Authroutes()
    app.register_blueprint(auth_routes.login())

    # ── Admin API blueprint (new — prefix /api/admin, no clash) ────────── #
    from app.routes.admin import admin_bp
    app.register_blueprint(admin_bp)

    # ── PUBLIC ──────────────────────────────────────────────────────────── #

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
        return render_template(
            "dashboard.html",
            user_name=session.get("user_name"),
            user_role=session.get("user_role")
        )
    @app.route("/create-shipment", methods=["GET", "POST"])
    @login_required
    @no_cache
    def create_shipment():
        if request.method == "POST":
            sender_name = request.form.get("sender_name", "").strip()
            receiver_name = request.form.get("receiver_name", "").strip()
            delivery_type = request.form.get("delivery_type", "").strip()

            # delivery type is required and must be one of the allowed values
            allowed_types = ["Standard", "Express", "Same-day"]
            if not sender_name or not receiver_name:
                flash("Sender and receiver names are required.", "danger")
                return redirect(url_for("create_shipment"))
            if delivery_type not in allowed_types:
                flash("Please select a valid delivery type.", "danger")
                return redirect(url_for("create_shipment"))

            shipment = Shipment()
            tracking_id = Shipment.generate_tracking_id()
            shipment.create({
                "tracking_id": tracking_id,
                "user_id": session.get("user_id"),
                "sender_name": sender_name,
                "sender_phone": request.form.get("sender_phone", "").strip(),
                "sender_address": request.form.get("sender_address", "").strip(),
                "sender_city": request.form.get("sender_city", "").strip(),
                "receiver_name": receiver_name,
                "receiver_phone": request.form.get("receiver_phone", "").strip(),
                "receiver_address": request.form.get("receiver_address", "").strip(),
                "receiver_city": request.form.get("receiver_city", "").strip(),
                "package_type": request.form.get("package_type", "").strip(),
                "weight": request.form.get("weight") or 0,
                "delivery_type": delivery_type,
                "payment_method": request.form.get("payment_method", "").strip(),
                "status": "Pending",
            })
            flash(f"Shipment created! Tracking ID: {tracking_id}", "success")
            return redirect(url_for("shipment_history"))

        get_flashed_messages()
        return render_template(
            "create-shipment.html",
            user_name=session.get("user_name"),
            user_role=session.get("user_role")
        )

    @app.route("/shipment-history")
    @login_required
    @no_cache
    def shipment_history():
        get_flashed_messages()
        return render_template(
            "shipment-history.html",
            user_name=session.get("user_name"),
            user_role=session.get("user_role")
        )

    @app.route("/settings", methods=["GET", "POST"])
    @login_required
    @no_cache
    def settings():
        user_email = session.get("user_email")
        user = User(email=user_email)

        if request.method == "POST":
            form_type = request.form.get("form_type", "")
            if form_type == "profile":
                name = request.form.get("name", "").strip()
                phone = request.form.get("phone", "").strip()
                address = request.form.get("address", "").strip()
                if not name:
                    flash("Name cannot be empty.", "danger")
                    return redirect(url_for("settings"))
                user.update_profile_info(name, phone, address)
                session["user_name"] = name  # keep sidebar/greeting in sync
                flash("Profile updated successfully!", "success")
                return redirect(url_for("settings"))

            if form_type == "password":
                current = request.form.get("current_password", "").strip()
                new = request.form.get("new_password", "").strip()
                confirm = request.form.get("confirm_password", "").strip()
                if not current or not new or not confirm:
                    flash("Please fill in all password fields.", "danger")
                    return redirect(url_for("settings"))
                if not user.check_password(current):
                    flash("Current password is incorrect.", "danger")
                    return redirect(url_for("settings"))
                if new != confirm:
                    flash("New passwords do not match.", "danger")
                    return redirect(url_for("settings"))
                if len(new) < 6:
                    flash("Password must be at least 6 characters.", "danger")
                    return redirect(url_for("settings"))
                user.update_password(new)
                flash("Password updated successfully!", "success")
                return redirect(url_for("settings"))

        get_flashed_messages()
        user_data = user.find_by("email", user_email)
        return render_template(
            "settings.html",
            user=user_data,
            user_name=session.get("user_name"),
            user_role=session.get("user_role")
        )
    @app.route("/admin-dashboard")
    @no_cache
    def admin_dashboard():
        # Accept either customer session or admin API session
        if not session.get("user_id") and not session.get("admin_logged_in"):
            return redirect(url_for("auth.login"))
        get_flashed_messages()
        return render_template(
            "admin-dashboard.html",
            user_name=session.get("user_name") or session.get("admin_name"),
            user_role=session.get("user_role") or session.get("admin_role")
        )

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
    
    @app.route("/debug-session")
    def debug_session():
      from flask import current_app
      rules = {str(r): r.endpoint for r in current_app.url_map.iter_rules()}
      return {"session": dict(session), "routes": rules}

    return app

