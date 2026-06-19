from flask import Flask, app, render_template, session, redirect, url_for, flash, request, get_flashed_messages, make_response
from app.controllers.AgentControllers import AgentController
from app.routes.authroutes import Authroutes
from app.routes.UserRoutes import UserRoutes
from app.models.database import Database
import config
import os


def create_app():

    app_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(app_dir)

    template_folder = os.path.join(project_root, 'templates')
    static_folder   = os.path.join(project_root, 'static')

    app = Flask(
        __name__,
        template_folder=template_folder,
        static_folder=static_folder
    )

    app.secret_key = config.SECRET_KEY

    with app.app_context():
        Database.create_tables()

    # ── Auth blueprint ─────────────────────────────────────────────────── #
    auth_routes = Authroutes()
    app.register_blueprint(auth_routes.login())

    # ── User pages blueprint ───────────────────────────────────────────── #
    user_routes = UserRoutes()
    app.register_blueprint(user_routes.register())

    # ── Admin API blueprint ────────────────────────────────────────────── #
    from app.routes.admin import admin_bp
    app.register_blueprint(admin_bp)

    # ── Agent blueprint ────────────────────────────────────────────────── #
    from app.routes.AgentRoutes import AgentRoutes
    agent_routes = AgentRoutes()
    app.register_blueprint(agent_routes.register_routes())

    # ── ADMIN PAGES (teammates' — left inline) ─────────────────────────── #

    @app.route("/admin-dashboard")
    def admin_dashboard():
        if not session.get("user_id") and not session.get("admin_logged_in"):
            return redirect(url_for("auth.login"))
        get_flashed_messages()
        return render_template(
            "admin-dashboard.html",
            user_name=session.get("user_name") or session.get("admin_name"),
            user_role=session.get("user_role") or session.get("admin_role")
        )

    @app.route("/admin-shipments")
    def admin_shipments():
        if not session.get("user_id") and not session.get("admin_logged_in"):
            return redirect(url_for("auth.login"))
        get_flashed_messages()
        return render_template(
            "admin-shipments.html",
            user_name=session.get("user_name") or session.get("admin_name"),
            user_role=session.get("user_role") or session.get("admin_role")
        )

    @app.route("/admin-users")
    def admin_users():
        if not session.get("user_id") and not session.get("admin_logged_in"):
            return redirect(url_for("auth.login"))
        get_flashed_messages()
        return render_template(
            "admin-users.html",
            user_name=session.get("user_name") or session.get("admin_name"),
            user_role=session.get("user_role") or session.get("admin_role")
        )

    @app.route("/admin-reports")
    def admin_reports():
        if not session.get("user_id") and not session.get("admin_logged_in"):
            return redirect(url_for("auth.login"))
        get_flashed_messages()
        return render_template(
            "admin-reports.html",
            user_name=session.get("user_name") or session.get("admin_name"),
            user_role=session.get("user_role") or session.get("admin_role")
        )

    @app.route("/admin-settings")
    def admin_settings():
        if not session.get("user_id") and not session.get("admin_logged_in"):
            return redirect(url_for("auth.login"))
        get_flashed_messages()
        return render_template(
            "admin-settings.html",
            user_name=session.get("user_name") or session.get("admin_name"),
            user_role=session.get("user_role") or session.get("admin_role")
        )

    @app.route("/admin-agents")
    def admin_agents():
        if not session.get("user_id") and not session.get("admin_logged_in"):
            return redirect(url_for("auth.login"))
        get_flashed_messages()
        return render_template(
            "admin-agents.html",
            user_name=session.get("user_name") or session.get("admin_name"),
            user_role=session.get("user_role") or session.get("admin_role")
        )

    # ── Error handler ──────────────────────────────────────────────────── #
    @app.errorhandler(404)
    def error(e):
        return render_template("error.html"), 404

    # ── Debug helper ───────────────────────────────────────────────────── #
    @app.route("/debug-session")
    def debug_session():
        from flask import current_app
        rules = {str(r): r.endpoint for r in current_app.url_map.iter_rules()}
        return {"session": dict(session), "routes": rules}

    return app