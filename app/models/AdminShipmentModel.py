from app.models.BaseModel import BaseModel
from app.models.database import Database, execute_query
import random
import time


class Shipment(BaseModel):
    """
    Teammate's Shipment class — customer-facing.
    Uses user_id column (renamed from customer_id in DB).
    """
    table = "shipments"

    def __init__(self):
        self.id = None

    @staticmethod
    def generate_tracking_id():
        db = Database()
        while True:
            tid = f"NXP-{random.randint(1000,9999)}-{random.randint(1000,9999)}"
            existing = db.fetch_one(
                "SELECT id FROM shipments WHERE tracking_id=%s", (tid,)
            )
            if not existing:
                db.close()
                return tid

    def create(self, data):
        db = Database()
        query = (
            "INSERT INTO shipments "
            "(tracking_id, user_id, sender_name, sender_phone, sender_address, "
            " sender_city, receiver_name, receiver_phone, "
            " receiver_address, receiver_city, package_type, "
            " weight, delivery_type, payment_method, status, notes) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        )
        db.execute(query, (
            data["tracking_id"],
            data["user_id"],
            data.get("sender_name", ""),
            data.get("sender_phone", ""),
            data.get("sender_address", ""),
            data.get("sender_city", ""),
            data.get("receiver_name", ""),
            data.get("receiver_phone", ""),
            data.get("receiver_address", ""),
            data.get("receiver_city", ""),
            data.get("package_type", ""),
            data.get("weight") or None,
            data.get("delivery_type", "Standard"),
            data.get("payment_method", "cod"),
            data.get("status", "Pending"),
            data.get("instructions", ""),
        ))
        db.close()

    def find_by_user(self, user_id, status=None):
        db = Database()
        if status:
            results = db.fetch_all(
                "SELECT * FROM shipments WHERE user_id=%s AND status=%s ORDER BY created_at DESC",
                (user_id, status)
            )
        else:
            results = db.fetch_all(
                "SELECT * FROM shipments WHERE user_id=%s ORDER BY created_at DESC",
                (user_id,)
            )
        db.close()
        return results

    def get_stats_for_user(self, user_id):
        db = Database()
        rows = db.fetch_all(
            "SELECT status, COUNT(*) AS cnt FROM shipments WHERE user_id=%s GROUP BY status",
            (user_id,)
        )
        db.close()
        stats = {"total": 0, "Delivered": 0, "In Transit": 0, "Processing": 0}
        label_map = {
            "delivered":  "Delivered",
            "in_transit": "In Transit",
            "in transit": "In Transit",
            "processing": "Processing",
            "pending":    "Processing",
            "delayed":    "In Transit",
            "cancelled":  "Cancelled",
        }
        for row in rows:
            stats["total"] += row["cnt"]
            label = label_map.get((row["status"] or "").lower(), "")
            if label and label in stats:
                stats[label] += row["cnt"]
        return stats

    @classmethod
    def get_history_for_agent(cls, agent_id):
        sql = """
            SELECT s.*, u.name AS customer_name
            FROM shipments s
            JOIN users u ON s.user_id = u.id
            WHERE s.agent_id = %s
            ORDER BY s.updated_at DESC
        """
        return execute_query(sql, (agent_id,), fetchall=True)

    def get_summary_for_user(self, user_id):
        db = Database()
        rows = db.fetch_all(
            "SELECT status, amount, created_at FROM shipments WHERE user_id=%s",
            (user_id,)
        )
        db.close()

        total = len(rows)
        delivered = in_transit = failed = 0
        value_spent = value_this_month = value_last_month = 0.0
        ship_spent = 0.0

        from datetime import date
        today  = date.today()
        this_m, this_y = today.month, today.year
        last_m = 12 if this_m == 1 else this_m - 1
        last_y = this_y - 1 if this_m == 1 else this_y

        for r in rows:
            st  = (r["status"] or "").lower()
            val = float(r["amount"] or 0)
            value_spent += val
            if st == "delivered":
                delivered += 1
                ship_spent += val
            elif st in ("in_transit", "delayed"):
                in_transit += 1
            elif st == "cancelled":
                failed += 1
            d = r["created_at"]
            if d:
                if d.month == this_m and d.year == this_y:
                    value_this_month += val
                elif d.month == last_m and d.year == last_y:
                    value_last_month += val

        avg_value    = (value_spent / total) if total else 0
        avg_ship     = (ship_spent  / total) if total else 0
        success_rate = (delivered   / total * 100) if total else 0
        base = total if total else 1
        return {
            "total":            total,
            "delivered":        delivered,
            "in_transit":       in_transit,
            "failed":           failed,
            "value_spent":      value_spent,
            "avg_value":        avg_value,
            "ship_spent":       ship_spent,
            "avg_ship":         avg_ship,
            "value_this_month": value_this_month,
            "value_last_month": value_last_month,
            "success_rate":     success_rate,
            "pct_delivered":    round(delivered  / base * 100),
            "pct_transit":      round(in_transit / base * 100),
            "pct_failed":       round(failed     / base * 100),
        }

    def find_recent_for_user(self, user_id, limit=5):
        db = Database()
        results = db.fetch_all(
            "SELECT * FROM shipments WHERE user_id=%s ORDER BY created_at DESC LIMIT %s",
            (user_id, limit)
        )
        db.close()
        return results


# ─────────────────────────────────────────────────────────────────────────── #
#  Admin ShipmentModel — uses user_id column (renamed in DB)                  #
# ─────────────────────────────────────────────────────────────────────────── #

class ShipmentModel:

    table = "shipments"

    @classmethod
    def get_recent_shipments(cls, limit=10):
        sql = """
            SELECT s.id, s.tracking_id,
                   u.name  AS customer_name,
                   a.name  AS agent_name,
                   s.destination, s.status, s.amount, s.created_at
            FROM shipments s
            LEFT JOIN users           u ON s.user_id   = u.id
            LEFT JOIN delivery_agents a ON s.agent_id  = a.id
            ORDER BY s.created_at DESC
            LIMIT %s
        """
        return execute_query(sql, (limit,), fetchall=True)

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
        rows = execute_query(
            "SELECT status, COUNT(*) as cnt FROM shipments GROUP BY status",
            fetchall=True
        )
        total = sum(r['cnt'] for r in rows) or 1
        return [
            {"status": r['status'], "count": r['cnt'],
             "percentage": round((r['cnt'] / total) * 100, 1)}
            for r in rows
        ]

    @classmethod
    def get_monthly_change(cls, status: str = None):
        if status:
            sql_this = ("SELECT COUNT(*) as cnt FROM shipments WHERE status=%s"
                        " AND MONTH(created_at)=MONTH(CURDATE()) AND YEAR(created_at)=YEAR(CURDATE())")
            sql_last = ("SELECT COUNT(*) as cnt FROM shipments WHERE status=%s"
                        " AND MONTH(created_at)=MONTH(DATE_SUB(CURDATE(),INTERVAL 1 MONTH))"
                        " AND YEAR(created_at)=YEAR(DATE_SUB(CURDATE(),INTERVAL 1 MONTH))")
            this_m = execute_query(sql_this, (status,), fetchone=True)['cnt']
            last_m = execute_query(sql_last, (status,), fetchone=True)['cnt']
        else:
            sql_this = ("SELECT COUNT(*) as cnt FROM shipments"
                        " WHERE MONTH(created_at)=MONTH(CURDATE()) AND YEAR(created_at)=YEAR(CURDATE())")
            sql_last = ("SELECT COUNT(*) as cnt FROM shipments"
                        " WHERE MONTH(created_at)=MONTH(DATE_SUB(CURDATE(),INTERVAL 1 MONTH))"
                        " AND YEAR(created_at)=YEAR(DATE_SUB(CURDATE(),INTERVAL 1 MONTH))")
            this_m = execute_query(sql_this, fetchone=True)['cnt']
            last_m = execute_query(sql_last, fetchone=True)['cnt']
        if last_m == 0:
            return 100 if this_m > 0 else 0
        return round(((this_m - last_m) / last_m) * 100, 1)

    @classmethod
    def get_total_revenue(cls):
        result = execute_query(
            "SELECT COALESCE(SUM(amount),0) as total FROM shipments WHERE status='delivered'",
            fetchone=True
        )
        return result['total'] if result else 0

    @classmethod
    def get_revenue_change_this_month(cls):
        sql_this = ("SELECT COALESCE(SUM(amount),0) as total FROM shipments"
                    " WHERE status='delivered' AND MONTH(created_at)=MONTH(CURDATE())"
                    " AND YEAR(created_at)=YEAR(CURDATE())")
        sql_last = ("SELECT COALESCE(SUM(amount),0) as total FROM shipments"
                    " WHERE status='delivered'"
                    " AND MONTH(created_at)=MONTH(DATE_SUB(CURDATE(),INTERVAL 1 MONTH))"
                    " AND YEAR(created_at)=YEAR(DATE_SUB(CURDATE(),INTERVAL 1 MONTH))")
        this_m = execute_query(sql_this, fetchone=True)['total']
        last_m = execute_query(sql_last, fetchone=True)['total']
        if last_m == 0:
            return 100 if this_m > 0 else 0
        return round(((this_m - last_m) / last_m) * 100, 1)

    @classmethod
    def get_all_paginated(cls, status=None, search=None, page=1, limit=10):
        offset = (page - 1) * limit
        conditions, params = [], []
        if status:
            conditions.append("s.status = %s")
            params.append(status)
        if search:
            conditions.append(
                "(s.tracking_id LIKE %s OR u.name LIKE %s OR s.destination LIKE %s)"
            )
            like = f"%{search}%"
            params.extend([like, like, like])
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        total = execute_query(
            f"SELECT COUNT(*) as cnt FROM shipments s "
            f"LEFT JOIN users u ON s.user_id=u.id {where}",
            params, fetchone=True
        )['cnt']

        rows = execute_query(
            f"""SELECT s.id, s.tracking_id,
                   u.name AS customer_name, a.name AS agent_name,
                   s.destination, s.status, s.amount, s.notes,
                   s.created_at, s.updated_at
            FROM shipments s
            LEFT JOIN users           u ON s.user_id   = u.id
            LEFT JOIN delivery_agents a ON s.agent_id  = a.id
            {where}
            ORDER BY s.created_at DESC
            LIMIT %s OFFSET %s""",
            params + [limit, offset], fetchall=True
        )
        for r in rows:
            r['created_at'] = str(r['created_at']) if r.get('created_at') else None
            r['updated_at'] = str(r['updated_at']) if r.get('updated_at') else None
        return rows, total

    @classmethod
    def get_by_id(cls, shipment_id):
        row = execute_query(
            """SELECT s.*, u.name AS customer_name, u.email AS customer_email,
                      a.name AS agent_name, a.phone AS agent_phone
               FROM shipments s
               LEFT JOIN users           u ON s.user_id  = u.id
               LEFT JOIN delivery_agents a ON s.agent_id = a.id
               WHERE s.id = %s""",
            (shipment_id,), fetchone=True
        )
        if row:
            row['created_at'] = str(row['created_at']) if row.get('created_at') else None
            row['updated_at'] = str(row['updated_at']) if row.get('updated_at') else None
        return row

    @classmethod
    def admin_create(cls, data: dict):
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
            "INSERT INTO shipments (tracking_id, user_id, agent_id, destination, status, amount, notes) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s)",
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
    def update_status(cls, shipment_id, new_status):
        return execute_query(
            "UPDATE shipments SET status=%s WHERE id=%s",
            (new_status, shipment_id)
        )

    @classmethod
    def delete(cls, shipment_id):
        return execute_query(
            "DELETE FROM shipments WHERE id=%s", (shipment_id,)
        )