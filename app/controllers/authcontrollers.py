from flask import render_template
class AuthController:
 
    def login(self):
        return render_template('login.html')
    
    def register(self):
        return render_template('register-page.html')
    
    def dashboard(self):
        return render_template('dashboard.html')
    
    def admin_dashboard(self):
        return render_template('admin-dashboard.html')
    
    def create_shipment(self):
        return render_template('create-shipment.html')
    
    def shipment_history(self):
        return render_template('shipment-history.html')
     
    def settings(self):
        return render_template('settings.html')
    
    def base(self):
        return render_template('base.html')

    
 
