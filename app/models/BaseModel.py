"""
=============================================================
  OOP Concept: ABSTRACTION & INHERITANCE (Base Model)
=============================================================
  Teammate's ABC structure kept intact.
  Admin dashboard class methods added at the bottom —
  they don't override anything the teammate wrote.
=============================================================
"""

from abc import ABC, abstractmethod
from app.models.database import Database, execute_query


class BaseModel(ABC):
    """
    Abstract Base Class for all models.
    Teammate's original methods (find_by_id, find_by, find_all,
    count_all, delete_by_id) are untouched.
    Admin dashboard helpers added below as class methods.
    """

    # ── Abstract Property (teammate's — child MUST define 'table') ──── #
    @property
    @abstractmethod
    def table(self):
        pass

    # ── Teammate's shared methods (unchanged) ────────────────────────── #

    def find_by_id(self, record_id):
        """Find a single record by its ID."""
        db = Database()
        result = db.fetch_one(
            f"SELECT * FROM {self.table} WHERE id = %s", (record_id,)
        )
        db.close()
        return result

    def find_by(self, column, value):
        """Find a single record by any column."""
        db = Database()
        result = db.fetch_one(
            f"SELECT * FROM {self.table} WHERE {column} = %s", (value,)
        )
        db.close()
        return result

    def find_all(self, order_by="id"):
        """Get all records from the table, ordered by a column."""
        db = Database()
        results = db.fetch_all(
            f"SELECT * FROM {self.table} ORDER BY {order_by}"
        )
        db.close()
        return results

    def count_all(self):
        """Count total records in the table."""
        db = Database()
        result = db.fetch_one(f"SELECT COUNT(*) AS total FROM {self.table}")
        db.close()
        return result["total"]

    def delete_by_id(self, record_id):
        """Delete a record by its ID."""
        db = Database()
        db.execute(f"DELETE FROM {self.table} WHERE id = %s", (record_id,))
        db.close()

    # ── Admin dashboard helpers (new — use execute_query shorthand) ───── #
    # These are class methods so they can be called without an instance,
    # e.g. User.count_where({"role": "customer", "status": "active"})

    @classmethod
    def _table_name(cls):
        """Get table name — works whether subclass uses 'table' property or not."""
        obj = cls.__new__(cls)
        try:
            return obj.table
        except AttributeError:
            return getattr(cls, 'table_name', None)

    @classmethod
    def count_where(cls, conditions: dict = None):
        """Count rows matching optional equality conditions."""
        tbl = cls._table_name()
        if conditions:
            where = " AND ".join([f"{k} = %s" for k in conditions])
            sql = f"SELECT COUNT(*) as cnt FROM {tbl} WHERE {where}"
            result = execute_query(sql, list(conditions.values()), fetchone=True)
        else:
            result = execute_query(f"SELECT COUNT(*) as cnt FROM {tbl}", fetchone=True)
        return result['cnt'] if result else 0

    @classmethod
    def find_where(cls, conditions: dict, order_by="id DESC", limit=None):
        """Fetch rows matching equality conditions."""
        tbl = cls._table_name()
        where = " AND ".join([f"{k} = %s" for k in conditions])
        sql = f"SELECT * FROM {tbl} WHERE {where} ORDER BY {order_by}"
        if limit:
            sql += f" LIMIT {int(limit)}"
        return execute_query(sql, list(conditions.values()), fetchall=True)

    @classmethod
    def insert(cls, data: dict, allowed_fields: list):
        """Insert a row. Returns new row id."""
        tbl = cls._table_name()
        allowed = {k: v for k, v in data.items() if k in allowed_fields}
        cols = ", ".join(allowed.keys())
        placeholders = ", ".join(["%s"] * len(allowed))
        sql = f"INSERT INTO {tbl} ({cols}) VALUES ({placeholders})"
        return execute_query(sql, list(allowed.values()))

    @classmethod
    def update_by_id(cls, record_id, data: dict, allowed_fields: list):
        """Update a row by id. Returns rowcount."""
        tbl = cls._table_name()
        allowed = {k: v for k, v in data.items() if k in allowed_fields}
        set_clause = ", ".join([f"{k} = %s" for k in allowed])
        sql = f"UPDATE {tbl} SET {set_clause} WHERE id = %s"
        return execute_query(sql, list(allowed.values()) + [record_id])