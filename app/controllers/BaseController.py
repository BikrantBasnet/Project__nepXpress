"""
=============================================================
  OOP Concept: INHERITANCE & ENCAPSULATION (Base Controller)
=============================================================
  Teammate's instance methods kept exactly as-is.
  Admin JSON response helpers added as static methods below —
  they don't overlap with anything the teammate wrote.
=============================================================
"""

from flask import session, flash, redirect, url_for, request, jsonify
from functools import wraps


class BaseController:
    """
    Base Controller — parent class for all controllers.

    Teammate's helpers:
      - get_form_data()       — safely read form inputs
      - is_logged_in()        — check if user is logged in
      - get_current_user_id() — get logged-in user's ID
      - get_current_role()    — get logged-in user's role
      - flash_and_redirect()  — show message and redirect

    Admin API helpers (new, static):
      - success()     — JSON 200 response
      - error()       — JSON 4xx/5xx response
      - not_found()   — JSON 404 response
    """

    # ── Teammate's instance methods (unchanged) ──────────────────────── #

    def get_form_data(self, *fields):
        """Safely get multiple form fields at once."""
        return tuple(request.form.get(field, "").strip() for field in fields)

    def is_logged_in(self):
        """Check if a user is currently logged in."""
        return "user_id" in session

    def get_current_user_id(self):
        """Get the logged-in user's ID from session."""
        return session.get("user_id")

    def get_current_role(self):
        """Get the logged-in user's role from session."""
        return session.get("role")

    def flash_and_redirect(self, message, category, endpoint):
        """Show a flash message and redirect to a page."""
        flash(message, category)
        return redirect(url_for(endpoint))

    # ── Admin JSON response helpers (new, static) ────────────────────── #

    @staticmethod
    def success(data=None, message="Success", status_code=200):
        response = {"success": True, "message": message}
        if data is not None:
            response["data"] = data
        return jsonify(response), status_code

    @staticmethod
    def error(message="An error occurred", status_code=400):
        return jsonify({"success": False, "message": message}), status_code

    @staticmethod
    def not_found(message="Resource not found"):
        return jsonify({"success": False, "message": message}), 404


# ── Admin session decorator ───────────────────────────────────────────────── #
# Separate from teammate's login_required (which uses user_id + flash + redirect).
# This one returns JSON 401 — for admin API routes only.

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Accept regular admin login OR API admin login
        is_api_admin = session.get('admin_logged_in')
        is_form_admin = session.get('user_id') and session.get('user_role') == 'admin'
        
        if not is_api_admin and not is_form_admin:
            return jsonify({"success": False, "message": "Unauthorized — admin login required"}), 401
        return f(*args, **kwargs)
    return decorated
