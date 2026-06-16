"""
seed_data.py — one-time seed script for NepXpress.

Drop this file in your PROJECT ROOT (same folder as run.py) and run:
    python seed_data.py

Creates 20 users (with werkzeug password hashes + hashed security
answers) and shipments for each user covering every status, with a
realistic per-stage timeline (processing -> in_transit -> delivered/
delayed/cancelled), each stage timestamped at a different time.

Safe to re-run: it skips users that already exist.
"""

import random
from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash
from app.models.database import Database


# ── Config ──────────────────────────────────────────────────────────────── #

FIRST_NAMES = [
    "ram", "hari", "shyam", "geeta", "krishna", "anish", "sabin", "unish",
    "rujab", "bikrant", "ishan", "sankalpa", "bardan", "progess", "aayush",
    "pranjal", "ishant", "yash", "pratik", "rom",
]

SURNAMES = [
    "Sharma", "Thapa", "Gurung", "Karki", "Adhikari", "Shrestha", "Rai",
    "Magar", "Tamang", "Bhattarai", "Lamichhane", "Poudel", "Khadka",
    "Basnet", "Acharya", "Pandey", "Dahal", "Joshi", "Chhetri", "Subedi",
]

CITIES = ["Kathmandu", "Pokhara", "Itahari", "Biratnagar", "Lalitpur",
          "Bhaktapur", "Birgunj", "Dharan", "Butwal", "Nepalgunj"]

DISTRICT_BY_CITY = {
    "Kathmandu": "Kathmandu", "Pokhara": "Kaski", "Itahari": "Sunsari",
    "Biratnagar": "Morang", "Lalitpur": "Lalitpur", "Bhaktapur": "Bhaktapur",
    "Birgunj": "Parsa", "Dharan": "Sunsari", "Butwal": "Rupandehi",
    "Nepalgunj": "Banke",
}

STATUSES = ["processing", "in_transit", "delivered", "delayed", "cancelled"]

PACKAGE_TYPES = ["Document", "Parcel", "Fragile", "Electronics", "Clothing", "Food"]

DELIVERY_PRICES = {"Standard": 150, "Express": 350, "Same-day": 500}

SECURITY_ANSWER = "dog"   # hashed, lowercased — matches check_security_answer()


def make_email(name, existing_emails):
    """name123@gmail.com, or NAME123@GMAIL.COM if the lowercase one is taken."""
    lower = f"{name}123@gmail.com"
    if lower not in existing_emails:
        return lower
    return f"{name.upper()}123@GMAIL.COM"


def generate_tracking_id(db):
    while True:
        tid = f"NXP-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
        if not db.fetch_one("SELECT id FROM shipments WHERE tracking_id=%s", (tid,)):
            return tid


def main():
    db = Database()

    existing = db.fetch_all("SELECT email FROM users")
    existing_emails = {row["email"] for row in existing}

    created_users = 0
    created_shipments = 0

    for i, name in enumerate(FIRST_NAMES):
        surname = SURNAMES[i % len(SURNAMES)]
        full_name = f"{name.capitalize()} {surname}"
        email = make_email(name, existing_emails)
        existing_emails.add(email)

        plain_password = f"{name}123@"
        hashed_password = generate_password_hash(plain_password)
        hashed_answer = generate_password_hash(SECURITY_ANSWER.strip().lower())

        phone = f"98{random.randint(10000000, 99999999)}"
        home_city = random.choice(CITIES)
        address = f"{home_city}-{random.randint(1, 20)}, {DISTRICT_BY_CITY[home_city]}"

        row = db.fetch_one("SELECT id FROM users WHERE email=%s", (email,))
        if row:
            user_id = row["id"]
        else:
            db.execute(
                "INSERT INTO users (name, email, password, role, status, phone, address, security_answer) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (full_name, email, hashed_password, "customer", "active",
                 phone, address, hashed_answer)
            )
            user_id = db.fetch_one("SELECT id FROM users WHERE email=%s", (email,))["id"]
            created_users += 1

        # One shipment per status for this user
        for offset, status in enumerate(STATUSES):
            sender_city = home_city
            receiver_city = random.choice([c for c in CITIES if c != sender_city])
            delivery_type = random.choice(list(DELIVERY_PRICES.keys()))
            delivery_cost = DELIVERY_PRICES[delivery_type]
            estimated_value = random.choice([500, 800, 1200, 1500, 2000, 3000, 5000])
            weight = round(random.uniform(0.5, 9.5), 1)
            created_at = datetime.now() - timedelta(days=offset * 3 + random.randint(2, 5))
            tracking_id = generate_tracking_id(db)

            # ── Build the stage timeline ──────────────────────────────── #
            processing_at = created_at
            in_transit_at = None
            delivered_at  = None
            delayed_at    = None
            cancelled_at  = None

            accept_gap = timedelta(hours=random.randint(4, 28))
            move_gap   = timedelta(days=random.randint(1, 3), hours=random.randint(0, 12))

            if status == "in_transit":
                in_transit_at = processing_at + accept_gap
            elif status == "delivered":
                in_transit_at = processing_at + accept_gap
                delivered_at  = in_transit_at + move_gap
            elif status == "delayed":
                in_transit_at = processing_at + accept_gap
                delayed_at    = in_transit_at + move_gap
            elif status == "cancelled":
                cancelled_at  = processing_at + timedelta(hours=random.randint(2, 20))
            # status == "processing" -> only processing_at is set

            db.execute(
                "INSERT INTO shipments "
                "(tracking_id, user_id, sender_name, sender_phone, sender_address, "
                " sender_city, sender_district, receiver_name, receiver_phone, "
                " receiver_address, receiver_city, receiver_district, destination, "
                " package_type, weight, estimated_value, delivery_cost, "
                " delivery_type, payment_method, status, instructions, created_at, "
                " processing_at, in_transit_at, delivered_at, delayed_at, cancelled_at) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (
                    tracking_id, user_id,
                    full_name, phone, address,
                    sender_city, DISTRICT_BY_CITY[sender_city],
                    f"Receiver {offset+1}", f"98{random.randint(10000000, 99999999)}",
                    f"{receiver_city}-{random.randint(1, 20)}", receiver_city,
                    DISTRICT_BY_CITY[receiver_city], receiver_city,
                    random.choice(PACKAGE_TYPES), weight, estimated_value, delivery_cost,
                    delivery_type, "cod", status, "", created_at,
                    processing_at, in_transit_at, delivered_at, delayed_at, cancelled_at,
                )
            )
            created_shipments += 1

    db.close()
    print(f"✅ Seed complete. New users: {created_users}, new shipments: {created_shipments}")


if __name__ == "__main__":
    main()