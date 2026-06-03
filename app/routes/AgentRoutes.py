from flask import Blueprint
from app.controllers.AgentControllers import AgentController

class AgentRoutes:
    def __init__(self):
        self.bp = Blueprint("agent", __name__)
        self.controller = AgentController()

    def register_routes(self):
        self.bp.add_url_rule(
            "/agent-dashboard",
            endpoint="dashboard",
            view_func=self.controller.dashboard,
            methods=["GET"]
        )
        return self.bp