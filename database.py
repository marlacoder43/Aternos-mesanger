import sqlite3

# Bazani yaratamiz
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# Jadval yaratamiz
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    password TEXT
)
""")
conn.commit()

def save_user(user_id, username, password):
    """Foydalanuvchi ma'lumotlarini saqlash"""
    cursor.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?)", (user_id, username, password))
    conn.commit()

def get_user(user_id):
    """Foydalanuvchi login va parolini olish"""
    cursor.execute("SELECT username, password FROM users WHERE user_id=?", (user_id,))
    return cursor.fetchone()