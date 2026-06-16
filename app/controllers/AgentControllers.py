from flask import render_template, session, redirect, url_for, request, jsonify
from app.controllers.BaseController import BaseController
from app.models.ShipmentModel import Shipment

class AgentController(BaseController):

    def dashboard(self):
        if "user_id" not in session or session.get("user_role") != "agent":
            return redirect(url_for("auth.login"))
            
        return render_template(
            "agent-dashboard.html",
            user_name=session.get("user_name"),
            user_role=session.get("user_role")
        )
    
    def delivery_history(self):
        if "user_id" not in session or session.get("user_role") != "agent":
            return redirect(url_for("auth.login"))
            
        agent_id = session.get("user_id")
        shipment_records = Shipment.get_history_for_agent(agent_id)
        
        return render_template(
            "agent-history.html", 
            history_records=shipment_records,
            user_name=session.get("user_name"),
            user_role=session.get("user_role")
        )

    def available_deliveries(self):
        """GET /agent-deliveries — Renders the page with live unassigned orders"""
        if "user_id" not in session or session.get("user_role") != "agent":
            return redirect(url_for("auth.login"))
            
        # Pull live pending database tuples
        live_requests = Shipment.get_available_deliveries()
        
        return render_template(
            "agent-deliveries.html",
            requests=live_requests,
            user_name=session.get("user_name"),
            user_role=session.get("user_role")
        )

    def get_shipment_details(self, shipment_id):
        """GET /api/agent/shipment-details/<id> — For interactive modals"""
        if "user_id" not in session or session.get("user_role") != "agent":
            return jsonify({"success": False, "message": "Unauthorized"}), 401
            
        shipment_obj = Shipment()
        row = shipment_obj.find_by_id(shipment_id)
        if not row:
            return jsonify({"success": False, "message": "Shipment record not found"}), 404
            
        return jsonify({"success": True, "data": row})

    def accept_delivery(self):
        """POST /api/agent/accept-delivery — Handles assignment tracking changes"""
        if "user_id" not in session or session.get("user_role") != "agent":
            return jsonify({"success": False, "message": "Unauthorized"}), 401
            
        data = request.get_json() or {}
        shipment_id = data.get("shipment_id")
        agent_id = session.get("user_id")
        
        if not shipment_id:
            return jsonify({"success": False, "message": "Missing shipment identification target"}), 400
            
        affected = Shipment.assign_agent_to_shipment(shipment_id, agent_id)
        if affected == 0:
            return jsonify({"success": False, "message": "Delivery assignment failed. It may have been taken by another agent."}), 400
            
        return jsonify({"success": True, "message": "Delivery successfully assigned to your route!"})