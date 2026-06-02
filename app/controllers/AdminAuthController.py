from flask import request, session
from app.controllers.BaseController import BaseController
from app.models.UserModel import User


class AdminAuthController(BaseController):
    """
    Admin-only JSON authentication.
    Completely separate from teammate's AuthController (template-based).

    Session keys used here:
        admin_logged_in  — boolean flag
        admin_id         — admin user id
        admin_name       — admin display name
        admin_role       — 'admin' or 'superadmin'

    These do NOT clash with teammate's session keys:
        user_id, user_name, user_email, user_role
    """

    @staticmethod
    def login():
        """
        POST /api/admin/login
        Body: { "email": "...", "password": "..." }
        """
        data = request.get_json(silent=True) or {}
        email    = (data.get('email') or '').strip()
        password = (data.get('password') or '').strip()

        if not email or not password:
            return AdminAuthController.error("Email and password are required", 400)

        user = User.admin_verify_login(email, password)
        if not user:
            return AdminAuthController.error("Invalid credentials or not an admin account", 401)

        session['admin_logged_in'] = True
        session['admin_id']        = user['id']
        session['admin_name']      = user['name']
        session['admin_role']      = user['role']
        session.permanent          = True

        return AdminAuthController.success(
            data={
                "id":    user['id'],
                "name":  user['name'],
                "email": user['email'],
                "role":  user['role'],
            },
            message="Admin login successful"
        )

    @staticmethod
    def logout():
        """POST /api/admin/logout — clears only admin session keys."""
        session.pop('admin_logged_in', None)
        session.pop('admin_id',        None)
        session.pop('admin_name',      None)
        session.pop('admin_role',      None)
        return AdminAuthController.success(message="Logged out successfully")

    @staticmethod
    def me():
        """GET /api/admin/me — returns current admin session info."""
        if not session.get('admin_logged_in'):
            return AdminAuthController.error("Not authenticated", 401)
        return AdminAuthController.success(data={
            "id":   session.get('admin_id'),
            "name": session.get('admin_name'),
            "role": session.get('admin_role'),
        })
    