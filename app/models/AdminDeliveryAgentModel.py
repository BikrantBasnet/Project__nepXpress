from app.models.database import execute_query


class DeliveryAgentModel:
    """
    Delivery agent queries for the admin dashboard.
    UPDATED: delivery_agents table is retired - agents are now
    users with role='agent'. All queries below use the users
    table instead.
    """

    table = "users"

    @classmethod
    def get_top_agents(cls, limit=5):
        """Agents ranked by this-month deliveries, with performance %."""
        rows = execute_query(
            """
            SELECT
                a.id, a.name, a.status,
                COUNT(s.id) AS delivery_count
            FROM users a
            LEFT JOIN shipments s
                ON s.agent_id    = a.id
               AND s.status      = 'delivered'
               AND MONTH(s.created_at) = MONTH(CURDATE())
               AND YEAR(s.created_at)  = YEAR(CURDATE())
            WHERE a.role = 'agent'
            GROUP BY a.id, a.name, a.status
            ORDER BY delivery_count DESC
            LIMIT %s
            """,
            (limit,), fetchall=True
        )
        if not rows:
            return []
        max_count = rows[0]['delivery_count'] or 1
        for row in rows:
            row['performance_pct'] = round((row['delivery_count'] / max_count) * 100)
        return rows

    @classmethod
    def get_total_count(cls):
        result = execute_query(
            "SELECT COUNT(*) as cnt FROM users WHERE role = 'agent'", fetchone=True
        )
        return result['cnt'] if result else 0

    @classmethod
    def get_new_agents_this_month(cls):
        result = execute_query(
            """
            SELECT COUNT(*) as cnt FROM users
            WHERE role = 'agent'
              AND MONTH(created_at) = MONTH(CURDATE())
              AND YEAR(created_at)  = YEAR(CURDATE())
            """,
            fetchone=True
        )
        return result['cnt'] if result else 0