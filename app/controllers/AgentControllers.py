
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
        if "user_id" not in session or session.get("user_role") != "agent":
            return redirect(url_for("auth.login"))
        live_requests = Shipment.get_available_deliveries()
        return render_template(
            "agent-deliveries.html",
            requests=live_requests,
            user_name=session.get("user_name"),
            user_role=session.get("user_role")
        )

    def get_shipment_details(self, shipment_id):
        if "user_id" not in session or session.get("user_role") != "agent":
            return jsonify({"success": False, "message": "Unauthorized"}), 401
        shipment_obj = Shipment()
        row = shipment_obj.find_by_id(shipment_id)
        if not row:
            return jsonify({"success": False, "message": "Shipment record not found"}), 404
        return jsonify({"success": True, "data": row})

    def accept_delivery(self):
        if "user_id" not in session or session.get("user_role") != "agent":
            return jsonify({"success": False, "message": "Unauthorized"}), 401
        data = request.get_json() or {}
        shipment_id = data.get("shipment_id")
        agent_id = session.get("user_id")
        if not shipment_id:
            return jsonify({"success": False, "message": "Missing shipment_id"}), 400
        affected = Shipment.assign_agent_to_shipment(shipment_id, agent_id)
        if affected == 0:
            return jsonify({"success": False, "message": "Assignment failed — already taken."}), 400
        return jsonify({"success": True, "message": "Delivery assigned to your route!"})

    def shipment_management(self):
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
        """POST /api/agent/update-status
        Valid transitions from in_transit: Delivered, Cancelled, Delayed
        Delayed can also go back to In Transit (agent retries).
        """
        if "user_id" not in session or session.get("user_role") != "agent":
            return jsonify({"success": False, "message": "Unauthorized"}), 401

        data        = request.get_json() or {}
        shipment_id = data.get("shipment_id")
        new_status  = data.get("status")
        notes       = data.get("notes")

        VALID_STATUSES = ["In Transit", "Delivered", "Delayed", "Cancelled"]

        if not shipment_id or not new_status:
            return jsonify({"success": False, "message": "Missing shipment_id or status"}), 400
        if new_status not in VALID_STATUSES:
            return jsonify({"success": False, "message": f"Invalid status: {new_status}"}), 400

        agent_id = session.get("user_id")
        Shipment.update_status(shipment_id, agent_id, new_status, notes=notes)
        return jsonify({"success": True, "message": f"Status updated to {new_status}"})

    def fail_delivery(self):
        """POST /api/agent/fail-delivery — kept for backward compat but not used in new flow"""
        if "user_id" not in session or session.get("user_role") != "agent":
            return jsonify({"success": False, "message": "Unauthorized"}), 401
        data        = request.get_json() or {}
        shipment_id = data.get("shipment_id")
        reason      = data.get("reason")
        agent_id    = session.get("user_id")
        if not shipment_id or not reason:
            return jsonify({"success": False, "message": "Missing shipment_id or reason"}), 400
        new_attempts = Shipment.record_failed_attempt(shipment_id, agent_id, reason=reason)
        return jsonify({
            "success": True, "attempts": new_attempts,
            "message": f"Failed attempt {new_attempts} recorded."
        })

    def settings(self):
        if "user_id" not in session or session.get("user_role") != "agent":
            return redirect(url_for("auth.login"))
        from app.models.UserModel import User
        user = User().find_by_id(session.get("user_id"))
        if request.method == "POST":
            form_type = request.form.get("form_type")
            if form_type == "profile":
                pass
            elif form_type == "password":
                pass
            return redirect(url_for("agent.settings"))
        return render_template(
            "agent-settings.html",
            user=user,
            user_name=session.get("user_name"),
            user_role=session.get("user_role")
        )