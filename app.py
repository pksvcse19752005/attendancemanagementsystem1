from flask import Flask, render_template, request, jsonify
import sqlite3
import smtplib
from email.message import EmailMessage
import os
from datetime import datetime
from flask import Flask, send_from_directory
import os
app = Flask(__name__)

DB_NAME = "attendance.db"


# ==========================================
# DATABASE CONNECTION
# ==========================================
def connect_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# ==========================================
# CREATE TABLES
# ==========================================
def create_tables():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            email TEXT UNIQUE
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rollno TEXT UNIQUE,
            name TEXT,
            department TEXT,
            year TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rollno TEXT,
            date TEXT,
            status TEXT
        )
    """)

    conn.commit()

    # Insert default admin if not exists
    cur.execute("SELECT * FROM admin WHERE username=?", ("admin",))
    admin = cur.fetchone()

    if not admin:
        cur.execute("""
            INSERT INTO admin (username, password, email)
            VALUES (?, ?, ?)
        """, ("admin", "admin123", "yourgmail@gmail.com"))
        conn.commit()

    conn.close()


create_tables()


# ==========================================
# HOME PAGE
# ==========================================

@app.route("/")
def home():
    return send_from_directory("static", "attendance1.html")


# ==========================================
# ADMIN LOGIN
# ==========================================
@app.route("/admin_login", methods=["POST"])
def admin_login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM admin WHERE username=? AND password=?", (username, password))
    admin = cur.fetchone()
    conn.close()

    if admin:
        return jsonify({"success": True, "message": "Admin Login Successful"})
    else:
        return jsonify({"success": False, "message": "Invalid Username or Password"})


# ==========================================
# STUDENT LOGIN
# ==========================================
@app.route("/student_login", methods=["POST"])
def student_login():
    data = request.json
    rollno = data.get("rollno")

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM students WHERE rollno=?", (rollno,))
    student = cur.fetchone()
    conn.close()

    if student:
        return jsonify({
            "success": True,
            "rollno": student["rollno"],
            "name": student["name"],
            "department": student["department"],
            "year": student["year"]
        })
    else:
        return jsonify({"success": False, "message": "Student Not Found"})


# ==========================================
# ADD STUDENT
# ==========================================
@app.route("/add_student", methods=["POST"])
def add_student():
    data = request.json
    rollno = data.get("rollno")
    name = data.get("name")
    department = data.get("department")
    year = data.get("year")

    conn = connect_db()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO students (rollno, name, department, year)
            VALUES (?, ?, ?, ?)
        """, (rollno, name, department, year))

        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Student Added Successfully"})
    except:
        conn.close()
        return jsonify({"success": False, "message": "Student Roll No Already Exists"})


# ==========================================
# GET ALL STUDENTS
# ==========================================
@app.route("/get_students", methods=["GET"])
def get_students():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM students")
    students = cur.fetchall()
    conn.close()

    student_list = []
    for s in students:
        student_list.append({
            "rollno": s["rollno"],
            "name": s["name"],
            "department": s["department"],
            "year": s["year"]
        })

    return jsonify({"success": True, "students": student_list})


# ==========================================
# MARK ATTENDANCE
# ==========================================
@app.route("/mark_attendance", methods=["POST"])
def mark_attendance():
    data = request.json
    rollno = data.get("rollno")
    date = data.get("date")
    status = data.get("status")

    conn = connect_db()
    cur = conn.cursor()

    # Check if already marked
    cur.execute("SELECT * FROM attendance WHERE rollno=? AND date=?", (rollno, date))
    existing = cur.fetchone()

    if existing:
        cur.execute("""
            UPDATE attendance SET status=?
            WHERE rollno=? AND date=?
        """, (status, rollno, date))
    else:
        cur.execute("""
            INSERT INTO attendance (rollno, date, status)
            VALUES (?, ?, ?)
        """, (rollno, date, status))

    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Attendance Marked Successfully"})


# ==========================================
# STUDENT CHECK ATTENDANCE HISTORY
# ==========================================
@app.route("/student_attendance/<rollno>", methods=["GET"])
def student_attendance(rollno):
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM attendance WHERE rollno=? ORDER BY date DESC", (rollno,))
    records = cur.fetchall()
    conn.close()

    history = []
    for r in records:
        history.append({
            "date": r["date"],
            "status": r["status"]
        })

    return jsonify({"success": True, "history": history})


# ==========================================
# ADMIN VIEW ATTENDANCE REPORT BY DATE
# ==========================================
@app.route("/attendance_report", methods=["POST"])
def attendance_report():
    data = request.json
    date = data.get("date")

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT students.rollno, students.name, students.department, students.year,
               attendance.status, attendance.date
        FROM students
        LEFT JOIN attendance ON students.rollno = attendance.rollno AND attendance.date = ?
    """, (date,))

    records = cur.fetchall()
    conn.close()

    report = []
    for r in records:
        report.append({
            "rollno": r["rollno"],
            "name": r["name"],
            "department": r["department"],
            "year": r["year"],
            "status": r["status"] if r["status"] else "Not Marked"
        })

    return jsonify({"success": True, "report": report})


# ==========================================
# SEND PASSWORD TO EMAIL
# ==========================================
def send_password_email(receiver_email, password):
    sender_email = "yourgmail@gmail.com"
    sender_password = "YOUR_APP_PASSWORD"  # Gmail App Password

    msg = EmailMessage()
    msg["Subject"] = "Attendance System - Password Recovery"
    msg["From"] = sender_email
    msg["To"] = receiver_email

    msg.set_content(f"""
Hello Sir/Leader,

Your Attendance System Password is:

Password: {password}

Thank you,
Attendance Management System
""")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender_email, sender_password)
        smtp.send_message(msg)


# ==========================================
# FORGOT PASSWORD API
# ==========================================
@app.route("/forgot_password", methods=["POST"])
def forgot_password():
    data = request.json
    email = data.get("email")

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM admin WHERE email=?", (email,))
    admin = cur.fetchone()
    conn.close()

    if admin:
        try:
            send_password_email(email, admin["password"])
            return jsonify({"success": True, "message": "Password Sent to Gmail Successfully!"})
        except Exception as e:
            return jsonify({"success": False, "message": f"Email Sending Failed: {str(e)}"})
    else:
        return jsonify({"success": False, "message": "Email Not Registered"})


# ==========================================
# RUN APP
# ==========================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

