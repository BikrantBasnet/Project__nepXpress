from flask import Blueprint
from app.controllers.AdminDashboardController import DashboardController


class Dashboardroutes:
    def __init__(self):
        self.bp = Blueprint("dashboard", __name__)
        self.controller = DashboardController()

    def dashboard(self):
        self.bp.add_url_rule(
            "/dashboard",
            endpoint="dashboard",
            view_func=self.controller.dashboard,
            methods=["GET", "POST"]
        )
        self.bp.add_url_rule(
            "/admin-dashboard",
            endpoint="admin-dashboard",
            view_func=self.controller.admin_dashboard,
            methods=["GET", "POST"]
        )
      
        return self.bp