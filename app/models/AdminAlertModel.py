from app.models.database import execute_query


class AlertModel:
    """System alert queries for the admin dashboard."""

    table = "system_alerts"

    @classmethod
    def get_recent_alerts(cls, limit=10):
        return execute_query(
            """
            SELECT id, type, title, message, reference_id, is_read, created_at
            FROM system_alerts
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (limit,), fetchall=True
        )

    @classmethod
    def get_unread_count(cls):
        result = execute_query(
            "SELECT COUNT(*) as cnt FROM system_alerts WHERE is_read = 0",
            fetchone=True
        )
        return result['cnt'] if result else 0

    @classmethod
    def mark_as_read(cls, alert_id: int):
        return execute_query(
            "UPDATE system_alerts SET is_read = 1 WHERE id = %s", (alert_id,)
        )

    @classmethod
    def mark_all_read(cls):
        return execute_query("UPDATE system_alerts SET is_read = 1 WHERE is_read = 0")