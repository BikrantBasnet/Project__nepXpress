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
        db = Database()

        # ── users ─────────────────────────────────────────────────────── #
        db.execute(
            "CREATE TABLE IF NOT EXISTS users ("
            "id              INT          PRIMARY KEY AUTO_INCREMENT,"
            "name            VARCHAR(100) NOT NULL,"
            "email           VARCHAR(100) NOT NULL UNIQUE,"
            "password        VARCHAR(255) NOT NULL,"
            "role            VARCHAR(20)  NOT NULL DEFAULT 'customer',"
            "status          VARCHAR(20)  NOT NULL DEFAULT 'active',"
            "phone           VARCHAR(20)           DEFAULT NULL,"
            "address         TEXT                  DEFAULT NULL,"
            "security_answer VARCHAR(255)          DEFAULT NULL,"
            "created_at      TIMESTAMP             DEFAULT CURRENT_TIMESTAMP"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci"
        )

        # ── delivery_agents ──────────────────────────────────────────── #
        db.execute(
            "CREATE TABLE IF NOT EXISTS delivery_agents ("
            "id         INT          PRIMARY KEY AUTO_INCREMENT,"
            "name       VARCHAR(120) NOT NULL,"
            "email      VARCHAR(180) NOT NULL UNIQUE,"
            "phone      VARCHAR(20)           DEFAULT NULL,"
            "status     ENUM('active','inactive','offline') NOT NULL DEFAULT 'active',"
            "zone       VARCHAR(100)          DEFAULT NULL,"
            "created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,"
            "updated_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci"
        )

        # ── shipments ────────────────────────────────────────────────── #
        # user_id  → customer who created the shipment  (CASCADE delete)
        # agent_id → agent from users table assigned to deliver (SET NULL on delete)
        db.execute(
            "CREATE TABLE IF NOT EXISTS shipments ("
            "id                INT           PRIMARY KEY AUTO_INCREMENT,"
            "tracking_id       VARCHAR(40)   NOT NULL UNIQUE,"
            "user_id           INT                    DEFAULT NULL,"
            "agent_id          INT                    DEFAULT NULL,"
            "sender_name       VARCHAR(120)           DEFAULT NULL,"
            "sender_phone      VARCHAR(20)            DEFAULT NULL,"
            "sender_address    VARCHAR(255)           DEFAULT NULL,"
            "sender_city       VARCHAR(100)           DEFAULT NULL,"
            "sender_district   VARCHAR(100)           DEFAULT NULL,"
            "receiver_name     VARCHAR(120)           DEFAULT NULL,"
            "receiver_phone    VARCHAR(20)            DEFAULT NULL,"
            "receiver_address  VARCHAR(255)           DEFAULT NULL,"
            "receiver_city     VARCHAR(100)           DEFAULT NULL,"
            "receiver_district VARCHAR(100)           DEFAULT NULL,"
            "destination       VARCHAR(200)           DEFAULT NULL,"
            "package_type      VARCHAR(50)            DEFAULT NULL,"
            "weight            DECIMAL(10,2)          DEFAULT NULL,"
            "estimated_value   DECIMAL(12,2) NOT NULL DEFAULT 0.00,"
            "delivery_cost     DECIMAL(12,2) NOT NULL DEFAULT 0.00,"
            "delivery_type     VARCHAR(50)   NOT NULL DEFAULT 'Standard',"
            "payment_method    VARCHAR(50)   NOT NULL DEFAULT 'cod',"
            "status            ENUM('pending','processing','in_transit','delivered','delayed','cancelled')"
            "                               NOT NULL DEFAULT 'pending',"
            "attempts          TINYINT       NOT NULL DEFAULT 0,"
            "amount            DECIMAL(12,2) NOT NULL DEFAULT 0.00,"
            "instructions      TEXT                   DEFAULT NULL,"
            "notes             TEXT                   DEFAULT NULL,"
            "processing_at     DATETIME               DEFAULT NULL,"
            "in_transit_at     DATETIME               DEFAULT NULL,"
            "delivered_at      DATETIME               DEFAULT NULL,"
            "delayed_at        DATETIME               DEFAULT NULL,"
            "cancelled_at      DATETIME               DEFAULT NULL,"
            "created_at        DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,"
            "updated_at        DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,"
            "KEY user_id  (user_id),"
            "KEY agent_id (agent_id),"
            "CONSTRAINT shipments_ibfk_1    FOREIGN KEY (user_id)  REFERENCES users(id) ON DELETE CASCADE,"
            "CONSTRAINT fk_shipments_agent  FOREIGN KEY (agent_id) REFERENCES users(id) ON DELETE SET NULL"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci"
        )

        # ── shipment_status_logs ─────────────────────────────────────── #
        db.execute(
            "CREATE TABLE IF NOT EXISTS shipment_status_logs ("
            "id          INT         PRIMARY KEY AUTO_INCREMENT,"
            "shipment_id INT         NOT NULL,"
            "status      VARCHAR(50) NOT NULL,"
            "changed_by  INT                  DEFAULT NULL,"
            "notes       TEXT                 DEFAULT NULL,"
            "created_at  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,"
            "KEY shipment_id (shipment_id),"
            "KEY changed_by  (changed_by),"
            "CONSTRAINT shipment_status_logs_ibfk_1 FOREIGN KEY (shipment_id) REFERENCES shipments(id) ON DELETE CASCADE,"
            "CONSTRAINT shipment_status_logs_ibfk_2 FOREIGN KEY (changed_by)  REFERENCES users(id)     ON DELETE SET NULL"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci"
        )

        # ── system_alerts ────────────────────────────────────────────── #
        db.execute(
            "CREATE TABLE IF NOT EXISTS system_alerts ("
            "id           INT          PRIMARY KEY AUTO_INCREMENT,"
            "type         ENUM('warning','info','success','error') NOT NULL DEFAULT 'info',"
            "title        VARCHAR(200) NOT NULL,"
            "message      TEXT                  DEFAULT NULL,"
            "reference_id VARCHAR(50)           DEFAULT NULL,"
            "is_read      TINYINT(1)   NOT NULL DEFAULT 0,"
            "created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci"
        )

        # ── seed admin user ──────────────────────────────────────────── #
        admin_password = generate_password_hash("admin123")
        db.execute(
            "INSERT IGNORE INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
            ("Admin", "admin@admin.com", admin_password, "admin")
        )

        db.close()
        print("✅ Database tables created successfully!")


# ── Standalone query helper ──────────────────────────────────────────────── #
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