from flask import Flask, render_template, session, redirect, url_for
from app.routes.authroutes import Authroutes
from app.models.database import Database
import config
import os


def create_app():
    # Method 1: Try using the module's directory
    app_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(app_dir)
    
    template_folder = os.path.join(project_root, 'templates')
    static_folder = os.path.join(project_root, 'static')
    
    # Debug: Print the paths
    print(f"📁 App directory: {app_dir}")
    print(f"📁 Project root: {project_root}")
    print(f"📁 Template folder: {template_folder}")
    print(f"📁 Template exists: {os.path.exists(template_folder)}")
    
    # Create Flask app
    app = Flask(
        __name__,
        template_folder=template_folder,
        static_folder=static_folder
    )
    
    # Set secret key for session management
    app.secret_key = config.SECRET_KEY
    
    # Create database tables on app startup
    with app.app_context():
        Database.create_tables()
    
    # Register authentication routes (login, register, settings)
    auth_routes = Authroutes()
    app.register_blueprint(auth_routes.login())

    
    # ========== PUBLIC ROUTES (No authentication required) ==========
    
    @app.route("/")
    def home():
        """Home page - redirects to login"""
        return render_template("login.html")
    
    
    # ========== PROTECTED ROUTES (Require login) ==========
    
    @app.route("/dashboard")
    def dashboard():
        """User dashboard - requires login"""
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return render_template("dashboard.html")
    
    
    @app.route("/create-shipment")
    def create_shipment():
        """Create shipment page - requires login"""
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return render_template("create-shipment.html")
    
    
    @app.route("/shipment-history")
    def shipment_history():
        """Shipment history page - requires login"""
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return render_template("shipment-history.html")

    
    @app.route("/settings")
    def settings():
        """Settings page - requires login"""
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return render_template("settings.html")

    
    @app.route("/admin-dashboard")
    def admin_dashboard():
        """Admin dashboard - requires login AND admin role"""
        if "user_id" not in session or session.get("user_role") != "admin":
            return redirect(url_for("auth.login"))
        return render_template("admin-dashboard.html")

    
    # ========== LOGOUT ROUTE ==========
    
    @app.route("/logout")
    def logout():
        """Clear session and redirect to login"""
        session.clear()
        return redirect(url_for("auth.login"))

   
    # ========== ERROR HANDLERS ==========
    
    @app.errorhandler(404)
    def error(e):
        """Handle 404 errors"""
        return render_template("error.html"), 404
    
    
    return app