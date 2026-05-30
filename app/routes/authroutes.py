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
            "/logout",
            endpoint="logout",
            view_func=self.controller.logout,
            methods=["GET", "POST"]
        )
        self.bp.add_url_rule(
            "/settings",
            endpoint="settings",
            view_func=self.controller.settings,
            methods=["GET", "POST"]
        )
        self.bp.add_url_rule(
            "/base",
            endpoint="base",
            view_func=self.controller.base,
            methods=["GET", "POST"]
        )
        return self.bp