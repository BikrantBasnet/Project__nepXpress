from flask import render_template, session, redirect, url_for
from app.controllers.BaseController import BaseController

class AgentController(BaseController):

    def dashboard(self):
        # Enforce that only logged-in users with the 'agent' role can see this page
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
            
        from app.models.ShipmentModel import Shipment
        agent_id = session.get("user_id")
        
        # Pull history rows from your live MySQL tables
        shipment_records = Shipment.get_history_for_agent(agent_id)
        
        return render_template(
            "agent-history.html", 
            history_records=shipment_records,
            user_name=session.get("user_name"),
            user_role=session.get("user_role")
        )