from app.models.BaseModel import BaseModel
from app.models.database import Database
import random


class Shipment(BaseModel):
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
            "(tracking_id, user_id, sender_name, sender_phone, sender_address, sender_city, sender_district, "
            "receiver_name, receiver_phone, receiver_address, receiver_city, receiver_district, "
            "package_type, weight, estimated_value, length_cm, width_cm, height_cm, instructions, "
            "delivery_type, payment_method, status) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        )
        db.execute(query, (
            data["tracking_id"], data["user_id"],
            data["sender_name"], data["sender_phone"], data["sender_address"], data["sender_city"], data["sender_district"],
            data["receiver_name"], data["receiver_phone"], data["receiver_address"], data["receiver_city"], data["receiver_district"],
            data["package_type"], data["weight"], data["estimated_value"],
            data["length_cm"], data["width_cm"], data["height_cm"], data["instructions"],
            data["delivery_type"], data["payment_method"], data["status"],
        ))
        db.close()
        db.execute(query, (
            data["tracking_id"], data["user_id"],
            data["sender_name"], data["sender_phone"], data["sender_address"], data["sender_city"], data["sender_district"],
            data["receiver_name"], data["receiver_phone"], data["receiver_address"], data["receiver_city"], data["receiver_district"],
            data["package_type"], data["weight"], data["estimated_value"],
            data["length_cm"], data["width_cm"], data["height_cm"], data["instructions"],
            data["delivery_type"], data["payment_method"], data["status"],
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