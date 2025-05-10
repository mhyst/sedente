from datetime import datetime
from database import Database

class SessionModel:
    def __init__(self, db: Database):
        self.db = db

    def create_session(self, start_time: datetime, end_time: datetime):
        """Crea una nueva sesión de trabajo."""
        duration = int((end_time - start_time).total_seconds())
        self.db.execute("""
            INSERT INTO sessions (start_time, end_time, duration)
            VALUES (?, ?, ?)
        """, (start_time.isoformat(), end_time.isoformat(), duration))

    def list_sessions(self):
        """Devuelve todas las sesiones ordenadas por fecha de inicio."""
        return self.db.fetchall("SELECT * FROM sessions ORDER BY start_time")

    def delete_session(self, session_id: int):
        """Elimina una sesión por su ID."""
        self.db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))

    def get_session_by_id(self, session_id: int):
        """Devuelve los detalles de una sesión por ID."""
        return self.db.fetchone("SELECT * FROM sessions WHERE id = ?", (session_id,))
    
    def get_last_session_id(self) -> int:
        query = "SELECT last_insert_rowid()"
        result = self.db.fetchone(query)
        return result[0] if result else None

class BreakModel:
    def __init__(self, db: Database):
        self.db = db

    def create_break(self, session_id: int, break_time: datetime, duration: int):
        """Registra una pausa tomada durante una sesión."""
        self.db.execute("""
            INSERT INTO breaks (session_id, break_time, duration)
            VALUES (?, ?, ?)
        """, (session_id, break_time.isoformat(), duration))

    def list_breaks(self):
        """Devuelve todas las pausas registradas."""
        return self.db.fetchall("SELECT * FROM breaks ORDER BY break_time")

    def delete_break(self, break_id: int):
        """Elimina una pausa por su ID."""
        self.db.execute("DELETE FROM breaks WHERE id = ?", (break_id,))

    def get_break_by_id(self, break_id: int):
        """Devuelve los detalles de una pausa por ID."""
        return self.db.fetchone("SELECT * FROM breaks WHERE id = ?", (break_id,))
