from flask import Flask, render_template, request, redirect, session, flash, send_from_directory
import sqlite3
from datetime import timedelta, date
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)
app.secret_key = "super-secret-key"

app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=2)

# ================= DATABASE =================
def get_db():
    conn = sqlite3.connect("attendance.db", timeout=10)
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

# ================= DASHBOARD (BUG FIX: pass stats) =================
@app.route("/dashboard")
def dashboard():
    if "admin" not in session:
        return redirect("/")
    db = get_db()
    total_teachers = db.execute("SELECT COUNT(*) FROM teachers WHERE active=1").fetchone()[0]
    total_students = db.execute("SELECT COUNT(*) FROM students WHERE active=1").fetchone()[0]
    total_attendance = db.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
    db.close()
    return render_template("dashboard.html",
                           admin=session["admin"],
                           total_teachers=total_teachers,
                           total_students=total_students,
                           total_attendance=total_attendance)

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
        db.execute("INSERT INTO teachers (teacher_id, name, password, subject) VALUES (?, ?, ?, ?)",
                   (request.form["teacher_id"], request.form["name"],
                    request.form["password"], request.form["subject"]))
        db.commit()
    except sqlite3.IntegrityError:
        db.close()
        return redirect("/teachers?error=Teacher+ID+already+exists")
    db.close()
    return redirect("/teachers")

@app.route("/assign-slot", methods=["POST"])
def assign_slot():
    if "admin" not in session:
        return redirect("/")

    teacher_id = request.form["teacher_id"]
    class_name = request.form["class_assigned"]
    day = request.form["day"]
    time_slot = request.form["time_slot"]

    db = get_db()

    # Check if teacher already has a class at this time
    teacher_conflict = db.execute(
        "SELECT * FROM teacher_assignments WHERE teacher_id=? AND day=? AND time_slot=?",
        (teacher_id, day, time_slot)
    ).fetchone()

    if teacher_conflict:
        db.close()
        return redirect("/teachers?error=⚠️ Teacher already assigned to another class at this time")

    # Check if class already has a teacher at this time
    class_conflict = db.execute(
        "SELECT * FROM teacher_assignments WHERE class=? AND day=? AND time_slot=?",
        (class_name, day, time_slot)
    ).fetchone()

    if class_conflict:
        db.close()
        return redirect("/teachers?error=⚠️ This class already has a teacher at this time")

    # Insert assignment
    db.execute(
        "INSERT INTO teacher_assignments (teacher_id, class, day, time_slot) VALUES (?, ?, ?, ?)",
        (teacher_id, class_name, day, time_slot)
    )

    db.commit()
    db.close()

    return redirect("/teachers?success=Timetable assigned successfully")

@app.route("/admin-delete-slot/<teacher_id>/<day>/<time_slot>")
def admin_delete_slot(teacher_id, day, time_slot):
    if "admin" not in session:
        return redirect("/")
    db = get_db()
    db.execute("DELETE FROM teacher_assignments WHERE teacher_id=? AND day=? AND time_slot=?",
               (teacher_id, day, time_slot))
    db.commit()
    db.close()
    return redirect("/teachers")

@app.route("/admin-delete-teacher/<teacher_id>")
def admin_delete_teacher(teacher_id):
    if "admin" not in session:
        return redirect("/")
    db = get_db()
    db.execute("DELETE FROM teacher_assignments WHERE teacher_id=?", (teacher_id,))
    db.execute("DELETE FROM teachers WHERE teacher_id=?", (teacher_id,))
    db.commit()
    db.close()
    return redirect("/teachers")

# BUG FIX: Added missing /search-teacher route
@app.route("/search-teacher", methods=["POST"])
def search_teacher():
    if "admin" not in session:
        return redirect("/")
    teacher_id = request.form["teacher_id"]
    db = get_db()
    teachers = db.execute("""
        SELECT t.teacher_id, t.name, t.subject, ta.class, ta.day, ta.time_slot
        FROM teachers t
        LEFT JOIN teacher_assignments ta ON t.teacher_id = ta.teacher_id
        WHERE t.teacher_id LIKE ?
    """, (f"%{teacher_id}%",)).fetchall()
    db.close()
    return render_template("teachers.html", admin=session["admin"], teachers=teachers)

# ================= STUDENTS =================
@app.route("/students")
def manage_students():
    if "admin" not in session:
        return redirect("/")
    db = get_db()
    students = db.execute("SELECT student_id, name, class FROM students WHERE active=1").fetchall()
    db.close()
    return render_template("students.html", admin=session["admin"], students=students)

@app.route("/add-student", methods=["POST"])
def add_student():
    if "admin" not in session:
        return redirect("/")
    db = get_db()
    try:
        db.execute("INSERT INTO students (student_id, name, class) VALUES (?, ?, ?)",
                   (request.form["student_id"], request.form["name"], request.form["class"]))
        db.commit()
    except sqlite3.IntegrityError:
        db.close()
        return redirect("/students?error=Student+ID+already+exists")
    db.close()
    return redirect("/students")

@app.route("/delete-student/<student_id>")
def delete_student(student_id):
    if "admin" not in session:
        return redirect("/")
    db = get_db()
    db.execute("UPDATE students SET active=0 WHERE student_id=?", (student_id,))
    db.commit()
    db.close()
    return redirect("/students")

@app.route("/view-students", methods=["POST"])
def view_students():
    if "admin" not in session:
        return redirect("/")
    class_name = request.form["class"]
    db = get_db()
    students = db.execute(
        "SELECT student_id, name, class FROM students WHERE class=? AND active=1",
        (class_name,)
    ).fetchall()
    db.close()
    return render_template("students.html", admin=session["admin"], students=students)

# BUG FIX: Added missing /search-student route
@app.route("/search-student", methods=["POST"])
def search_student():
    if "admin" not in session:
        return redirect("/")
    student_id = request.form["student_id"]
    db = get_db()
    students = db.execute(
        "SELECT student_id, name, class FROM students WHERE student_id LIKE ? AND active=1",
        (f"%{student_id}%",)
    ).fetchall()
    db.close()
    return render_template("students.html", admin=session["admin"], students=students)

@app.route("/update-class/<student_id>", methods=["POST"])
def update_class(student_id):
    if "admin" not in session:
        return redirect("/")
    new_class = request.form["new_class"]
    db = get_db()
    db.execute("UPDATE students SET class=? WHERE student_id=?", (new_class, student_id))
    db.commit()
    db.close()
    return redirect("/students")

# ================= ADMIN ATTENDANCE VIEW =================
@app.route("/attendance")
def attendance_dashboard():
    if "admin" not in session:
        return redirect("/")
    return render_template("attendance.html")

@app.route("/filter-attendance", methods=["POST"])
def filter_attendance():
    if "admin" not in session:
        return redirect("/")
    class_name = request.form["class"]
    roll = request.form.get("roll", "")
    db = get_db()
    records = db.execute("""
        SELECT a.student_id, s.name, a.date, a.hour, a.status
        FROM attendance a
        JOIN students s ON a.student_id = s.student_id
        WHERE s.class=? AND s.student_id LIKE ?
        ORDER BY a.date DESC
    """, (class_name, f"%{roll}%")).fetchall()
    db.close()
    return render_template("attendance.html", records=records)

@app.route("/admin-add-attendance", methods=["POST"])
def admin_add_attendance():
    if "admin" not in session:
        return redirect("/")
    student = request.form["student"]
    class_name = request.form["class"]
    date_value = request.form["date"]
    slot = request.form["slot"]
    status = request.form["status"]
    db = get_db()
    db.execute("""
        INSERT OR REPLACE INTO attendance (student_id, class, date, hour, status)
        VALUES (?, ?, ?, ?, ?)
    """, (student, class_name, date_value, slot, status))
    db.commit()
    db.close()
    return redirect("/attendance?success=Attendance+saved")

# ================= REPORTS (BUG FIX: all 3 report routes added) =================
@app.route("/reports")
def reports():
    if "admin" not in session:
        return redirect("/")
    db = get_db()
    classes = db.execute("SELECT DISTINCT class FROM students WHERE active=1").fetchall()
    students = db.execute("SELECT student_id, name, class FROM students WHERE active=1").fetchall()
    teachers = db.execute("SELECT teacher_id, name FROM teachers WHERE active=1").fetchall()
    db.close()
    return render_template("reports.html", classes=classes, students=students, teachers=teachers)

@app.route("/class-report", methods=["POST"])
def class_report():
    if "admin" not in session:
        return redirect("/")
    class_name = request.form["class"]
    db = get_db()
    students = db.execute(
        "SELECT student_id, name FROM students WHERE class=? AND active=1", (class_name,)
    ).fetchall()
    report_data = []
    for s in students:
        # BUG FIX: count present/absent per student in this class only
        present = db.execute(
            "SELECT COUNT(*) FROM attendance WHERE student_id=? AND class=? AND status='Present'",
            (s["student_id"], class_name)
        ).fetchone()[0]
        absent = db.execute(
            "SELECT COUNT(*) FROM attendance WHERE student_id=? AND class=? AND status='Absent'",
            (s["student_id"], class_name)
        ).fetchone()[0]
        total = present + absent
        pct = round((present / total * 100), 1) if total > 0 else 0
        report_data.append((s["student_id"], s["name"], total, present, pct))
    db.close()
    return render_template("class_report.html", class_name=class_name, report_data=report_data)

@app.route("/student-report", methods=["POST"])
def student_report():
    if "admin" not in session:
        return redirect("/")
    student_id = request.form["student_id"]
    db = get_db()
    student = db.execute(
        "SELECT student_id, name, class FROM students WHERE student_id=?", (student_id,)
    ).fetchone()
    if not student:
        db.close()
        return redirect("/reports?error=Student+not+found")
    records_raw = db.execute(
        "SELECT date, hour, status FROM attendance WHERE student_id=? ORDER BY date DESC",
        (student_id,)
    ).fetchall()
    records = [(f"{r['date']} | {r['hour']}", r["status"]) for r in records_raw]
    total = len(records)
    present = sum(1 for r in records_raw if r["status"] == "Present")
    absent = total - present
    percentage = round((present / total * 100), 1) if total > 0 else 0
    db.close()
    return render_template("student_report.html",
                           student_id=student["student_id"],
                           name=student["name"],
                           records=records,
                           total=total,
                           present=present,
                           absent=absent,
                           percentage=percentage)

@app.route("/teacher-report-view", methods=["POST"])
def teacher_report_view():
    if "admin" not in session:
        return redirect("/")
    teacher_id = request.form["teacher_id"]
    db = get_db()
    teacher = db.execute(
        "SELECT teacher_id, name FROM teachers WHERE teacher_id=?", (teacher_id,)
    ).fetchone()
    if not teacher:
        db.close()
        return redirect("/reports?error=Teacher+not+found")
    # Get all classes assigned to this teacher
    assignments = db.execute(
        "SELECT class, day, time_slot FROM teacher_assignments WHERE teacher_id=?",
        (teacher_id,)
    ).fetchall()

    # For each assigned class+slot, find dates attendance was marked
    records = []
    for a in assignments:
        dates = db.execute(
            "SELECT DISTINCT date FROM attendance WHERE class=? AND hour=? ORDER BY date DESC",
            (a["class"], a["time_slot"])
        ).fetchall()
        for d in dates:
            records.append((f"{d['date']} | {a['class']} | {a['time_slot']}", "Conducted"))

    total_conducted = len(records)
    db.close()
    return render_template("teacher_report.html",
                           teacher_id=teacher["teacher_id"],
                           name=teacher["name"],
                           assignments=assignments,
                           records=records,
                           total_conducted=total_conducted)

# ================= TEACHER LOGIN =================
@app.route("/teacher")
def teacher_login_page():
    return render_template("teacher_login.html")

# BUG FIX: teacher login now works with standard form POST (no JS fetch needed)
@app.route("/teacher-login", methods=["POST"])
def teacher_login():
    teacher_id = request.form["teacher_id"]
    password = request.form["password"]
    db = get_db()
    teacher = db.execute("SELECT * FROM teachers WHERE teacher_id=? AND active=1",
                         (teacher_id,)).fetchone()
    db.close()
    if teacher and teacher["password"] == password:
        session["teacher"] = teacher_id
        return redirect("/teacher-dashboard")
    return render_template("teacher_login.html", error="Invalid Login")

@app.route("/teacher-dashboard")
def teacher_dashboard():
    if "teacher" not in session:
        return redirect("/teacher")
    teacher_id = session["teacher"]
    db = get_db()
    teacher = db.execute("SELECT name FROM teachers WHERE teacher_id=?", (teacher_id,)).fetchone()
    timetable = db.execute(
        "SELECT class, day, time_slot FROM teacher_assignments WHERE teacher_id=?",
        (teacher_id,)
    ).fetchall()
    db.close()
    return render_template("teacher_dashboard.html",
                           timetable=timetable,
                           teacher_name=teacher["name"] if teacher else teacher_id)

@app.route("/teacher-attendance")
def teacher_attendance_select():
    if "teacher" not in session:
        return redirect("/teacher")
    teacher_id = session["teacher"]
    db = get_db()
    assignments = db.execute(
        "SELECT class, day, time_slot FROM teacher_assignments WHERE teacher_id=?",
        (teacher_id,)
    ).fetchall()
    db.close()
    return render_template("teacher_attendance_select.html", assignments=assignments)

@app.route("/teacher-attendance/<class_name>/<path:time_slot>")
def teacher_attendance_page(class_name, time_slot):
    if "teacher" not in session:
        return redirect("/teacher")
    db = get_db()
    students = db.execute(
        "SELECT student_id, name FROM students WHERE class=? AND active=1",
        (class_name,)
    ).fetchall()
    db.close()
    return render_template("teacher_attendance.html",
                           students=students,
                           class_name=class_name,
                           time_slot=time_slot,
                           today=date.today().isoformat())

# BUG FIX: student_id extraction fixed from key.split("_")[1] → key[7:]
@app.route("/teacher-mark-attendance", methods=["POST"])
def teacher_mark_attendance():
    if "teacher" not in session:
        return redirect("/teacher")
    class_name = request.form["class"]
    time_slot = request.form["time_slot"]
    date_value = request.form["date"]

    selected_date = date.fromisoformat(date_value)
    today = date.today()
    if selected_date > today:
        return render_template("teacher_attendance.html",
                               error="❌ You cannot mark attendance for future dates!",
                               class_name=class_name, time_slot=time_slot, students=[])

    db = get_db()
    for key in request.form:
        if key.startswith("status_"):
            student_id = key[7:]  # BUG FIX: was key.split("_")[1] which broke IDs with underscores
            status = request.form[key]
            db.execute("""
                INSERT OR REPLACE INTO attendance (student_id, class, date, hour, status)
                VALUES (?, ?, ?, ?, ?)
            """, (student_id, class_name, date_value, time_slot, status))
    db.commit()
    db.close()
    return redirect("/teacher-dashboard?success=Attendance+saved+successfully")

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.pop("admin", None)
    session.pop("teacher", None)
    return redirect("/")

# ================= PWA ROUTES =================
@app.route("/sw.js")
def service_worker():
    return send_from_directory("static", "sw.js",
                               mimetype="application/javascript")

@app.route("/offline.html")
def offline_page():
    return render_template("offline.html")

print("✅ Server Loaded — PWA + All bugs fixed!")

if __name__ == "__main__":
    app.run(debug=True)
