from flask import render_template, redirect, url_for, session, flash, request
from app.controllers.BaseController import BaseController
from app.models.UserModel import User


class AuthController(BaseController):
    
    # ========== LOGIN METHOD ==========
    def login(self):
        # GET request: show the login form
        if request.method == "GET":
            return render_template("login.html")
        
        # POST request: process login
        if request.method == "POST":
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "").strip()
            
            # Check if email is provided
            if not email or not password:
                flash("Email and password are required.", "danger")
                return render_template("login.html")
            
            # Check if user exists in database
            user = User(email=email)
            user_data = user.find_by("email", email)
            
            if not user_data:
                flash("Email not found. Please register.", "danger")
                return render_template("login.html")
            
            # Check if password is correct
            if not user.check_password(password):
                flash("Incorrect password. Please try again.", "danger")
                return render_template("login.html")
            
            # LOGIN SUCCESS: Set session variables
            session["user_id"] = user_data["id"]
            session["user_name"] = user_data["name"]
            session["user_email"] = user_data["email"]
            session["user_role"] = user_data["role"]
            
            flash(f"Welcome, {user_data['name']}!", "success")
            return redirect(url_for("dashboard"))
    
    
    # ========== REGISTER METHOD ==========
    def register(self):
        # GET request: show the register form
        if request.method == "GET":
            return render_template("register.html")
        
        # POST request: process form submission
        if request.method == "POST":
            # Get form data
            name = request.form.get("fullName", "").strip()
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "").strip()
            confirm_password = request.form.get("confirmPassword", "").strip()
            role = request.form.get("role", "customer").strip()
            
            # VALIDATION 1: Check all required fields are filled
            if not name or not email or not password or not confirm_password:
                flash("All fields are required.", "danger")
                return render_template("register.html")
            
            # VALIDATION 2: Check passwords match
            if password != confirm_password:
                flash("Passwords do not match.", "danger")
                return render_template("register.html")
            
            # VALIDATION 3: Check password length
            if len(password) < 6:
                flash("Password must be at least 6 characters.", "danger")
                return render_template("register.html")
            
            # VALIDATION 4: Check name length
            if len(name) > 100:
                flash("Name must be under 100 characters.", "danger")
                return render_template("register.html")
            
            # VALIDATION 5: Check if email already exists
            new_user = User(name=name, email=email, password=password, role=role)
            if new_user.email_exists():
                flash("Email already registered. Please login or use a different email.", "danger")
                return render_template("register.html")
            
            # SAVE USER TO DATABASE
            try:
                new_user.save()
                flash("Registration successful! Please login with your credentials.", "success")
                return redirect(url_for("auth.login"))
            except Exception as e:
                flash(f"Registration failed: {str(e)}", "danger")
                return render_template("register.html")
    
    
    # ========== SETTINGS METHOD ==========
    def settings(self):
        return render_template('settings.html')
    
    
    # ========== BASE METHOD ==========
    def base(self):
        return render_template('base.html')
    
 
