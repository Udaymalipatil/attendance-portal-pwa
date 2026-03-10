import sqlite3

# 🔥 Safe connection (UPGRADED)
conn = sqlite3.connect("attendance.db", timeout=30, check_same_thread=False)
cur = conn.cursor()

cur.execute("PRAGMA journal_mode=WAL;")
cur.execute("PRAGMA busy_timeout = 30000;")

# =========================
# 👨‍💼 ADMIN LOGIN TABLE
# =========================
cur.execute("""
CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

# Default admin
cur.execute("SELECT * FROM admin")
if not cur.fetchone():
    cur.execute("INSERT INTO admin (username, password) VALUES (?, ?)",
                ("shreedhar", "shree123"))

# =========================
# 👨‍🏫 TEACHERS TABLE
# =========================
cur.execute("""
CREATE TABLE IF NOT EXISTS teachers (
    teacher_id TEXT PRIMARY KEY,
    name TEXT,
    password TEXT,
    subject TEXT,
    active INTEGER DEFAULT 1
)
""")

# =========================
# 🗓️ TEACHER TIMETABLE
# =========================
cur.execute("""
CREATE TABLE IF NOT EXISTS teacher_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_id TEXT,
    class TEXT,
    day TEXT,
    time_slot TEXT,
    UNIQUE(teacher_id, day, time_slot),
    UNIQUE(class, day, time_slot)
)
""")

# =========================
# 🎓 STUDENTS TABLE
# =========================
cur.execute("""
CREATE TABLE IF NOT EXISTS students (
    student_id TEXT PRIMARY KEY,
    name TEXT,
    class TEXT,
    active INTEGER DEFAULT 1
)
""")

# =========================
# 📊 STUDENT ATTENDANCE
# =========================
cur.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT,
    class TEXT,
    date TEXT,
    hour TEXT,
    status TEXT CHECK(status IN ('Present','Absent')),
    UNIQUE(student_id, date, hour)
)
""")

conn.commit()
conn.close()

print("✅ DATABASE CREATED SUCCESSFULLY — FULL SYSTEM READY")