from flask import Blueprint
from app.controllers.AgentControllers import AgentController

class AgentRoutes:
    def __init__(self):
        self.bp = Blueprint("agent", __name__)
        self.controller = AgentController()

    def register_routes(self):
        # 1. Main Dashboard View
        self.bp.add_url_rule(
            "/agent-dashboard",
            endpoint="dashboard",
            view_func=self.controller.dashboard,
            methods=["GET"]
        )
    
        # 2. Historical Completed Deliveries View
        self.bp.add_url_rule(
            "/agent-history",
            endpoint="delivery_history",
            view_func=self.controller.delivery_history,
            methods=["GET"]
        )
        
        # 3. Available Deliveries View
        self.bp.add_url_rule(
            "/agent-deliveries",
            endpoint="available_deliveries",
            view_func=self.controller.available_deliveries,
            methods=["GET"]
        )

        # 4. API: Fetch structural delivery detail mapping items for Modals
        self.bp.add_url_rule(
            "/api/agent/shipment-details/<int:shipment_id>",
            endpoint="get_shipment_details",
            view_func=self.controller.get_shipment_details,
            methods=["GET"]
        )

        # 5. API: Process table structural changes upon clicking Accept Request
        self.bp.add_url_rule(
            "/api/agent/accept-delivery",
            endpoint="accept_delivery",
            view_func=self.controller.accept_delivery,
            methods=["POST"]
        )

        # 6. New: Shipment Management View (for interactive route tracking)
        self.bp.add_url_rule(
            "/agent-routes",
            endpoint="shipment_management",
            view_func=self.controller.shipment_management,
            methods=["GET"]
        )

        self.bp.add_url_rule(
            "/agent-settings",
            endpoint="settings",
            view_func=self.controller.settings,
            methods=["GET", "POST"]
        )

        self.bp.add_url_rule(
            "/agent-routes", 
            endpoint="shipment_management",
            view_func=self.controller.shipment_management,
            methods=["GET"]
        )
        
        self.bp.add_url_rule(
            "/api/agent/update-status",
            endpoint="update_status",
            view_func=self.controller.update_status,
            methods=["POST"]
        )
        self.bp.add_url_rule(
            "/api/agent/fail-delivery",
            endpoint="fail_delivery",
            view_func=self.controller.fail_delivery,
            methods=["POST"]
        )
        self.bp.add_url_rule(
            "/agent-settings",
            endpoint="settings",
            view_func=self.controller.settings,
            methods=["GET", "POST"]
        )
        
        return self.bp
     