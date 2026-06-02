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
        Expanded to create all 4 tables NepXpress needs.
        Teammate's original users table is preserved exactly.
        """
        db = Database()

        # ── users (teammate's original, untouched) ───────────────────── #
        db.execute(
            "CREATE TABLE IF NOT EXISTS users ("
            "id INT PRIMARY KEY AUTO_INCREMENT,"
            "name VARCHAR(100) NOT NULL,"
            "email VARCHAR(100) NOT NULL UNIQUE,"
            "password VARCHAR(255) NOT NULL,"
            "role VARCHAR(20) NOT NULL DEFAULT 'customer',"
            "status VARCHAR(20) NOT NULL DEFAULT 'active',"
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            ")"
        )

        # ── delivery_agents ──────────────────────────────────────────── #
        db.execute(
            "CREATE TABLE IF NOT EXISTS delivery_agents ("
            "id INT PRIMARY KEY AUTO_INCREMENT,"
            "name VARCHAR(120) NOT NULL,"
            "email VARCHAR(180) NOT NULL UNIQUE,"
            "phone VARCHAR(20),"
            "status ENUM('active','inactive','offline') NOT NULL DEFAULT 'active',"
            "zone VARCHAR(100),"
            "created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,"
            "updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
            ")"
        )

        # ── shipments ────────────────────────────────────────────────── #
        db.execute(
            "CREATE TABLE IF NOT EXISTS shipments ("
            "id INT PRIMARY KEY AUTO_INCREMENT,"
            "tracking_id VARCHAR(30) NOT NULL UNIQUE,"
            "customer_id INT NOT NULL,"
            "agent_id INT,"
            "destination VARCHAR(200) NOT NULL,"
            "status ENUM('pending','processing','in_transit','delivered','delayed','cancelled')"
            "  NOT NULL DEFAULT 'pending',"
            "amount DECIMAL(12,2) NOT NULL DEFAULT 0.00,"
            "notes TEXT,"
            "created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,"
            "updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,"
            "FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE,"
            "FOREIGN KEY (agent_id) REFERENCES delivery_agents(id) ON DELETE SET NULL"
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
        