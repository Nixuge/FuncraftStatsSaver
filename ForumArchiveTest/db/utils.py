import gzip
from sqlite3 import Row
import threading
from db.VARS import DbVars
from db.queries import QueriesThreads

lock = threading.Lock()

class DbUtils:
    @staticmethod
    def contains_post_id(table_name: str, thread_id: int) -> Row:
        query = QueriesThreads.get_where_contains_thread_id(table_name, thread_id)
        try:
            lock.acquire(True)
            data = DbVars.ReadInstance.cursor.execute(query).fetchone()
        finally:
            lock.release()

        return data