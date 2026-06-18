from app.models.BaseModel import BaseModel
from app.models.database import Database, execute_query
import random


class Shipment(BaseModel):
    table = "shipments"

    def __init__(self):
        self.id = None

    @staticmethod
    def generate_tracking_id():
        db = Database()
        while True:
            tid = f"NXP-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
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
            " sender_city, sender_district, receiver_name, receiver_phone, "
            " receiver_address, receiver_city, receiver_district, destination, package_type, "
            " weight, estimated_value, delivery_cost, "
            " delivery_type, payment_method, status, instructions) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        )
        db.execute(query, (
            data["tracking_id"],
            data["user_id"],
            data.get("sender_name", ""),
            data.get("sender_phone", ""),
            data.get("sender_address", ""),
            data.get("sender_city", ""),
            data.get("sender_district", ""),
            data.get("receiver_name", ""),
            data.get("receiver_phone", ""),
            data.get("receiver_address", ""),
            data.get("receiver_city", ""),
            data.get("receiver_district", ""),
            data.get("package_type", ""),
            data.get("weight") or None,
            data.get("estimated_value") or 0,
            data.get("delivery_cost") or 0,
            data.get("delivery_type", "Standard"),
            data.get("payment_method", "cod"),
            data.get("status", "Pending"),
            data.get("instructions", ""),
        ))
        db.close()
    # ---- READ: history page ----
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

    # ---- READ: history stat cards ----
    def get_stats_for_user(self, user_id):
        db = Database()
        rows = db.fetch_all(
            "SELECT status, COUNT(*) AS cnt FROM shipments WHERE user_id=%s GROUP BY status",
            (user_id,)
        )
        db.close()
        stats = {"total": 0, "Delivered": 0, "In Transit": 0, "Processing": 0}
        label_map = {
            "delivered": "Delivered", "in_transit": "In Transit", "in transit": "In Transit",
            "processing": "Processing", "pending": "Processing",
            "delayed": "In Transit", "cancelled": "Cancelled",
        }
        for row in rows:
            stats["total"] += row["cnt"]
            label = label_map.get((row["status"] or "").lower(), "")
            if label and label in stats:
                stats[label] += row["cnt"]
        return stats

    @classmethod
    def get_history_for_agent(cls, agent_id):
        """
        Fetches the complete delivery history for a logged-in agent.
        """
        sql = """
            SELECT s.*, u.name AS customer_name 
            FROM shipments s
            JOIN users u ON s.user_id = u.id
            WHERE s.agent_id = %s
            ORDER BY s.updated_at DESC
        """
        return execute_query(sql, (agent_id,), fetchall=True)
    
# ---- READ: summary page numbers ----
    def get_summary_for_user(self, user_id):
        db = Database()
        rows = db.fetch_all(
            "SELECT status, estimated_value, delivery_cost, created_at FROM shipments WHERE user_id=%s",
            (user_id,)
        )
        db.close()

        total = len(rows)
        delivered = in_transit = failed = 0
        value_spent = value_this_month = value_last_month = 0.0   # package value
        ship_spent = 0.0                                          # delivery cost

        from datetime import date
        today = date.today()
        this_m, this_y = today.month, today.year
        last_m = 12 if this_m == 1 else this_m - 1
        last_y = this_y - 1 if this_m == 1 else this_y

        for r in rows:
            st = (r["status"] or "").lower()
            val = float(r["estimated_value"] or 0)
            ship = float(r["delivery_cost"] or 0)
            value_spent += val
            ship_spent += ship
            if st == "delivered":
                delivered += 1
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

        avg_value = (value_spent / total) if total else 0
        avg_ship = (ship_spent / total) if total else 0
        success_rate = (delivered / total * 100) if total else 0
        base = total if total else 1
        return {
            "total": total, "delivered": delivered, "in_transit": in_transit, "failed": failed,
            "value_spent": value_spent, "avg_value": avg_value,
            "ship_spent": ship_spent, "avg_ship": avg_ship,
            "value_this_month": value_this_month, "value_last_month": value_last_month,
            "success_rate": success_rate,
            "pct_delivered": round(delivered / base * 100),
            "pct_transit": round(in_transit / base * 100),
            "pct_failed": round(failed / base * 100),
        }

    # ---- READ: dashboard + summary recent list ----
    def find_recent_for_user(self, user_id, limit=5):
        db = Database()
        results = db.fetch_all(
            "SELECT * FROM shipments WHERE user_id=%s ORDER BY created_at DESC LIMIT %s",
            (user_id, limit)
        )
        db.close()
        return results

    @classmethod
    def get_available_deliveries(cls):
        """Fetch all shipments that have not been assigned to any driver yet."""
        sql = """
            SELECT id, tracking_id, sender_city, destination, package_type, 
                   weight, estimated_value, delivery_cost, status 
            FROM shipments 
            WHERE agent_id IS NULL AND status = 'pending'
            ORDER BY created_at DESC
        """
        return execute_query(sql, fetchall=True)

    @classmethod
    def assign_agent_to_shipment(cls, shipment_id, agent_id):
        """Assign driver ID and update status tracking."""
        sql = """
            UPDATE shipments 
            SET agent_id = %s, status = 'processing', updated_at = NOW() 
            WHERE id = %s AND agent_id IS NULL
        """
        db = Database()
        cursor = db.connection.cursor()
        affected_rows = cursor.execute(sql, (agent_id, shipment_id))
        db.connection.commit()
        db.close()
        return affected_rows
    
    @classmethod
    def get_active_for_agent(cls, agent_id):
        sql = """
            SELECT id, tracking_id, sender_name, sender_phone,
                sender_address, sender_city, receiver_name, receiver_phone,
                receiver_address, receiver_city, package_type, weight,
                delivery_cost, payment_method, status, instructions
            FROM shipments
            WHERE agent_id = %s
            AND status NOT IN ('delivered', 'cancelled')
            ORDER BY created_at ASC
        """
        return execute_query(sql, (agent_id,), fetchall=True)
    
    @classmethod
    def get_active_for_agent(cls, agent_id):
        # Step 1: get the shipments
        shipments = execute_query(
            """
            SELECT id, tracking_id, sender_name, sender_phone,
                sender_address, sender_city, receiver_name, receiver_phone,
                receiver_address, receiver_city, package_type, weight,
                delivery_cost, payment_method, status, instructions, attempts
            FROM shipments
            WHERE agent_id = %s
            AND status NOT IN ('delivered', 'cancelled', 'return_to_sender')
            ORDER BY created_at ASC
            """,
            (agent_id,), fetchall=True
        )

        if not shipments:
            return []

        # Step 2: for each shipment, fetch its status log from the notebook
        for shipment in shipments:
            logs = execute_query(
                """
                SELECT status, notes,
                    DATE_FORMAT(created_at, '%Y-%m-%d %H:%i') AS time
                FROM shipment_status_logs
                WHERE shipment_id = %s
                ORDER BY created_at ASC
                """,
                (shipment["id"],), fetchall=True
            )
            # Attach the history so the template can read it
            # If no logs yet, seed with the current status so the timeline isn't empty
            shipment["history"] = logs if logs else [
                {"status": shipment["status"], "time": "—", "notes": None}
            ]

        return shipments

    
    @classmethod
    def update_status(cls, shipment_id, agent_id, new_status, notes=None):
        # Update the current status on the shipment (the whiteboard)
        execute_query(
            "UPDATE shipments SET status = %s, updated_at = NOW() "
            "WHERE id = %s AND agent_id = %s",
            (new_status, shipment_id, agent_id)
        )
        # Write to the notebook so history is never lost
        cls.log_status_change(shipment_id, new_status, agent_id, notes)

    @classmethod
    def record_failed_attempt(cls, shipment_id, agent_id, reason=None):
        execute_query(
            "UPDATE shipments SET attempts = attempts + 1, updated_at = NOW() "
            "WHERE id = %s AND agent_id = %s",
            (shipment_id, agent_id)
        )
        row = execute_query(
            "SELECT attempts FROM shipments WHERE id = %s",
            (shipment_id,), fetchone=True
        )
        new_attempts = row["attempts"] if row else 0
        # Log it with the reason as a note
        cls.log_status_change(shipment_id, "Failed Attempt", agent_id, notes=reason)
        return new_attempts
    
    @classmethod
    def log_status_change(cls, shipment_id, new_status, agent_id, notes=None):
        """Write one row to the notebook every time status changes."""
        execute_query(
            "INSERT INTO shipment_status_logs (shipment_id, status, changed_by, notes) "
            "VALUES (%s, %s, %s, %s)",
            (shipment_id, new_status, agent_id, notes)
        )
