from flask import render_template, redirect, url_for, session, flash, request
from app.controllers.BaseController import BaseController
from app.models.UserModel import User


class AuthController(BaseController):

    def login(self):
        if "user_id" in session:
            if session.get("user_role") == "admin":
                return redirect(url_for("admin_dashboard"))
            if session.get("user_role") == "agent":
                return redirect(url_for("agent.dashboard"))
            return redirect(url_for("user.dashboard"))
        if request.method == "GET":
            return render_template("login.html")
        if request.method == "POST":
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "").strip()
            if not email or not password:
                flash("Email and password are required.", "danger")
                return render_template("login.html")
            user = User(email=email)
            user_data = user.find_by("email", email)
            if not user_data:
                flash("Email not found. Please register.", "danger")
                return render_template("login.html")
            if not user.check_password(password):
                flash("Incorrect password. Please try again.", "danger")
                return render_template("login.html")
           
            session["user_id"] = user_data["id"]
            session["user_name"] = user_data["name"]
            session["user_email"] = user_data["email"]
            session["user_role"] = user_data["role"]
            flash(f"Welcome, {user_data['name']}!", "success")
            if user_data["role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            if user_data["role"] == "agent":
                return redirect(url_for("agent.dashboard"))
            return redirect(url_for("user.dashboard"))

    def register(self):
        if "user_id" in session:
           return redirect(url_for("user.dashboard"))
        if request.method == "GET":
            return render_template("register.html")
        if request.method == "POST":
            name = request.form.get("fullName", "").strip()
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "").strip()
            confirm_password = request.form.get("confirmPassword", "").strip()
            role = request.form.get("role", "customer").strip()
            security_answer = request.form.get("security_answer", "").strip()
            phone = request.form.get("phone", "").strip()
            if not name or not email or not password or not confirm_password or not security_answer:
                flash("All fields are required.", "danger")
                return render_template("register.html")
            if password != confirm_password:
                flash("Passwords do not match.", "danger")
                return render_template("register.html")
            if len(password) < 6:
                flash("Password must be at least 6 characters.", "danger")
                return render_template("register.html")
            if len(name) > 100:
                flash("Name must be under 100 characters.", "danger")
                return render_template("register.html")
            new_user = User(name=name, email=email, password=password, role=role, security_answer=security_answer, phone=phone)
            if new_user.email_exists():
                flash("Email already registered. Please login or use a different email.", "danger")
                return render_template("register.html")
            try:
                new_user.save()
                flash("Registration successful! Please login with your credentials.", "success")
                return redirect(url_for("auth.login"))
            except Exception as e:
                flash(f"Registration failed: {str(e)}", "danger")
                return render_template("register.html")
    
    def forgot_password(self):
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

    def settings(self):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return render_template("settings.html")

    def base(self):
        return render_template("base.html")

    def about_us(self):
        return render_template("about-us.html")

    def contact(self):
        return render_template("contact.html")

    def privacy_policy(self):
        return render_template("privacy-policy.html")

    def terms(self):
        return render_template("terms.html")

    
    