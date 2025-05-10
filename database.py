import sqlite3
from typing import Any, List, Tuple, Optional

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None

    def connect(self):
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path)
            self.cursor = self.connection.cursor()

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        self.connection = None
        self.cursor = None

    def execute(self, query: str, params: Tuple = ()) -> None:
        self.connect()
        self.cursor.execute(query, params)
        self.connection.commit()

    def fetchall(self, query: str, params: Tuple = ()) -> List[Tuple[Any, ...]]:
        self.connect()
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def fetchone(self, query: str, params: Tuple = ()) -> Optional[Tuple[Any, ...]]:
        self.connect()
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    def check_table_exists(self, table_name: str) -> bool:
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        result = self.fetchone(query, (table_name,))
        return result is not None

    def init(self):
        with self:
            self.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    duration INTEGER  -- En segundos
                )
            """)
        
            self.execute("""
                CREATE TABLE IF NOT EXISTS breaks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    break_time TEXT NOT NULL,
                    duration INTEGER,  -- En segundos
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
            """)
        
            self.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)


    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
