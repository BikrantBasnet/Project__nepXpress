from app.controllers.BaseController import BaseController, admin_required
from app.models.database import execute_query


class AdminReportsController(BaseController):

    @staticmethod
    @admin_required
    def get_revenue_monthly():
        """GET /api/admin/reports/revenue-monthly"""
        try:
            rows = execute_query(
                "SELECT "
                "  DATE_FORMAT(created_at, '%%b %%Y') AS month, "
                "  DATE_FORMAT(created_at, '%%Y-%%m')  AS month_key, "
                "  COALESCE(SUM(amount), 0)             AS revenue, "
                "  COUNT(*)                             AS shipments "
                "FROM shipments "
                "WHERE status = 'delivered' "
                "  AND created_at >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH) "
                "GROUP BY month_key, month "
                "ORDER BY month_key ASC",
                fetchall=True
            )
            for r in rows:
                r['revenue'] = float(r['revenue'])
            return AdminReportsController.success(data=rows)
        except Exception as e:
            return AdminReportsController.error(str(e), 500)

    @staticmethod
    @admin_required
    def get_shipments_monthly():
        """GET /api/admin/reports/shipments-monthly"""
        try:
            rows = execute_query(
                "SELECT "
                "  DATE_FORMAT(created_at, '%%b %%Y') AS month, "
                "  DATE_FORMAT(created_at, '%%Y-%%m')  AS month_key, "
                "  status, "
                "  COUNT(*) AS count "
                "FROM shipments "
                "WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH) "
                "GROUP BY month_key, month, status "
                "ORDER BY month_key ASC",
                fetchall=True
            )
            return AdminReportsController.success(data=rows)
        except Exception as e:
            return AdminReportsController.error(str(e), 500)

    @staticmethod
    @admin_required
    def get_agent_performance():
        """
        GET /api/admin/reports/agent-performance
        UPDATED: agents are now users with role='agent' -
        delivery_agents table is retired.
        """
        try:
            rows = execute_query(
                "SELECT "
                "  a.name, "
                "  COUNT(s.id) AS total, "
                "  SUM(CASE WHEN s.status='delivered'  THEN 1 ELSE 0 END) AS delivered, "
                "  SUM(CASE WHEN s.status='delayed'    THEN 1 ELSE 0 END) AS `delayed`, "
                "  SUM(CASE WHEN s.status='in_transit' THEN 1 ELSE 0 END) AS in_transit, "
                "  COALESCE(SUM(s.amount), 0) AS revenue "
                "FROM users a "
                "LEFT JOIN shipments s ON s.agent_id = a.id "
                "WHERE a.role = 'agent' "
                "GROUP BY a.id, a.name "
                "ORDER BY delivered DESC",
                fetchall=True
            )
            for r in rows:
                r['revenue']     = float(r['revenue'])
                r['success_pct'] = round(
                    (r['delivered'] / r['total'] * 100) if r['total'] > 0 else 0, 1
                )
            return AdminReportsController.success(data=rows)
        except Exception as e:
            return AdminReportsController.error(str(e), 500)

    @staticmethod
    @admin_required
    def get_customer_activity():
        """GET /api/admin/reports/customer-activity"""
        try:
            rows = execute_query(
                "SELECT "
                "  u.name, "
                "  COUNT(s.id)                AS total_shipments, "
                "  COALESCE(SUM(s.amount), 0) AS total_spent, "
                "  MAX(s.created_at)           AS last_order "
                "FROM users u "
                "LEFT JOIN shipments s ON s.user_id = u.id "
                "WHERE u.role = 'customer' "
                "GROUP BY u.id, u.name "
                "ORDER BY total_shipments DESC "
                "LIMIT 8",
                fetchall=True
            )
            for r in rows:
                r['total_spent'] = float(r['total_spent'])
                r['last_order']  = str(r['last_order']) if r.get('last_order') else None
            return AdminReportsController.success(data=rows)
        except Exception as e:
            return AdminReportsController.error(str(e), 500)

    @staticmethod
    @admin_required
    def get_summary():
        """GET /api/admin/reports/summary"""
        try:
            total_rev  = execute_query(
                "SELECT COALESCE(SUM(amount),0) as v FROM shipments WHERE status='delivered'",
                fetchone=True
            )['v']
            total_ship = execute_query(
                "SELECT COUNT(*) as v FROM shipments",
                fetchone=True
            )['v']
            total_users= execute_query(
                "SELECT COUNT(*) as v FROM users WHERE role='customer'",
                fetchone=True
            )['v']
            avg_order  = execute_query(
                "SELECT COALESCE(AVG(amount),0) as v FROM shipments WHERE status='delivered'",
                fetchone=True
            )['v']
            return AdminReportsController.success(data={
                "total_revenue":   float(total_rev),
                "total_shipments": total_ship,
                "total_customers": total_users,
                "avg_order_value": float(avg_order)
            })
        except Exception as e:
            return AdminReportsController.error(str(e), 500)