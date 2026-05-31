from flask import render_template, redirect, url_for, session, flash, request
from app.controllers.BaseController import BaseController
from app.models.UserModel import User


class AuthController(BaseController):

    def login(self):
        if "user_id" in session:
            return redirect(url_for("dashboard"))
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
            return redirect(url_for("dashboard"))

    def register(self):
        if "user_id" in session:
            return redirect(url_for("dashboard"))
        if request.method == "GET":
            return render_template("register.html")
        if request.method == "POST":
            name = request.form.get("fullName", "").strip()
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "").strip()
            confirm_password = request.form.get("confirmPassword", "").strip()
            role = request.form.get("role", "customer").strip()
            security_answer = request.form.get("security_answer", "").strip()
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
            new_user = User(name=name, email=email, password=password, role=role, security_answer=security_answer)
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

    def logout(self):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
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

    def settings(self):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return render_template('settings.html')

    def base(self):
        return render_template('base.html')