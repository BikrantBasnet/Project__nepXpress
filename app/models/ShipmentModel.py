from app.models.BaseModel import BaseModel
from app.models.database import Database, execute_query
import random


class Shipment(BaseModel):
    """
    Teammate's Shipment class — kept exactly as-is.
    Used by the customer-facing create-shipment page.
    """
    table = "shipments"

    def __init__(self):
        self.id = None

    @staticmethod
    def generate_tracking_id():
        """Generate a unique tracking ID in format NXP-NNNN-NNNN."""
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
        """Insert a new shipment. `data` is a dict of column->value."""
        db = Database()
        query = (
            "INSERT INTO shipments "
            "(tracking_id, user_id, sender_name, sender_phone, sender_address, "
            " sender_city, sender_district, receiver_name, receiver_phone, "
            " receiver_address, receiver_city, receiver_district, package_type, "
            " weight, estimated_value, length_cm, width_cm, height_cm, "
            " delivery_type, payment_method, status, instructions) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        )
        db.execute(query, (
            data["tracking_id"], data["customer_id"],
            data["destination"], data.get("status", "pending"), data.get("amount", 0.00), data.get("notes", ""),
        ))
        db.close()

    def find_by_user(self, user_id):
        """Get all shipments for a user, newest first."""
        db = Database()
        results = db.fetch_all(
            "SELECT * FROM shipments WHERE user_id=%s ORDER BY created_at DESC",
            (user_id,)
        )
        db.close()
        return results

    def get_stats_for_user(self, user_id):
        """Return counts per status for the stats cards on the history page."""
        db = Database()
        rows = db.fetch_all(
            "SELECT status, COUNT(*) AS cnt "
            "FROM shipments WHERE customer_id=%s GROUP BY status",
            (user_id,)
        )
        db.close()
        stats = {"total": 0, "Delivered": 0, "In Transit": 0, "Processing": 0}
        # Map DB enum values → display labels
        label_map = {
            "delivered":   "Delivered",
            "in_transit":  "In Transit",
            "processing":  "Processing",
            "pending":     "Processing",   # treat pending as processing for display
            "delayed":     "In Transit",   # delayed still counts as in-transit for display
            "cancelled":   "Cancelled",
        }
        for row in rows:
            stats["total"] += row["cnt"]
            label = label_map.get(row["status"].lower(), "")
            if label and label in stats:
                stats[label] += row["cnt"]
        return stats