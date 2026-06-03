from flask import request
from app.controllers.BaseController import BaseController, admin_required
from app.models.database import execute_query


class AdminUserController(BaseController):

    @staticmethod
    @admin_required
    def get_all():
        """GET /api/admin/users?page=1&limit=10&role=&status=&search="""
        try:
            page   = int(request.args.get('page', 1))
            limit  = int(request.args.get('limit', 10))
            role   = request.args.get('role', '').strip() or None
            status = request.args.get('status', '').strip() or None
            search = request.args.get('search', '').strip() or None
            offset = (page - 1) * limit

            conditions, params = [], []
            if role:
                conditions.append("role = %s")
                params.append(role)
            if status:
                conditions.append("status = %s")
                params.append(status)
            if search:
                conditions.append("(name LIKE %s OR email LIKE %s)")
                like = f"%{search}%"
                params.extend([like, like])

            where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

            total = execute_query(
                f"SELECT COUNT(*) as cnt FROM users {where}",
                params, fetchone=True
            )['cnt']

            rows = execute_query(
                f"""SELECT id, name, email, role, status, created_at
                    FROM users {where}
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s""",
                params + [limit, offset], fetchall=True
            )
            for r in rows:
                r['created_at'] = str(r['created_at']) if r.get('created_at') else None

            return AdminUserController.success(data={
                "users": rows,
                "pagination": {
                    "total":       total,
                    "page":        page,
                    "limit":       limit,
                    "total_pages": -(-total // limit)
                }
            })
        except Exception as e:
            return AdminUserController.error(str(e), 500)

    @staticmethod
    @admin_required
    def get_one(user_id: int):
        """GET /api/admin/users/<id>"""
        try:
            user = execute_query(
                "SELECT id, name, email, role, status, created_at FROM users WHERE id = %s",
                (user_id,), fetchone=True
            )
            if not user:
                return AdminUserController.not_found("User not found")
            user['created_at'] = str(user['created_at']) if user.get('created_at') else None

            # Get their shipment stats
            stats = execute_query(
                """SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status='delivered'  THEN 1 ELSE 0 END) as delivered,
                    SUM(CASE WHEN status='pending'    THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status='in_transit' THEN 1 ELSE 0 END) as in_transit,
                    SUM(CASE WHEN status='delayed'    THEN 1 ELSE 0 END) as delayed,
                    COALESCE(SUM(amount), 0) as total_spent
                FROM shipments WHERE customer_id = %s""",
                (user_id,), fetchone=True
            )

            # Get recent shipments
            shipments = execute_query(
                """SELECT tracking_id, destination, status, amount, created_at
                   FROM shipments WHERE customer_id = %s
                   ORDER BY created_at DESC LIMIT 5""",
                (user_id,), fetchall=True
            )
            for s in shipments:
                s['created_at'] = str(s['created_at']) if s.get('created_at') else None

            return AdminUserController.success(data={
                "user":      user,
                "stats":     stats,
                "shipments": shipments
            })
        except Exception as e:
            return AdminUserController.error(str(e), 500)

    @staticmethod
    @admin_required
    def update_status(user_id: int):
        """PATCH /api/admin/users/<id>/status — body: { "status": "active" }"""
        try:
            data   = request.get_json(silent=True) or {}
            status = (data.get('status') or '').strip()
            if status not in ('active', 'inactive'):
                return AdminUserController.error("Status must be 'active' or 'inactive'", 400)

            # Prevent deactivating own account
            from flask import session
            if session.get('user_id') == user_id or session.get('admin_id') == user_id:
                return AdminUserController.error("You cannot deactivate your own account", 400)

            affected = execute_query(
                "UPDATE users SET status = %s WHERE id = %s",
                (status, user_id)
            )
            if not affected:
                return AdminUserController.not_found("User not found")
            return AdminUserController.success(message=f"User status updated to '{status}'")
        except Exception as e:
            return AdminUserController.error(str(e), 500)

    @staticmethod
    @admin_required
    def update_role(user_id: int):
        """PATCH /api/admin/users/<id>/role — body: { "role": "admin" }"""
        try:
            data = request.get_json(silent=True) or {}
            role = (data.get('role') or '').strip()
            if role not in ('customer', 'admin'):
                return AdminUserController.error("Role must be 'customer' or 'admin'", 400)

            from flask import session
            if session.get('user_id') == user_id or session.get('admin_id') == user_id:
                return AdminUserController.error("You cannot change your own role", 400)

            affected = execute_query(
                "UPDATE users SET role = %s WHERE id = %s",
                (role, user_id)
            )
            if not affected:
                return AdminUserController.not_found("User not found")
            return AdminUserController.success(message=f"User role updated to '{role}'")
        except Exception as e:
            return AdminUserController.error(str(e), 500)

    @staticmethod
    @admin_required
    def delete(user_id: int):
        """DELETE /api/admin/users/<id>"""
        try:
            from flask import session
            if session.get('user_id') == user_id or session.get('admin_id') == user_id:
                return AdminUserController.error("You cannot delete your own account", 400)

            affected = execute_query(
                "DELETE FROM users WHERE id = %s", (user_id,)
            )
            if not affected:
                return AdminUserController.not_found("User not found")
            return AdminUserController.success(message="User deleted successfully")
        except Exception as e:
            return AdminUserController.error(str(e), 500)

    @staticmethod
    @admin_required
    def get_stats():
        """GET /api/admin/users/stats"""
        try:
            total    = execute_query("SELECT COUNT(*) as cnt FROM users", fetchone=True)['cnt']
            active   = execute_query("SELECT COUNT(*) as cnt FROM users WHERE status='active'", fetchone=True)['cnt']
            inactive = execute_query("SELECT COUNT(*) as cnt FROM users WHERE status='inactive'", fetchone=True)['cnt']
            admins   = execute_query("SELECT COUNT(*) as cnt FROM users WHERE role='admin'", fetchone=True)['cnt']
            customers= execute_query("SELECT COUNT(*) as cnt FROM users WHERE role='customer'", fetchone=True)['cnt']
            new_this_month = execute_query(
                """SELECT COUNT(*) as cnt FROM users
                   WHERE MONTH(created_at)=MONTH(CURDATE())
                   AND YEAR(created_at)=YEAR(CURDATE())""",
                fetchone=True
            )['cnt']
            return AdminUserController.success(data={
                "total": total, "active": active, "inactive": inactive,
                "admins": admins, "customers": customers,
                "new_this_month": new_this_month
            })
        except Exception as e:
            return AdminUserController.error(str(e), 500)
