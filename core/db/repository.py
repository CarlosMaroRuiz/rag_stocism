class BaseRepository:
    def __init__(self, db):
        self.db = db

    def fetch_one(self, query, params=None):
        conn = self.db.connect()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            return cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

    def fetch_all(self, query, params=None):
        conn = self.db.connect()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    def execute(self, query, params=None):
        conn = self.db.connect()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params or ())
            conn.commit()
            return cursor.rowcount
        finally:
            cursor.close()
            conn.close()
