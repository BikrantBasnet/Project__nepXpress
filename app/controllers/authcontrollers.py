from flask import render_template, redirect, url_for, session, flash,request
from app.controllers.BaseController import BaseController
from app.models.UserModel import User


class AuthController(BaseController):
    def login(self):
        return render_template('login.html')
    
    def register(self):
        if self.is_logged_in():
            return redirect(url_for("auth.dashboard"))
        if request.method == "POST":
            name, email = self.get_form_data("name", "email")
            password = request.form.get("password", "")
            # Validation
            if not name or not email or not password:
                flash("All fields are required.", "danger")
                return render_template("register.html")

            if len(name) > 100:
                flash("Name must be under 100 characters.", "danger")
                return render_template("register.html")

            if len(password) < 6:
                flash("Password must be at least 6 characters.", "danger")
                return render_template("register.html")

            # Create a new User object and check email
            new_user = User(name=name, email=email, password=password, role="user")

            if new_user.email_exists():
                flash("Email already exists.", "danger")
                return redirect(url_for("auth.register"))

            # Save to database
            new_user.save()
            return self.flash_and_redirect(
                "Registration successful! Please login.", "success", "auth.login"
            )

        return render_template("register.html")
    

    def settings(self):
        return render_template('settings.html')
    
    def base(self):
        return render_template('base.html')

    
 
