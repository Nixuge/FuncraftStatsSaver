import gzip
from sqlite3 import Row
import threading
from db.VARS import DbVars
from db.queries import Queries

lock = threading.Lock()

class DbUtils:
    @staticmethod
    def contains_id(id: int) -> Row:
        query = Queries.get_where_contains_id(id)
        try:
            lock.acquire(True)
            data = DbVars.ReadInstance.cursor.execute(query).fetchone()
        finally:
            lock.release()

        return data