import pymysql
from werkzeug.security import generate_password_hash


class Database:
    def __init__(self):
       self.connection = pymysql.connect(
    host="localhost",
    user="root",
    password="Newbie007@",
    database="nepXpress",
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
        
        # Create users table
        db.execute(
            "CREATE TABLE IF NOT EXISTS users ("
            "id INT PRIMARY KEY AUTO_INCREMENT,"
            "name VARCHAR(100) NOT NULL,"
            "email VARCHAR(100) NOT NULL UNIQUE,"
            "password VARCHAR(255) NOT NULL,"
            "role VARCHAR(20) NOT NULL DEFAULT 'customer',"
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            ")"
        )
        
        # Insert default admin user
        admin_password = generate_password_hash("admin123")
        db.execute(
            "INSERT IGNORE INTO users (name, email, password, role) "
            "VALUES (%s, %s, %s, %s)",
            ("Admin", "admin@admin.com", admin_password, "admin")
        )
        
        db.close()
        print("✅ Database tables created successfully!")