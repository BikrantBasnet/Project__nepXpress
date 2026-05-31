from app.models.BaseModel import BaseModel
from app.models.database import Database
from werkzeug.security import generate_password_hash, check_password_hash


class User(BaseModel):
    table = "users"
    
    def __init__(self, name="", email="", password="", role="customer"):
        self.id = None
        self.name = name
        self.email = email
        self.__password = password  # Private attribute for plain text
        self.role = role
        self.created_at = None
        
    
    def save(self):
        """Save user to database with hashed password"""
        db = Database()
        
        # Hash the password before saving
        hashed_password = generate_password_hash(self.__password)
        
        query = (
            f"INSERT INTO {self.table} (name, email, password, role) "
            f"VALUES (%s, %s, %s, %s)"
        )
        db.execute(query, (self.name, self.email, hashed_password, self.role))
        db.close()
    
    
    def update(self):
        """Update user in database"""
        db = Database()
        
        # If password is provided, hash it
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
        """Update user profile (name and email only)"""
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
        """Check if email already exists in database"""
        db = Database()
        query = f"SELECT COUNT(*) as count FROM {self.table} WHERE email=%s"
        result = db.fetch_one(query, (self.email,))
        db.close()
        return result['count'] > 0
    
    
    def find_by(self, field, value):
        """Find user by a specific field"""
        db = Database()
        query = f"SELECT * FROM {self.table} WHERE {field}=%s"
        result = db.fetch_one(query, (value,))
        db.close()
        return result
    
    
    def check_password(self, plain_password):
        """Check if plain password matches the hashed password in database"""
        db = Database()
        
        # Get the stored hash from database using email
        query = f"SELECT password FROM {self.table} WHERE email=%s"
        result = db.fetch_one(query, (self.email,))
        db.close()
        
        if not result:
            return False
        
        # Compare plain password with stored hash
        stored_hash = result['password']
        return check_password_hash(stored_hash, plain_password)
    
    
    @classmethod
    def from_db(cls, db_row):
        """Create User object from database row"""
        user = cls()
        user.id = db_row['id']
        user.name = db_row['name']
        user.email = db_row['email']
        user.__password = db_row['password']  # This is the hash
        user.role = db_row['role']
        user.created_at = db_row['created_at']
        return user