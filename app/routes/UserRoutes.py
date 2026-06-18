from flask import Blueprint
from app.controllers.UserController import UserController
from app.auth import login_required, no_cache


class UserRoutes:
    def __init__(self):
        self.bp = Blueprint("user", __name__)
        self.controller = UserController()

    def register(self):
        self.bp.route("/", methods=["GET"])(
            self.controller.home
        )
        self.bp.route("/dashboard", methods=["GET"])(
            login_required(no_cache(self.controller.dashboard))
        )
        self.bp.route("/create-shipment", methods=["GET", "POST"])(
            login_required(no_cache(self.controller.create_shipment))
        )
        self.bp.route("/shipment-history", methods=["GET"])(
            login_required(no_cache(self.controller.shipment_history))
        )
        self.bp.route("/summary", methods=["GET"])(
            login_required(no_cache(self.controller.summary))
        )
        self.bp.route("/settings", methods=["GET", "POST"])(
            login_required(no_cache(self.controller.settings))
        )
        self.bp.route("/delete-account", methods=["GET", "POST"])(
            login_required(no_cache(self.controller.delete_account))
        )
        self.bp.route("/logout", methods=["GET", "POST"])(
            login_required(self.controller.logout)
        )
        return self.bp