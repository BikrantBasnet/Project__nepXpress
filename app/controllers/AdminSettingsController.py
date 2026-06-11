from flask import request, session
from app.controllers.BaseController import BaseController, admin_required
from app.models.database import execute_query
from werkzeug.security import generate_password_hash, check_password_hash


class AdminSettingsController(BaseController):

    @staticmethod
    @admin_required
    def get_profile():
        """GET /api/admin/settings/profile"""
        try:
            uid = session.get('user_id') or session.get('admin_id')
            user = execute_query(
                "SELECT id, name, email, role FROM users WHERE id = %s",
                (uid,), fetchone=True
            )
            if not user:
                return AdminSettingsController.not_found("Admin not found")
            return AdminSettingsController.success(data=user)
        except Exception as e:
            return AdminSettingsController.error(str(e), 500)

    @staticmethod
    @admin_required
    def update_profile():
        """PATCH /api/admin/settings/profile"""
        try:
            uid  = session.get('user_id') or session.get('admin_id')
            data = request.get_json(silent=True) or {}
            name  = (data.get('name') or '').strip()
            email = (data.get('email') or '').strip()
            if not name or not email:
                return AdminSettingsController.error("Name and email are required", 400)

            # Check email not taken by another user
            existing = execute_query(
                "SELECT id FROM users WHERE email = %s AND id != %s",
                (email, uid), fetchone=True
            )
            if existing:
                return AdminSettingsController.error("Email already in use", 400)

            execute_query(
                "UPDATE users SET name = %s, email = %s WHERE id = %s",
                (name, email, uid)
            )
            session['user_name']  = name
            session['admin_name'] = name
            return AdminSettingsController.success(message="Profile updated successfully")
        except Exception as e:
            return AdminSettingsController.error(str(e), 500)

    @staticmethod
    @admin_required
    def update_password():
        """PATCH /api/admin/settings/password"""
        try:
            uid  = session.get('user_id') or session.get('admin_id')
            data = request.get_json(silent=True) or {}
            current = (data.get('current_password') or '').strip()
            new_pw  = (data.get('new_password') or '').strip()
            confirm = (data.get('confirm_password') or '').strip()

            if not current or not new_pw or not confirm:
                return AdminSettingsController.error("All password fields are required", 400)
            if new_pw != confirm:
                return AdminSettingsController.error("New passwords do not match", 400)
            if len(new_pw) < 6:
                return AdminSettingsController.error("Password must be at least 6 characters", 400)

            row = execute_query(
                "SELECT password FROM users WHERE id = %s", (uid,), fetchone=True
            )
            if not row or not check_password_hash(row['password'], current):
                return AdminSettingsController.error("Current password is incorrect", 400)

            execute_query(
                "UPDATE users SET password = %s WHERE id = %s",
                (generate_password_hash(new_pw), uid)
            )
            return AdminSettingsController.success(message="Password updated successfully")
        except Exception as e:
            return AdminSettingsController.error(str(e), 500)

    @staticmethod
    @admin_required
    def get_system():
        """GET /api/admin/settings/system"""
        try:
            rows = execute_query(
                "SELECT setting_key, setting_value FROM system_settings",
                fetchall=True
            )
            # Convert to dict
            settings = {r['setting_key']: r['setting_value'] for r in rows}
            return AdminSettingsController.success(data=settings)
        except Exception as e:
            # Table might not exist yet
            return AdminSettingsController.success(data={
                "site_name":      "NepXpress",
                "contact_email":  "admin@nepxpress.com",
                "currency":       "NPR",
                "support_phone":  "",
                "address":        ""
            })

    @staticmethod
    @admin_required
    def update_system():
        """PATCH /api/admin/settings/system"""
        try:
            data = request.get_json(silent=True) or {}
            allowed = ['site_name', 'contact_email', 'currency', 'support_phone', 'address']
            for key in allowed:
                if key in data:
                    execute_query(
                        "INSERT INTO system_settings (setting_key, setting_value) "
                        "VALUES (%s, %s) "
                        "ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value)",
                        (key, data[key])
                    )
            return AdminSettingsController.success(message="System settings saved")
        except Exception as e:
            return AdminSettingsController.error(str(e), 500)

    @staticmethod
    @admin_required
    def get_notifications():
        """GET /api/admin/settings/notifications"""
        try:
            rows = execute_query(
                "SELECT setting_key, setting_value FROM system_settings "
                "WHERE setting_key LIKE 'notif_%%'",
                fetchall=True
            )
            defaults = {
                "notif_delay":       "1",
                "notif_new_user":    "1",
                "notif_payment":     "1",
                "notif_agent_offline":"1",
                "notif_new_shipment":"0",
            }
            for r in rows:
                defaults[r['setting_key']] = r['setting_value']
            return AdminSettingsController.success(data=defaults)
        except Exception as e:
            return AdminSettingsController.success(data={
                "notif_delay":        "1",
                "notif_new_user":     "1",
                "notif_payment":      "1",
                "notif_agent_offline":"1",
                "notif_new_shipment": "0",
            })

    @staticmethod
    @admin_required
    def update_notifications():
        """PATCH /api/admin/settings/notifications"""
        try:
            data = request.get_json(silent=True) or {}
            allowed = [
                'notif_delay', 'notif_new_user', 'notif_payment',
                'notif_agent_offline', 'notif_new_shipment'
            ]
            for key in allowed:
                if key in data:
                    execute_query(
                        "INSERT INTO system_settings (setting_key, setting_value) "
                        "VALUES (%s, %s) "
                        "ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value)",
                        (key, str(data[key]))
                    )
            return AdminSettingsController.success(message="Notification settings saved")
        except Exception as e:
            return AdminSettingsController.error(str(e), 500)