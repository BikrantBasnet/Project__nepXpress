from app.models.database import execute_query


class ShipmentModel:
    """
    Shipment model — standalone class (no BaseModel needed here
    because shipment queries are too JOIN-heavy for generic helpers).
    """

    table = "shipments"

    # ── Dashboard – Recent Shipments ─────────────────────────────────── #

    @classmethod
    def admin_create(cls, data: dict):
        import time, random
        while True:
            suffix = random.randint(100, 999)
            tracking_id = f"NXP-{int(time.time()) % 100000}{suffix}"
            existing = execute_query(
            "SELECT id FROM shipments WHERE tracking_id = %s",
            (tracking_id,), fetchone=True
        )
            if not existing:
                break

        new_id = execute_query(
            "INSERT INTO shipments (tracking_id, customer_id, agent_id, destination, status, amount, notes) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (
            tracking_id,
            data['customer_id'],
            data.get('agent_id'),
            data['destination'],
            data.get('status', 'pending'),
            data['amount'],
            data.get('notes', '')
        )
    )
        return new_id, tracking_id


    @classmethod
    def get_recent_shipments(cls, limit=10):
        sql = """
            SELECT
                s.id,
                s.tracking_id,
                u.name        AS customer_name,
                a.name        AS agent_name,
                s.destination,
                s.status,
                s.amount,
                s.created_at
            FROM shipments s
            LEFT JOIN users           u ON s.customer_id = u.id
            LEFT JOIN delivery_agents a ON s.agent_id    = a.id
            ORDER BY s.created_at DESC
            LIMIT %s
        """
        return execute_query(sql, (limit,), fetchall=True)

    # ── Dashboard – KPI counts ───────────────────────────────────────── #

    @classmethod
    def get_total_count(cls):
        result = execute_query("SELECT COUNT(*) as cnt FROM shipments", fetchone=True)
        return result['cnt'] if result else 0

    @classmethod
    def get_count_by_status(cls, status: str):
        result = execute_query(
            "SELECT COUNT(*) as cnt FROM shipments WHERE status = %s",
            (status,), fetchone=True
        )
        return result['cnt'] if result else 0

    @classmethod
    def get_status_breakdown(cls):
        """All-time breakdown for the pie/donut chart."""
        rows = execute_query(
            "SELECT status, COUNT(*) as cnt FROM shipments GROUP BY status",
            fetchall=True
        )
        total = sum(r['cnt'] for r in rows) or 1
        return [
            {
                "status":     r['status'],
                "count":      r['cnt'],
                "percentage": round((r['cnt'] / total) * 100, 1)
            }
            for r in rows
        ]

    @classmethod
    def get_monthly_change(cls, status: str = None):
        """Percentage change vs last month."""
        if status:
            sql_this = """
                SELECT COUNT(*) as cnt FROM shipments
                WHERE status = %s
                  AND MONTH(created_at) = MONTH(CURDATE())
                  AND YEAR(created_at)  = YEAR(CURDATE())
            """
            sql_last = """
                SELECT COUNT(*) as cnt FROM shipments
                WHERE status = %s
                  AND MONTH(created_at) = MONTH(DATE_SUB(CURDATE(), INTERVAL 1 MONTH))
                  AND YEAR(created_at)  = YEAR(DATE_SUB(CURDATE(), INTERVAL 1 MONTH))
            """
            this_m = execute_query(sql_this, (status,), fetchone=True)['cnt']
            last_m = execute_query(sql_last, (status,), fetchone=True)['cnt']
        else:
            sql_this = """
                SELECT COUNT(*) as cnt FROM shipments
                WHERE MONTH(created_at) = MONTH(CURDATE())
                  AND YEAR(created_at)  = YEAR(CURDATE())
            """
            sql_last = """
                SELECT COUNT(*) as cnt FROM shipments
                WHERE MONTH(created_at) = MONTH(DATE_SUB(CURDATE(), INTERVAL 1 MONTH))
                  AND YEAR(created_at)  = YEAR(DATE_SUB(CURDATE(), INTERVAL 1 MONTH))
            """
            this_m = execute_query(sql_this, fetchone=True)['cnt']
            last_m = execute_query(sql_last, fetchone=True)['cnt']

        if last_m == 0:
            return 100 if this_m > 0 else 0
        return round(((this_m - last_m) / last_m) * 100, 1)

    # ── Revenue ──────────────────────────────────────────────────────── #

    @classmethod
    def get_total_revenue(cls):
        result = execute_query(
            "SELECT COALESCE(SUM(amount), 0) as total FROM shipments WHERE status = 'delivered'",
            fetchone=True
        )
        return result['total'] if result else 0

    @classmethod
    def get_revenue_change_this_month(cls):
        sql_this = """
            SELECT COALESCE(SUM(amount), 0) as total FROM shipments
            WHERE status = 'delivered'
              AND MONTH(created_at) = MONTH(CURDATE())
              AND YEAR(created_at)  = YEAR(CURDATE())
        """
        sql_last = """
            SELECT COALESCE(SUM(amount), 0) as total FROM shipments
            WHERE status = 'delivered'
              AND MONTH(created_at) = MONTH(DATE_SUB(CURDATE(), INTERVAL 1 MONTH))
              AND YEAR(created_at)  = YEAR(DATE_SUB(CURDATE(), INTERVAL 1 MONTH))
        """
        this_m = execute_query(sql_this, fetchone=True)['total']
        last_m = execute_query(sql_last, fetchone=True)['total']
        if last_m == 0:
            return 100 if this_m > 0 else 0
        return round(((this_m - last_m) / last_m) * 100, 1)

    # ── Shipment Management (CRUD) ───────────────────────────────────── #

    @classmethod
    def get_all_paginated(cls, status=None, search=None, page=1, limit=20):
        offset = (page - 1) * limit
        conditions, params = [], []

        if status:
            conditions.append("s.status = %s")
            params.append(status)
        if search:
            conditions.append("(s.tracking_id LIKE %s OR u.name LIKE %s OR s.destination LIKE %s)")
            like = f"%{search}%"
            params.extend([like, like, like])

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        total = execute_query(
            f"SELECT COUNT(*) as cnt FROM shipments s LEFT JOIN users u ON s.customer_id = u.id {where}",
            params, fetchone=True
        )['cnt']

        rows = execute_query(
            f"""
            SELECT s.id, s.tracking_id,
                   u.name AS customer_name, a.name AS agent_name,
                   s.destination, s.status, s.amount, s.notes,
                   s.created_at, s.updated_at
            FROM shipments s
            LEFT JOIN users           u ON s.customer_id = u.id
            LEFT JOIN delivery_agents a ON s.agent_id    = a.id
            {where}
            ORDER BY s.created_at DESC
            LIMIT %s OFFSET %s
            """,
            params + [limit, offset], fetchall=True
        )
        for r in rows:
            r['created_at'] = str(r['created_at']) if r.get('created_at') else None
            r['updated_at'] = str(r['updated_at']) if r.get('updated_at') else None

        return rows, total

    @classmethod
    def get_by_id(cls, shipment_id):
        return execute_query(
            """
            SELECT s.*, u.name AS customer_name, u.email AS customer_email,
                   a.name AS agent_name, a.phone AS agent_phone
            FROM shipments s
            LEFT JOIN users           u ON s.customer_id = u.id
            LEFT JOIN delivery_agents a ON s.agent_id    = a.id
            WHERE s.id = %s
            """,
            (shipment_id,), fetchone=True
        )

    @classmethod
    def create(cls, data: dict):
        last = execute_query(
            "SELECT tracking_id FROM shipments ORDER BY id DESC LIMIT 1", fetchone=True
        )
        if last and last['tracking_id']:
            last_num = int(last['tracking_id'].replace('NXP-', ''))
            tracking_id = f"NXP-{last_num + 1}"
        else:
            tracking_id = "NXP-1000"

        return execute_query(
            "INSERT INTO shipments (tracking_id, customer_id, agent_id, destination, status, amount, notes) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (
                tracking_id,
                data['customer_id'], data.get('agent_id'),
                data['destination'],
                data.get('status', 'pending'),
                data['amount'],
                data.get('notes', '')
            )
        ), tracking_id

    @classmethod
    def update_status(cls, shipment_id, new_status):
        return execute_query(
            "UPDATE shipments SET status = %s WHERE id = %s",
            (new_status, shipment_id)
        )

    @classmethod
    def delete(cls, shipment_id):
        return execute_query("DELETE FROM shipments WHERE id = %s", (shipment_id,))