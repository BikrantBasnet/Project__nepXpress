import pymysql
import pymysql.cursors
from werkzeug.security import generate_password_hash
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import config


class Database:
    """
    Teammate's Database class — kept intact.
    Credentials now read from config.py / .env instead of being hardcoded.
    """

    def __init__(self):
        self.connection = pymysql.connect(
            host=config.MYSQL_HOST,
            port=config.MYSQL_PORT,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            database=config.MYSQL_DATABASE,
            charset='utf8mb4'
        )
    def fetch_one(self, query, params=None):
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)
        cursor.execute(query, params)
        result = cursor.fetchone()
        cursor.close()
        return result

    def fetch_all(self, query, params=None):
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)
        cursor.execute(query, params)
        result = cursor.fetchall()
        cursor.close()
        return result

    def execute(self, query, params=None):
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        self.connection.commit()
        cursor.close()

    def close(self):
        self.connection.close()

    @staticmethod
    def create_tables():
        """
        Creates the user-side tables NepXpress needs.
        Matches the live production schema exactly (see nepxpress dump),
        plus shipment_status_logs which the agent routes page depends on,
        plus agent_id/attempts/out_for_delivery which the agent flow needs
        but were missing from the original dump.
        """
        db = Database()

        # ── users ─────────────────────────────────────────────────────── #
        db.execute(
            "CREATE TABLE IF NOT EXISTS users ("
            "id INT PRIMARY KEY AUTO_INCREMENT,"
            "name VARCHAR(100) NOT NULL,"
            "email VARCHAR(100) NOT NULL UNIQUE,"
            "password VARCHAR(255) NOT NULL,"
            "role VARCHAR(20) NOT NULL DEFAULT 'customer',"
            "created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,"
            "security_answer VARCHAR(255) DEFAULT NULL,"
            "phone VARCHAR(20) DEFAULT NULL,"
            "address TEXT,"
            "status VARCHAR(20) NOT NULL DEFAULT 'active'"
            ")"
        )

        # ── delivery_agents ──────────────────────────────────────────── #
        db.execute(
            "CREATE TABLE IF NOT EXISTS delivery_agents ("
            "id INT PRIMARY KEY AUTO_INCREMENT,"
            "name VARCHAR(120) NOT NULL,"
            "email VARCHAR(180) NOT NULL UNIQUE,"
            "phone VARCHAR(20) DEFAULT NULL,"
            "status ENUM('active','inactive','offline') NOT NULL DEFAULT 'active',"
            "zone VARCHAR(100) DEFAULT NULL,"
            "created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,"
            "updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
            ")"
        )

        # ── shipments ─────────────────────────────────────────────────── #
        # Matches live dump exactly, plus 3 columns the agent flow needs
        # that are missing from the dump: agent_id, attempts, and the
        # extra ENUM value 'out_for_delivery'.
        db.execute(
            "CREATE TABLE IF NOT EXISTS shipments ("
            "id INT PRIMARY KEY AUTO_INCREMENT,"
            "tracking_id VARCHAR(40) NOT NULL UNIQUE,"
            "user_id INT NOT NULL,"
            "agent_id INT DEFAULT NULL,"
            "sender_name VARCHAR(120),"
            "sender_phone VARCHAR(20),"
            "sender_address VARCHAR(255),"
            "sender_city VARCHAR(100),"
            "sender_district VARCHAR(100),"
            "receiver_name VARCHAR(120),"
            "receiver_phone VARCHAR(20),"
            "receiver_address VARCHAR(255),"
            "receiver_city VARCHAR(100),"
            "receiver_district VARCHAR(100),"
            "destination VARCHAR(200),"
            "package_type VARCHAR(50),"
            "weight DECIMAL(10,2),"
            "estimated_value DECIMAL(12,2) NOT NULL DEFAULT 0.00,"
            "delivery_cost DECIMAL(12,2) NOT NULL DEFAULT 0.00,"
            "delivery_type VARCHAR(20) NOT NULL DEFAULT 'Standard',"
            "payment_method VARCHAR(20) NOT NULL DEFAULT 'cod',"
            "status ENUM('pending','processing','picked_up','in_transit','out_for_delivery','delivered','delayed','cancelled')"
            "  NOT NULL DEFAULT 'pending',"
            "attempts TINYINT NOT NULL DEFAULT 0,"
            "instructions TEXT,"
            "created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,"
            "updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,"
            "processing_at DATETIME DEFAULT CURRENT_TIMESTAMP,"
            "in_transit_at DATETIME DEFAULT NULL,"
            "delivered_at DATETIME DEFAULT NULL,"
            "delayed_at DATETIME DEFAULT NULL,"
            "cancelled_at DATETIME DEFAULT NULL,"
            "FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,"
            "FOREIGN KEY (agent_id) REFERENCES users(id) ON DELETE SET NULL"
            ")"
        )

        # ── system_alerts ────────────────────────────────────────────── #
        db.execute(
            "CREATE TABLE IF NOT EXISTS system_alerts ("
            "id INT PRIMARY KEY AUTO_INCREMENT,"
            "type ENUM('warning','info','success','error') NOT NULL DEFAULT 'info',"
            "title VARCHAR(200) NOT NULL,"
            "message TEXT,"
            "reference_id VARCHAR(50),"
            "is_read TINYINT(1) NOT NULL DEFAULT 0,"
            "created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"
            ")"
        )

        # ── shipment_status_logs ──────────────────────────────────────── #
        # Not present in the live dump yet — required by get_active_for_agent
        # and update_status/record_failed_attempt in ShipmentModel.
        db.execute(
            "CREATE TABLE IF NOT EXISTS shipment_status_logs ("
            "id           INT PRIMARY KEY AUTO_INCREMENT,"
            "shipment_id  INT NOT NULL,"
            "status       VARCHAR(50) NOT NULL,"
            "changed_by   INT,"
            "notes        TEXT,"
            "created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,"
            "FOREIGN KEY (shipment_id) REFERENCES shipments(id) ON DELETE CASCADE,"
            "FOREIGN KEY (changed_by)  REFERENCES users(id) ON DELETE SET NULL"
            ")"
        )

        # ── seed admin user ──────────────────────────────────────────── #
        admin_password = generate_password_hash("admin123")
        db.execute(
            "INSERT IGNORE INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
            ("Admin", "admin@admin.com", admin_password, "admin")
        )

        db.close()
        print("✅ Database tables created successfully!")


# ── Standalone query helper (used by your admin controllers) ─────────────── #
def execute_query(query, params=None, fetchone=False, fetchall=False):
    """
    Used by ShipmentModel, DeliveryAgentModel, AlertModel, and dashboard
    controllers. Keeps those models clean without Database() boilerplate.
    """
    db = Database()
    try:
        with db.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(query, params or ())
            if fetchone:
                return cursor.fetchone()
            if fetchall:
                return cursor.fetchall()
            db.connection.commit()
            return cursor.lastrowid if cursor.lastrowid else cursor.rowcount
    finally:
        db.close()