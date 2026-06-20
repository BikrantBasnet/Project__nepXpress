from flask import request
from app.controllers.BaseController import BaseController, admin_required
from app.models.database import execute_query


class AdminAgentController(BaseController):
    """
    Delivery agents are now just users with role='agent'.
    The standalone delivery_agents table is retired -
    shipments.agent_id references users.id directly.
    """

    @staticmethod
    @admin_required
    def get_all():
        """GET /api/admin/delivery-agents?page=1&limit=10&status=&search="""
        try:
            page   = int(request.args.get('page', 1))
            limit  = int(request.args.get('limit', 10))
            status = request.args.get('status', '').strip() or None
            search = request.args.get('search', '').strip() or None
            offset = (page - 1) * limit

            conditions = ["a.role = 'agent'"]
            params = []
            if status:
                conditions.append("a.status = %s")
                params.append(status)
            if search:
                conditions.append("(a.name LIKE %s OR a.email LIKE %s)")
                like = f"%{search}%"
                params.extend([like, like])

            where = "WHERE " + " AND ".join(conditions)

            total = execute_query(
                f"SELECT COUNT(*) as cnt FROM users a {where}",
                params, fetchone=True
            )['cnt']

            rows = execute_query(
                f"""SELECT
                        a.id, a.name, a.email, a.phone, a.status,
                        a.created_at,
                        COUNT(s.id)                                          AS total_deliveries,
                        SUM(CASE WHEN s.status='delivered' THEN 1 ELSE 0 END) AS completed,
                        SUM(CASE WHEN s.status='delayed'   THEN 1 ELSE 0 END) AS `delayed`
                    FROM users a
                    LEFT JOIN shipments s ON s.agent_id = a.id
                    {where}
                    GROUP BY a.id
                    ORDER BY a.created_at DESC
                    LIMIT %s OFFSET %s""",
                params + [limit, offset], fetchall=True
            )
            for r in rows:
                r['created_at'] = str(r['created_at']) if r.get('created_at') else None
                r['zone'] = ''  # no zone column on users; keep key for frontend compatibility

            return AdminAgentController.success(data={
                "agents": rows,
                "pagination": {
                    "total":       total,
                    "page":        page,
                    "limit":       limit,
                    "total_pages": -(-total // limit)
                }
            })
        except Exception as e:
            return AdminAgentController.error(str(e), 500)

    @staticmethod
    @admin_required
    def get_one(agent_id: int):
        """GET /api/admin/delivery-agents/<id>"""
        try:
            agent = execute_query(
                """SELECT a.id, a.name, a.email, a.phone, a.status, a.created_at,
                          COUNT(s.id) AS total_deliveries,
                          SUM(CASE WHEN s.status='delivered'  THEN 1 ELSE 0 END) AS completed,
                          SUM(CASE WHEN s.status='delayed'    THEN 1 ELSE 0 END) AS `delayed`,
                          SUM(CASE WHEN s.status='in_transit' THEN 1 ELSE 0 END) AS in_transit
                   FROM users a
                   LEFT JOIN shipments s ON s.agent_id = a.id
                   WHERE a.id = %s AND a.role = 'agent'
                   GROUP BY a.id""",
                (agent_id,), fetchone=True
            )
            if not agent:
                return AdminAgentController.not_found("Agent not found")
            agent['created_at'] = str(agent['created_at']) if agent.get('created_at') else None
            agent['zone'] = ''

            shipments = execute_query(
                """SELECT s.tracking_id, u.name AS customer_name,
                          s.destination, s.status, s.amount, s.created_at
                   FROM shipments s
                   LEFT JOIN users u ON s.user_id = u.id
                   WHERE s.agent_id = %s
                   ORDER BY s.created_at DESC LIMIT 6""",
                (agent_id,), fetchall=True
            )
            for s in shipments:
                s['created_at'] = str(s['created_at']) if s.get('created_at') else None

            return AdminAgentController.success(data={
                "agent":     agent,
                "shipments": shipments
            })
        except Exception as e:
            return AdminAgentController.error(str(e), 500)

    @staticmethod
    @admin_required
    def create():
        """POST /api/admin/delivery-agents - creates a new user with role=agent"""
        try:
            from werkzeug.security import generate_password_hash
            data = request.get_json(silent=True) or {}
            for field in ['name', 'email']:
                if not data.get(field):
                    return AdminAgentController.error(f"Missing required field: {field}", 400)

            existing = execute_query(
                "SELECT id FROM users WHERE email = %s", (data['email'],), fetchone=True
            )
            if existing:
                return AdminAgentController.error("Email already registered", 400)

            temp_password = generate_password_hash(data.get('password', 'agent123'))

            new_id = execute_query(
                "INSERT INTO users (name, email, phone, role, status, password) "
                "VALUES (%s,%s,%s,'agent',%s,%s)",
                (
                    data['name'].strip(),
                    data['email'].strip(),
                    data.get('phone', '').strip(),
                    data.get('status', 'active'),
                    temp_password
                )
            )
            return AdminAgentController.success(
                data={"id": new_id},
                message="Agent created successfully",
                status_code=201
            )
        except Exception as e:
            return AdminAgentController.error(str(e), 500)

    @staticmethod
    @admin_required
    def update(agent_id: int):
        """PUT /api/admin/delivery-agents/<id>"""
        try:
            data = request.get_json(silent=True) or {}
            fields, params = [], []
            for col in ['name', 'email', 'phone','status']:
                if col in data:
                    fields.append(f"{col} = %s")
                    params.append(data[col].strip())
            if not fields:
                return AdminAgentController.error("No fields to update", 400)
            params.append(agent_id)
            execute_query(
                f"UPDATE users SET {', '.join(fields)} WHERE id = %s AND role = 'agent'", params
            )
            return AdminAgentController.success(message="Agent updated successfully")
        except Exception as e:
            return AdminAgentController.error(str(e), 500)

    @staticmethod
    @admin_required
    def update_status(agent_id: int):
        """PATCH /api/admin/delivery-agents/<id>/status"""
        try:
            data   = request.get_json(silent=True) or {}
            status = (data.get('status') or '').strip()
            if status not in ('active', 'inactive', 'offline'):
                return AdminAgentController.error("Status must be active, inactive or offline", 400)
            affected = execute_query(
                "UPDATE users SET status = %s WHERE id = %s AND role = 'agent'", (status, agent_id)
            )
            if not affected:
                return AdminAgentController.not_found("Agent not found")
            return AdminAgentController.success(message=f"Status updated to '{status}'")
        except Exception as e:
            return AdminAgentController.error(str(e), 500)

    @staticmethod
    @admin_required
    def delete(agent_id: int):
        """DELETE /api/admin/delivery-agents/<id>"""
        try:
            execute_query(
                "UPDATE shipments SET agent_id = NULL WHERE agent_id = %s", (agent_id,)
            )
            affected = execute_query(
                "DELETE FROM users WHERE id = %s AND role = 'agent'", (agent_id,)
            )
            if not affected:
                return AdminAgentController.not_found("Agent not found")
            return AdminAgentController.success(message="Agent deleted successfully")
        except Exception as e:
            return AdminAgentController.error(str(e), 500)

    @staticmethod
    @admin_required
    def get_stats():
        """GET /api/admin/delivery-agents/stats"""
        try:
            total    = execute_query("SELECT COUNT(*) as cnt FROM users WHERE role='agent'", fetchone=True)['cnt']
            active   = execute_query("SELECT COUNT(*) as cnt FROM users WHERE role='agent' AND status='active'",   fetchone=True)['cnt']
            offline  = execute_query("SELECT COUNT(*) as cnt FROM users WHERE role='agent' AND status='offline'",  fetchone=True)['cnt']
            inactive = execute_query("SELECT COUNT(*) as cnt FROM users WHERE role='agent' AND status='inactive'", fetchone=True)['cnt']
            new_month = execute_query(
                """SELECT COUNT(*) as cnt FROM users
                   WHERE role='agent' AND MONTH(created_at)=MONTH(CURDATE()) AND YEAR(created_at)=YEAR(CURDATE())""",
                fetchone=True
            )['cnt']
            total_deliveries = execute_query(
                "SELECT COUNT(*) as cnt FROM shipments WHERE status='delivered'", fetchone=True
            )['cnt']
            return AdminAgentController.success(data={
                "total": total, "active": active, "offline": offline,
                "inactive": inactive, "new_this_month": new_month,
                "total_deliveries": total_deliveries
            })
        except Exception as e:
            return AdminAgentController.error(str(e), 500)