from flask import Blueprint
from app.controllers.authcontrollers import AuthController


class Authroutes:
    def __init__(self):
        self.bp = Blueprint("auth", __name__)
        self.controller = AuthController()

    def login(self):
        self.bp.add_url_rule(
            "/login",
            endpoint="login",
            view_func=self.controller.login,
            methods=["GET", "POST"]
        )
        self.bp.add_url_rule(
            "/register",
            endpoint="register",
            view_func=self.controller.register,
            methods=["GET", "POST"]
        )
        self.bp.add_url_rule(
            "/about-us",
            endpoint="about_us",
            view_func=self.controller.about_us,
            methods=["GET", "POST"]
        )
        self.bp.add_url_rule(
            "/privacy-policy",
            endpoint="privacy_policy",
            view_func=self.controller.privacy_policy,
            methods=["GET"]
        )
        self.bp.add_url_rule(
            "/terms",
            endpoint="terms",
            view_func=self.controller.terms,
            methods=["GET"]
        )
        self.bp.add_url_rule(
            "/forgot-password",
            endpoint="forgot_password",
            view_func=self.controller.forgot_password,
            methods=["GET", "POST"]
        )
        return self.bp
    