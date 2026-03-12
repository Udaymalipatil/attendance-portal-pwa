from flask import Flask, render_template, request, redirect, session, send_from_directory
import sqlite3
from datetime import timedelta, date
from flask_cors import CORS
import os
import subprocess

app = Flask(__name__)
CORS(app)
app.secret_key = "super-secret-key"

app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=2)

# ================= DATABASE PATH =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "attendance.db")

# ================= AUTO CREATE DATABASE =================
if not os.path.exists(DB_PATH):
    print("Creating database automatically...")
    subprocess.run(["python", "init_db.py"])

# ================= DATABASE CONNECTION =================
def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    return conn

# ================= ADMIN LOGIN =================
@app.route("/", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM admin WHERE username=? AND password=?",
                    (request.form["username"], request.form["password"]))
        admin = cur.fetchone()
        db.close()

        if admin:
            session.permanent = True
            session["admin"] = admin["username"]
            return redirect("/dashboard")
        else:
            return render_template("admin_login.html", error="Invalid credentials")

    return render_template("admin_login.html")

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "admin" not in session:
        return redirect("/")

    db = get_db()

    total_teachers = db.execute(
        "SELECT COUNT(*) FROM teachers WHERE active=1"
    ).fetchone()[0]

    total_students = db.execute(
        "SELECT COUNT(*) FROM students WHERE active=1"
    ).fetchone()[0]

    total_attendance = db.execute(
        "SELECT COUNT(*) FROM attendance"
    ).fetchone()[0]

    db.close()

    return render_template(
        "dashboard.html",
        admin=session["admin"],
        total_teachers=total_teachers,
        total_students=total_students,
        total_attendance=total_attendance
    )

# ================= TEACHERS =================
@app.route("/teachers")
def manage_teachers():
    if "admin" not in session:
        return redirect("/")

    db = get_db()

    teachers = db.execute("""
        SELECT t.teacher_id, t.name, t.subject, ta.class, ta.day, ta.time_slot
        FROM teachers t
        LEFT JOIN teacher_assignments ta ON t.teacher_id = ta.teacher_id
    """).fetchall()

    db.close()

    return render_template("teachers.html", admin=session["admin"], teachers=teachers)

@app.route("/create-teacher", methods=["POST"])
def create_teacher():
    if "admin" not in session:
        return redirect("/")

    db = get_db()

    try:
        db.execute(
            "INSERT INTO teachers (teacher_id, name, password, subject) VALUES (?, ?, ?, ?)",
            (
                request.form["teacher_id"],
                request.form["name"],
                request.form["password"],
                request.form["subject"]
            )
        )
        db.commit()

    except sqlite3.IntegrityError:
        db.close()
        return redirect("/teachers?error=Teacher+ID+already+exists")

    db.close()
    return redirect("/teachers")

# ================= STUDENTS =================
@app.route("/students")
def manage_students():
    if "admin" not in session:
        return redirect("/")

    db = get_db()

    students = db.execute(
        "SELECT student_id, name, class FROM students WHERE active=1"
    ).fetchall()

    db.close()

    return render_template("students.html", admin=session["admin"], students=students)

@app.route("/add-student", methods=["POST"])
def add_student():
    if "admin" not in session:
        return redirect("/")

    db = get_db()

    try:
        db.execute(
            "INSERT INTO students (student_id, name, class) VALUES (?, ?, ?)",
            (
                request.form["student_id"],
                request.form["name"],
                request.form["class"]
            )
        )
        db.commit()

    except sqlite3.IntegrityError:
        db.close()
        return redirect("/students?error=Student+ID+exists")

    db.close()
    return redirect("/students")

# ================= TEACHER LOGIN =================
@app.route("/teacher")
def teacher_login_page():
    return render_template("teacher_login.html")

@app.route("/teacher-login", methods=["POST"])
def teacher_login():

    teacher_id = request.form["teacher_id"]
    password = request.form["password"]

    db = get_db()

    teacher = db.execute(
        "SELECT * FROM teachers WHERE teacher_id=? AND active=1",
        (teacher_id,)
    ).fetchone()

    db.close()

    if teacher and teacher["password"] == password:
        session["teacher"] = teacher_id
        return redirect("/teacher-dashboard")

    return render_template("teacher_login.html", error="Invalid Login")

# ================= TEACHER DASHBOARD =================
@app.route("/teacher-dashboard")
def teacher_dashboard():

    if "teacher" not in session:
        return redirect("/teacher")

    teacher_id = session["teacher"]

    db = get_db()

    teacher = db.execute(
        "SELECT name FROM teachers WHERE teacher_id=?",
        (teacher_id,)
    ).fetchone()

    timetable = db.execute(
        "SELECT class, day, time_slot FROM teacher_assignments WHERE teacher_id=?",
        (teacher_id,)
    ).fetchall()

    db.close()

    return render_template(
        "teacher_dashboard.html",
        timetable=timetable,
        teacher_name=teacher["name"] if teacher else teacher_id
    )

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.pop("admin", None)
    session.pop("teacher", None)
    return redirect("/")

# ================= PWA FILES =================
@app.route("/sw.js")
def service_worker():
    return send_from_directory("static", "sw.js",
                               mimetype="application/javascript")

@app.route("/offline.html")
def offline_page():
    return render_template("offline.html")

print("Server loaded successfully")

# ================= RENDER SERVER =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)