from flask import Flask, render_template
from app.routes.authroutes import Authroutes
from app.models.database import Database
import config


def create_app():
    app = Flask(__name__)
    app.secret_key = config.SECRET_KEY
    with app.app_context():
        Database.create_tables()  # Static method — called on the class, not an object
    auth_routes = Authroutes()
    app.register_blueprint(auth_routes.login())

    @app.route("/")
    def home():
        return render_template("home.html")
    
    @app.route("/register")
    def register():
        return render_template("register.html")

    @app.route("/login")
    def login():
        return render_template("login.html")
    
    @app.route("/dashboard")
    def dashboard():
        return render_template("dashboard.html")
    
    @app.route("/admin-dashboard")
    def admin_dashboard():
        return render_template("admin-dashboard.html")
    
    @app.route("/create-shipment")
    def create_shipment():
        return render_template("create-shipment.html")
    
    @app.route("/shipment-history")
    def shipment_history():
        return render_template("shipment-history.html")

    @app.route("/settings")
    def settings():
        return render_template("settings.html")

    @app.route("/base")
    def base():
        return render_template("base.html")

 
    @app.errorhandler(404)
    def error(e):
        return render_template("error.html")
    
   
    return app

