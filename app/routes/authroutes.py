from flask import Blueprint
from app.controllers.authcontrollers import AuthController

class Authroutes:
    def __init__(self):
        self.bp = Blueprint("auth", __name__)
        self.controller = AuthController()

    def login(self):
        # Register login route (accepts GET and POST methods)
        self.bp.route("/login", methods=["GET", "POST"])(
            self.controller.login
        )
        
        # Register register route (accepts GET and POST methods)
        self.bp.route("/register", methods=["GET", "POST"])(
            self.controller.register
        )
        
        # Register settings route
        self.bp.route("/settings", methods=["GET", "POST"])(
            self.controller.settings
        )
        
        # Register base route
        self.bp.route("/base", methods=["GET", "POST"])(
            self.controller.base
        )
        
        return self.bp