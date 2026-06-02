from app.models.BaseModel import BaseModel
from app.models.database import Database, execute_query
from werkzeug.security import generate_password_hash, check_password_hash


class User(BaseModel):
    """
    Teammate's User class kept exactly as-is.
    - Class name: User  (not UserModel)
    - Password column: 'password'  (not 'password_hash')
    - Hashing: werkzeug  (not SHA-256)

    Admin dashboard class methods added at the bottom —
    they are prefixed with 'admin_' to make it clear they
    belong to the admin backend, not the customer-facing app.
    """

    table = "users"
    
    
    def __init__(self, name="", email="", password="", role="customer", security_answer=""):
        self.id = None
        self.name = name
        self.email = email
        self.__password = password
        self.role = role
        self.__security_answer = security_answer  # plain text, hashed on save
        self.created_at = None
    
    def delete_account(self):
        """Permanently delete this user from the database by email."""
        db = Database()
        query = f"DELETE FROM {self.table} WHERE email=%s"
        db.execute(query, (self.email,))
        db.close()
        
    def check_security_answer(self, plain_answer):
        """Check if the given security answer matches the stored hash (by email)."""
        db = Database()
        query = f"SELECT security_answer FROM {self.table} WHERE email=%s"
        result = db.fetch_one(query, (self.email,))
        db.close()

        if not result or not result['security_answer']:
            return False
        return check_password_hash(result['security_answer'], plain_answer.strip().lower())
    
    
    def save(self):
            """Save user to database with hashed password and hashed security answer"""
            db = Database()

            hashed_password = generate_password_hash(self.__password)
            hashed_answer = generate_password_hash(self.__security_answer.strip().lower())

            query = (
                f"INSERT INTO {self.table} (name, email, password, role, security_answer) "
                f"VALUES (%s, %s, %s, %s, %s)"
            )
            db.execute(query, (self.name, self.email, hashed_password, self.role, hashed_answer))
            db.close()
    
    def update_profile_info(self, name, phone, address):
        """Update name, phone, and address by email (email stays the login key)."""
        db = Database()
        query = f"UPDATE {self.table} SET name=%s, phone=%s, address=%s WHERE email=%s"
        db.execute(query, (name, phone, address, self.email))
        db.close()
    
    def update(self):
        """Update user in database."""
        db = Database()
        if self.__password:
            hashed_password = generate_password_hash(self.__password)
            query = (
                f"UPDATE {self.table} SET name=%s, email=%s, password=%s, role=%s "
                f"WHERE id=%s"
            )
            db.execute(query, (self.name, self.email, hashed_password, self.role, self.id))
        else:
            query = (
                f"UPDATE {self.table} SET name=%s, email=%s, role=%s "
                f"WHERE id=%s"
            )
            db.execute(query, (self.name, self.email, self.role, self.id))
        db.close()

    def update_profile(self, name, email):
        """Update user profile (name and email only)."""
        self.name = name
        self.email = email
        self.update()
    
    def update_password(self, new_password):
        """Update the user's password (hashed) by email."""
        db = Database()
        hashed_password = generate_password_hash(new_password)
        query = f"UPDATE {self.table} SET password=%s WHERE email=%s"
        db.execute(query, (hashed_password, self.email))
        db.close()
    
    
    def email_exists(self):
        """Check if email already exists in database."""
        db = Database()
        query = f"SELECT COUNT(*) as count FROM {self.table} WHERE email=%s"
        result = db.fetch_one(query, (self.email,))
        db.close()
        return result['count'] > 0

    def find_by(self, field, value):
        """Find user by a specific field."""
        db = Database()
        query = f"SELECT * FROM {self.table} WHERE {field}=%s"
        result = db.fetch_one(query, (value,))
        db.close()
        return result

    def check_password(self, plain_password):
        """Check if plain password matches the hashed password in database."""
        db = Database()
        query = f"SELECT password FROM {self.table} WHERE email=%s"
        result = db.fetch_one(query, (self.email,))
        db.close()
        if not result:
            return False
        return check_password_hash(result['password'], plain_password)

    @classmethod
    def from_db(cls, db_row):
        """Create User object from database row."""
        user = cls()
        user.id = db_row['id']
        user.name = db_row['name']
        user.email = db_row['email']
        user._User__password = db_row['password']
        user.role = db_row['role']
        user.created_at = db_row['created_at']
        return user

    # ── Admin dashboard helpers (new) ────────────────────────────────── #
    # Prefixed with 'admin_' — clearly separate from customer-facing code.

    @classmethod
    def admin_get_recent_customers(cls, limit=10):
        """Recent customer registrations for the dashboard."""
        sql = """
            SELECT id, name, email, status, created_at
            FROM users
            WHERE role = 'customer'
            ORDER BY created_at DESC
            LIMIT %s
        """
        return execute_query(sql, (limit,), fetchall=True)

    @classmethod
    def admin_get_active_count(cls):
        """Total active customers."""
        sql = "SELECT COUNT(*) as cnt FROM users WHERE role='customer' AND status='active'"
        result = execute_query(sql, fetchone=True)
        return result['cnt'] if result else 0

    @classmethod
    def admin_get_new_this_month(cls):
        """New customer registrations this month (for % change badge)."""
        sql = """
            SELECT COUNT(*) as cnt FROM users
            WHERE role = 'customer'
              AND MONTH(created_at) = MONTH(CURDATE())
              AND YEAR(created_at)  = YEAR(CURDATE())
        """
        result = execute_query(sql, fetchone=True)
        return result['cnt'] if result else 0

    @classmethod
    def admin_verify_login(cls, email: str, plain_password: str):
        """
        Used by AdminAuthController only.
        Returns the full user row if credentials are valid, else None.
        """
        sql = "SELECT * FROM users WHERE email = %s AND role IN ('admin','superadmin') LIMIT 1"
        row = execute_query(sql, (email,), fetchone=True)
        if not row:
            return None
        if check_password_hash(row['password'], plain_password):
            return row
        return None