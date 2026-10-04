import sqlite3
import os
from pathlib import Path

DB_FILE = Path(__file__).resolve().parent.parent / "users.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    
    # Check if admin user exists, if not, create a default one (admin/admin)
    cursor.execute('SELECT * FROM users WHERE username = ?', ('admin',))
    if not cursor.fetchone():
        import hashlib
        salt = os.urandom(32)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', 'admin'.encode('utf-8'), salt, 100000)
        password_hash = salt.hex() + ":" + pwd_hash.hex()
        
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', ('admin', password_hash))
        print("Default admin user created with password 'admin'")
        
    conn.commit()
    conn.close()

# Initialize DB on import
init_db()
