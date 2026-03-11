import sqlite3
from werkzeug.security import generate_password_hash

# 🔥 Safe connection
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

# Insert teachers with hashed passwords
teachers = [
("T001","Dr. Anil Sharma",generate_password_hash("pass123"),"DBMS"),
("T002","Prof. Kavita Reddy",generate_password_hash("pass123"),"Operating Systems"),
("T003","Dr. Rajesh Gupta",generate_password_hash("pass123"),"Computer Networks"),
("T004","Prof. Sneha Iyer",generate_password_hash("pass123"),"Artificial Intelligence"),
("T005","Dr. Vikram Patel",generate_password_hash("pass123"),"Machine Learning"),
("T006","Prof. Nisha Verma",generate_password_hash("pass123"),"Software Engineering")
]

for t in teachers:
    cur.execute("""
    INSERT OR IGNORE INTO teachers (teacher_id,name,password,subject)
    VALUES (?,?,?,?)
    """, t)

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

assignments = [
("T001","CSE-A","Monday","9:00 - 10:00"),
("T001","CSE-B","Tuesday","9:00 - 10:00"),

("T002","CSE-A","Monday","10:00 - 11:00"),
("T002","CSE-B","Wednesday","10:00 - 11:00"),

("T003","CSE-A","Tuesday","11:00 - 12:00"),
("T003","CSE-B","Thursday","11:00 - 12:00"),

("T004","CSE-A","Wednesday","12:00 - 1:00"),
("T004","CSE-B","Friday","12:00 - 1:00"),

("T005","CSE-A","Thursday","2:00 - 3:00"),
("T005","CSE-B","Monday","2:00 - 3:00"),

("T006","CSE-A","Friday","3:00 - 4:00"),
("T006","CSE-B","Tuesday","3:00 - 4:00")
]

for a in assignments:
    cur.execute("""
    INSERT OR IGNORE INTO teacher_assignments
    (teacher_id,class,day,time_slot)
    VALUES (?,?,?,?)
    """, a)

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
# ADD 70 STUDENTS
# =========================

students = [

# CSE-A
("21CS001","Aarav Sharma","CSE-A"),
("21CS002","Vivaan Patel","CSE-A"),
("21CS003","Aditya Singh","CSE-A"),
("21CS004","Arjun Verma","CSE-A"),
("21CS005","Krishna Reddy","CSE-A"),
("21CS006","Rohan Mehta","CSE-A"),
("21CS007","Rahul Kumar","CSE-A"),
("21CS008","Karthik Nair","CSE-A"),
("21CS009","Siddharth Gupta","CSE-A"),
("21CS010","Aryan Mishra","CSE-A"),
("21CS011","Ishaan Joshi","CSE-A"),
("21CS012","Harsh Vardhan","CSE-A"),
("21CS013","Nikhil Agarwal","CSE-A"),
("21CS014","Yash Jain","CSE-A"),
("21CS015","Ankit Tiwari","CSE-A"),
("21CS016","Varun Choudhary","CSE-A"),
("21CS017","Manish Yadav","CSE-A"),
("21CS018","Deepak Thakur","CSE-A"),
("21CS019","Abhishek Pandey","CSE-A"),
("21CS020","Gaurav Saxena","CSE-A"),
("21CS021","Neha Sharma","CSE-A"),
("21CS022","Priya Verma","CSE-A"),
("21CS023","Sneha Reddy","CSE-A"),
("21CS024","Ananya Gupta","CSE-A"),
("21CS025","Riya Kapoor","CSE-A"),
("21CS026","Pooja Nair","CSE-A"),
("21CS027","Aditi Mishra","CSE-A"),
("21CS028","Kavya Iyer","CSE-A"),
("21CS029","Meera Jain","CSE-A"),
("21CS030","Shruti Patel","CSE-A"),
("21CS031","Tanvi Singh","CSE-A"),
("21CS032","Nisha Agarwal","CSE-A"),
("21CS033","Sakshi Mehta","CSE-A"),
("21CS034","Isha Choudhary","CSE-A"),
("21CS035","Divya Yadav","CSE-A"),

# CSE-B
("21CS036","Rajat Sharma","CSE-B"),
("21CS037","Kunal Patel","CSE-B"),
("21CS038","Saurabh Singh","CSE-B"),
("21CS039","Rakesh Verma","CSE-B"),
("21CS040","Praveen Kumar","CSE-B"),
("21CS041","Vikas Yadav","CSE-B"),
("21CS042","Rohit Gupta","CSE-B"),
("21CS043","Ajay Mishra","CSE-B"),
("21CS044","Sunil Tiwari","CSE-B"),
("21CS045","Mukesh Jain","CSE-B"),
("21CS046","Anil Reddy","CSE-B"),
("21CS047","Naveen Nair","CSE-B"),
("21CS048","Tarun Agarwal","CSE-B"),
("21CS049","Mahesh Choudhary","CSE-B"),
("21CS050","Prakash Thakur","CSE-B"),
("21CS051","Pankaj Sharma","CSE-B"),
("21CS052","Sanjay Patel","CSE-B"),
("21CS053","Alok Singh","CSE-B"),
("21CS054","Amit Verma","CSE-B"),
("21CS055","Dinesh Kumar","CSE-B"),
("21CS056","Simran Kaur","CSE-B"),
("21CS057","Kiran Reddy","CSE-B"),
("21CS058","Pallavi Nair","CSE-B"),
("21CS059","Monika Gupta","CSE-B"),
("21CS060","Shreya Kapoor","CSE-B"),
("21CS061","Ritu Sharma","CSE-B"),
("21CS062","Komal Jain","CSE-B"),
("21CS063","Payal Mishra","CSE-B"),
("21CS064","Sheetal Yadav","CSE-B"),
("21CS065","Preeti Verma","CSE-B"),
("21CS066","Anjali Singh","CSE-B"),
("21CS067","Deepika Patel","CSE-B"),
("21CS068","Bhavna Mehta","CSE-B"),
("21CS069","Rashmi Tiwari","CSE-B"),
("21CS070","Pooja Choudhary","CSE-B")
]

for s in students:
    cur.execute("""
    INSERT OR IGNORE INTO students (student_id,name,class)
    VALUES (?,?,?)
    """, s)

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