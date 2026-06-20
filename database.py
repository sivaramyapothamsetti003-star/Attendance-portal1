import sqlite3

conn = sqlite3.connect("attendance.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roll TEXT,
    status TEXT,
    date TEXT
)
""")

conn.commit()

def insert_attendance(roll, status, date):
    c.execute("INSERT INTO attendance (roll, status, date) VALUES (?, ?, ?)",
              (roll, status, date))
    conn.commit()