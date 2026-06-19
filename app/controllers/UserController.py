from flask import (
    render_template, redirect, url_for, session, flash, request,
    get_flashed_messages
)
from app.controllers.BaseController import BaseController
from app.models.ShipmentModel import Shipment
from app.models.UserModel import User


class UserController(BaseController):
    """
    Handles all customer-facing pages:
      home, dashboard, create_shipment, shipment_history,
      summary, settings, delete_account, forgot_password, logout.
    """

    # ── Home ────────────────────────────────────────────────
    def home(self):
        if "user_id" in session:
            return redirect(url_for("user.dashboard"))
        return redirect(url_for("auth.about_us"))

    # ── Dashboard ───────────────────────────────────────────
    def dashboard(self):
        user_id = session.get("user_id")
        shipment = Shipment()
        recent = shipment.find_recent_for_user(user_id, limit=5)
        return render_template(
            "dashboard.html",
            user_name=session.get("user_name"),
            user_role=session.get("user_role"),
            recent=recent,
        )

    # ── Create Shipment ─────────────────────────────────────
    def create_shipment(self):
        if request.method == "POST":
            sender_name = request.form.get("sender_name", "").strip()
            receiver_name = request.form.get("receiver_name", "").strip()
            delivery_type = request.form.get("delivery_type", "").strip()

            payment_method = request.form.get("payment_method", "cod").strip()
            if payment_method != "cod":
                payment_method = "cod"

            allowed_types = ["Standard", "Express", "Same-day"]
            if not sender_name or not receiver_name:
                flash("Sender and receiver names are required.", "danger")
                return redirect(url_for("user.create_shipment"))
            if delivery_type not in allowed_types:
                flash("Please select a valid delivery type.", "danger")
                return redirect(url_for("user.create_shipment"))

            try:
                weight = float(request.form.get("weight") or 0)
            except ValueError:
                weight = 0
            if weight <= 0:
                flash("Package weight must be greater than 0 kg.", "danger")
                return redirect(url_for("user.create_shipment"))

            delivery_prices = {"Standard": 150, "Express": 350, "Same-day": 500}
            delivery_cost = delivery_prices.get(delivery_type, 0)

            shipment = Shipment()
            tracking_id = Shipment.generate_tracking_id()

            shipment.create({
                "tracking_id": tracking_id,
                "user_id": session.get("user_id"),
                "sender_name": sender_name,
                "sender_phone": request.form.get("sender_phone", "").strip(),
                "sender_address": request.form.get("sender_address", "").strip(),
                "sender_city": request.form.get("sender_city", "").strip(),
                "sender_district": request.form.get("sender_district", "").strip(),
                "receiver_name": receiver_name,
                "receiver_phone": request.form.get("receiver_phone", "").strip(),
                "receiver_address": request.form.get("receiver_address", "").strip(),
                "receiver_city": request.form.get("receiver_city", "").strip(),
                "receiver_district": request.form.get("receiver_district", "").strip(),
                "destination": request.form.get("receiver_city", "").strip(),
                "package_type": request.form.get("package_type", "").strip(),
                "weight": weight,
                "estimated_value": request.form.get("value") or 0,
                "delivery_cost": delivery_cost,
                "delivery_type": delivery_type,
                "payment_method": payment_method,
                "status": "processing",
                "instructions": request.form.get("instructions", "").strip(),
            })
            flash(f"Shipment created! Tracking ID: {tracking_id} — Total: NPR {delivery_cost}", "success")
            return redirect(url_for("user.shipment_history"))

        get_flashed_messages()
        current_user = User(email=session.get("user_email")).find_by("email", session.get("user_email"))
        cities = ["Kathmandu", "Pokhara", "Itahari", "Biratnagar", "Lalitpur",
                  "Bhaktapur", "Birgunj", "Dharan", "Butwal", "Nepalgunj"]
        return render_template(
            "create-shipment.html",
            user_name=session.get("user_name"),
            user_role=session.get("user_role"),
            current_user=current_user,
            cities=cities
        )

    # ── Shipment History ────────────────────────────────────
    def shipment_history(self):
        get_flashed_messages()
        user_id = session.get("user_id")

        allowed = {"delivered": "delivered", "in_transit": "in_transit",
                   "processing": "processing",
                   "delayed": "delayed", "cancelled": "cancelled"}
        raw = request.args.get("status", "all")
        db_status = allowed.get(raw)

        shipment = Shipment()
        shipments = shipment.find_by_user(user_id, status=db_status)
        stats = shipment.get_stats_for_user(user_id)

        return render_template(
            "shipment-history.html",
            user_name=session.get("user_name"),
            user_role=session.get("user_role"),
            shipments=shipments,
            stats=stats,
            current_filter=raw if db_status else "all",
        )

    # ── Summary ─────────────────────────────────────────────
    def summary(self):
        user_id = session.get("user_id")
        shipment = Shipment()
        summary = shipment.get_summary_for_user(user_id)
        recent = shipment.find_recent_for_user(user_id, limit=5)
        return render_template(
            "summary.html",
            user_name=session.get("user_name"),
            user_role=session.get("user_role"),
            summary=summary,
            recent=recent,
        )

    # ── Settings ────────────────────────────────────────────
    def settings(self):
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
                    return redirect(url_for("user.settings"))
                user.update_profile_info(name, phone, address)
                session["user_name"] = name
                flash("Profile updated successfully!", "success")
                return redirect(url_for("user.settings"))

            if form_type == "password":
                current = request.form.get("current_password", "").strip()
                new = request.form.get("new_password", "").strip()
                confirm = request.form.get("confirm_password", "").strip()
                if not current or not new or not confirm:
                    flash("Please fill in all password fields.", "danger")
                    return redirect(url_for("user.settings"))
                if not user.check_password(current):
                    flash("Current password is incorrect.", "danger")
                    return redirect(url_for("user.settings"))
                if new != confirm:
                    flash("New passwords do not match.", "danger")
                    return redirect(url_for("user.settings"))
                if len(new) < 6:
                    flash("Password must be at least 6 characters.", "danger")
                    return redirect(url_for("user.settings"))
                user.update_password(new)
                flash("Password updated successfully!", "success")
                return redirect(url_for("user.settings"))

        get_flashed_messages()
        user_data = user.find_by("email", user_email)
        return render_template(
            "settings.html",
            user=user_data,
            user_name=session.get("user_name"),
            user_role=session.get("user_role")
        )

    # ── Delete Account ──────────────────────────────────────
    def delete_account(self):
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

    # ── Logout ──────────────────────────────────────────────
    def logout(self):
        get_flashed_messages()
        if request.method == "POST":
            session.clear()
            flash("You have been logged out successfully.", "success")
            return redirect(url_for("auth.login"))
        return render_template("logout.html")
