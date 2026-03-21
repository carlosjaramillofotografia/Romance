# core/romance_memory.py
import sqlite3
import time
from typing import Dict, List
import os

class RomanceMemory:
    """
    Sistema de Memoria Persistente de Romance.
    Utiliza SQLite para recordar conversaciones incluso si el sistema se apaga.
    """
    
    def __init__(self, db_path: str = "romance.db", max_context_messages: int = 15):
        # Adaptación para Vercel: el sistema de archivos es de solo lectura excepto /tmp
        if os.environ.get("VERCEL"):
            self.db_path = "/tmp/romance.db"
        else:
            self.db_path = db_path
        self.max_context = max_context_messages
        self._init_db()
        
    def _init_db(self):
        """Inicializa las tablas de la base de datos si no existen."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    last_active REAL
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    role TEXT,
                    content TEXT,
                    timestamp REAL,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                )
            ''')
            conn.commit()
            
    def _update_session(self, session_id: str, timestamp: float):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO sessions (session_id, last_active) VALUES (?, ?)", 
                (session_id, timestamp)
            )
            conn.commit()

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Añade un mensaje al historial y actualiza la sesión."""
        current_time = time.time()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (session_id, role, content, current_time)
            )
            conn.commit()
            
        self._update_session(session_id, current_time)
        
    def get_context(self, session_id: str, max_chars: int = 4000) -> List[Dict[str, str]]:
        """
        Recupera el contexto de la sesión, podado por cantidad de caracteres
        para evitar exceder los Rate Limits (TPM) de la API.
        Prioriza los mensajes más recientes.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Traemos un poco más de lo necesario para podar en Python
                cursor.execute('''
                    SELECT role, content FROM messages 
                    WHERE session_id = ? 
                    ORDER BY id DESC LIMIT 30
                ''', (session_id,))
                rows = cursor.fetchall()
            
            contexto = []
            char_count = 0
            
            # Recorremos desde el más reciente (están en orden DESC)
            for role, content in rows:
                msg_len = len(content)
                if char_count + msg_len > max_chars:
                    break
                contexto.append({"role": role, "content": content})
                char_count += msg_len
            
            # Revertimos para que el orden sea cronológico (viejo -> nuevo)
            return list(reversed(contexto))
                
        except sqlite3.Error as e:
            print(f"Error recuperando memoria: {e}")
            return []
        
    def clear_session(self, session_id: str) -> None:
        """Borra todo rastro de una sesión (efecto cascada en messages)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Borrar de messages explícitamente si PRAGMA foreign_keys no está activo por defecto
            cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
            
    def cleanup_old_sessions(self, max_idle_seconds: int = 86400) -> int:
        """Elimina sesiones demasiado antiguas (ej: 24h) para mantener la BD sana."""
        current_time = time.time()
        limit_time = current_time - max_idle_seconds
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT session_id FROM sessions WHERE last_active < ?", (limit_time,))
            old_sessions = cursor.fetchall()
            
            for (sid,) in old_sessions:
                cursor.execute("DELETE FROM messages WHERE session_id = ?", (sid,))
            
            cursor.execute("DELETE FROM sessions WHERE last_active < ?", (limit_time,))
            conn.commit()
            
        return len(old_sessions)

