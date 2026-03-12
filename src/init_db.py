import sqlite3

conn = sqlite3.connect("attendance.db")
cur = conn.cursor()

# ================= ADMIN =================
cur.execute("""
CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

cur.execute("""
INSERT OR IGNORE INTO admin (username,password)
VALUES ('shreedhar','shree123')
""")

# ================= TEACHERS =================
cur.execute("""
CREATE TABLE IF NOT EXISTS teachers (
    teacher_id TEXT PRIMARY KEY,
    name TEXT,
    password TEXT,
    subject TEXT,
    active INTEGER DEFAULT 1
)
""")

teachers = [
("T001","Dr. Anil Sharma","pass123","DBMS"),
("T002","Prof. Kavita Reddy","pass123","Operating Systems"),
("T003","Dr. Rajesh Gupta","pass123","Computer Networks"),
("T004","Prof. Sneha Iyer","pass123","Artificial Intelligence"),
("T005","Dr. Vikram Patel","pass123","Machine Learning"),
("T006","Prof. Nisha Verma","pass123","Software Engineering")
]

for t in teachers:
    cur.execute("""
    INSERT OR IGNORE INTO teachers (teacher_id,name,password,subject)
    VALUES (?,?,?,?)
    """, t)

# ================= TEACHER ASSIGNMENTS =================
cur.execute("""
CREATE TABLE IF NOT EXISTS teacher_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_id TEXT,
    class TEXT,
    day TEXT,
    time_slot TEXT
)
""")

assignments = [
("T001","CSE-A","Monday","9:00 - 10:00"),
("T002","CSE-A","Monday","10:00 - 11:00"),
("T003","CSE-A","Tuesday","11:00 - 12:00"),
("T004","CSE-A","Wednesday","12:00 - 1:00"),
("T005","CSE-A","Thursday","2:00 - 3:00"),
("T006","CSE-A","Friday","3:00 - 4:00"),

("T001","CSE-B","Tuesday","9:00 - 10:00"),
("T002","CSE-B","Wednesday","10:00 - 11:00"),
("T003","CSE-B","Thursday","11:00 - 12:00"),
("T004","CSE-B","Friday","12:00 - 1:00"),
("T005","CSE-B","Monday","2:00 - 3:00"),
("T006","CSE-B","Tuesday","3:00 - 4:00")
]

for a in assignments:
    cur.execute("""
    INSERT OR IGNORE INTO teacher_assignments
    (teacher_id,class,day,time_slot)
    VALUES (?,?,?,?)
    """, a)

# ================= STUDENTS =================
cur.execute("""
CREATE TABLE IF NOT EXISTS students (
    student_id TEXT PRIMARY KEY,
    name TEXT,
    class TEXT,
    active INTEGER DEFAULT 1
)
""")

students = []

# 35 students CSE-A
for i in range(1,36):
    students.append((f"21CSA{i:03d}", f"Student_A_{i}", "CSE-A"))

# 35 students CSE-B
for i in range(36,71):
    students.append((f"21CSB{i:03d}", f"Student_B_{i}", "CSE-B"))

for s in students:
    cur.execute("""
    INSERT OR IGNORE INTO students (student_id,name,class)
    VALUES (?,?,?)
    """, s)

# ================= ATTENDANCE =================
cur.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT,
    class TEXT,
    date TEXT,
    hour TEXT,
    status TEXT
)
""")

conn.commit()
conn.close()

print("Database + dataset created successfully")