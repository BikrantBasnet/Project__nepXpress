from flask import render_template, session, redirect, url_for, request, jsonify
from app.controllers.BaseController import BaseController
from app.models.ShipmentModel import Shipment

class AgentController(BaseController):

    def dashboard(self):
        if "user_id" not in session or session.get("user_role") != "agent":
            return redirect(url_for("auth.login"))

        agent_id = session.get("user_id")
        stats = Shipment.get_agent_dashboard_stats(agent_id)
        active_deliveries = Shipment.get_active_for_agent(agent_id)

        return render_template(
            "agent-dashboard.html",
            user_name=session.get("user_name"),
            user_role=session.get("user_role"),
            stats=stats,
            active_deliveries=active_deliveries
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
    
    def shipment_management(self):
        """GET /agent-routes — renders active routes page"""
        if "user_id" not in session or session.get("user_role") != "agent":
            return redirect(url_for("auth.login"))

        agent_id = session.get("user_id")
        deliveries = Shipment.get_active_for_agent(agent_id)

        return render_template(
            "agent-routes.html",
            deliveries=deliveries,
            user_name=session.get("user_name"),
            user_role=session.get("user_role")
        )

    def update_status(self):
        """POST /api/agent/update-status"""
        if "user_id" not in session or session.get("user_role") != "agent":
            return jsonify({"success": False, "message": "Unauthorized"}), 401

        data        = request.get_json() or {}
        shipment_id = data.get("shipment_id")
        new_status  = data.get("status")

        VALID_KEYWORDS = ["picked", "transit", "out for delivery", "delivered"]

        if not shipment_id or not new_status:
            return jsonify({"success": False, "message": "Missing shipment_id or status"}), 400

        clean_status = new_status.strip().lower()
        if not any(keyword in clean_status for keyword in VALID_KEYWORDS):
            return jsonify({"success": False, "message": f"Invalid status value: {new_status}"}), 400

        agent_id = session.get("user_id")
        affected = Shipment.update_status(shipment_id, agent_id, new_status)
        if not affected:
            return jsonify({"success": False, "message": "Update failed — not your shipment or already closed"}), 400

        return jsonify({"success": True, "message": f"Status updated to {new_status}"})

    def fail_delivery(self):
        """POST /api/agent/fail-delivery"""
        if "user_id" not in session or session.get("user_role") != "agent":
            return jsonify({"success": False, "message": "Unauthorized"}), 401

        data        = request.get_json() or {}
        shipment_id = data.get("shipment_id")
        reason      = data.get("reason")
        agent_id    = session.get("user_id")

        if not shipment_id or not reason:
            return jsonify({"success": False, "message": "Missing shipment_id or reason"}), 400

        # reason is now saved as a note in the log
        new_attempts = Shipment.record_failed_attempt(shipment_id, agent_id, reason=reason)

        if new_attempts >= 3:
            Shipment.update_status(shipment_id, agent_id, "return_to_sender",
                                notes="Max attempts reached — returning to sender")
            return jsonify({
                "success": True, "attempts": new_attempts, "final": True,
                "message": "3 attempts reached — shipment marked for return to sender."
            })

        return jsonify({
            "success": True, "attempts": new_attempts, "final": False,
            "message": f"Failed attempt {new_attempts} of 3 recorded."
        })

    def settings(self):
        if "user_id" not in session or session.get("user_role") != "agent":
            return redirect(url_for("auth.login"))

        from app.models.UserModel import User  # or however your user model is named
        user = User().find_by_id(session.get("user_id"))

        if request.method == "POST":
            form_type = request.form.get("form_type")
            if form_type == "profile":
                # update name, phone, zone
                pass
            elif form_type == "password":
                # verify current, hash new, update
                pass
            return redirect(url_for("agent.settings"))

        return render_template(
            "agent-settings.html",
            user=user,
            user_name=session.get("user_name"),
            user_role=session.get("user_role")
        )