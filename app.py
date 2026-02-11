from flask import Flask, render_template, request, jsonify
import sqlite3
import smtplib
from email.message import EmailMessage

app = Flask(__name__)

DB_NAME = "attendance.db"


# ======================================
# DATABASE CONNECTION
# ======================================
def connect_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# ======================================
# CREATE TABLES (RUN ON START)
# ======================================
def create_tables():
    conn = connect_db()
    cur = conn.cursor()

    # Admin table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            email TEXT
        )
    """)

    # Students table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rollno TEXT UNIQUE,
            name TEXT,
            section TEXT
        )
    """)

    # Attendance table
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
    cur.execute("SELECT * FROM admin WHERE username='admin'")
    admin = cur.fetchone()

    if not admin:
        cur.execute("""
            INSERT INTO admin (username, password, email)
            VALUES (?, ?, ?)
        """, ("admin", "admin123", "yourgmail@gmail.com"))
        conn.commit()

    conn.close()


create_tables()


# ======================================
# HOME PAGE
# ======================================
@app.route("/")
def home():
    return render_template("attendance1.html")


# ======================================
# ADMIN LOGIN API
# ======================================
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
        return jsonify({"success": True, "message": "Admin Login Successful!"})
    else:
        return jsonify({"success": False, "message": "Invalid Admin Credentials"})


# ======================================
# STUDENT LOGIN API
# ======================================
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
            "section": student["section"]
        })
    else:
        return jsonify({"success": False, "message": "Student Not Found"})


# ======================================
# ADD STUDENT API
# ======================================
@app.route("/add_student", methods=["POST"])
def add_student():
    data = request.json
    rollno = data.get("rollno")
    name = data.get("name")
    section = data.get("section")

    conn = connect_db()
    cur = conn.cursor()

    try:
        cur.execute("INSERT INTO students (rollno, name, section) VALUES (?, ?, ?)",
                    (rollno, name, section))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Student Added Successfully"})
    except:
        conn.close()
        return jsonify({"success": False, "message": "Student Already Exists"})


# ======================================
# MARK ATTENDANCE API
# ======================================
@app.route("/mark_attendance", methods=["POST"])
def mark_attendance():
    data = request.json
    rollno = data.get("rollno")
    date = data.get("date")
    status = data.get("status")

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("INSERT INTO attendance (rollno, date, status) VALUES (?, ?, ?)",
                (rollno, date, status))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Attendance Marked Successfully"})


# ======================================
# GET STUDENT ATTENDANCE STATUS
# ======================================
@app.route("/get_status/<rollno>", methods=["GET"])
def get_status(rollno):
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM attendance WHERE rollno=? ORDER BY id DESC LIMIT 1", (rollno,))
    record = cur.fetchone()
    conn.close()

    if record:
        return jsonify({
            "success": True,
            "date": record["date"],
            "status": record["status"]
        })
    else:
        return jsonify({"success": False, "message": "No attendance record found"})


# ======================================
# SEND EMAIL FUNCTION
# ======================================
def send_password_email(to_email, password):
    sender_email = "yourgmail@gmail.com"
    sender_password = "YOUR_APP_PASSWORD"   # Gmail App Password

    msg = EmailMessage()
    msg["Subject"] = "Attendance System - Admin Password Recovery"
    msg["From"] = sender_email
    msg["To"] = to_email
    msg.set_content(f"Hello Sir,\n\nYour Attendance System Password is:\n\nPassword: {password}\n\nThank You.")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender_email, sender_password)
        smtp.send_message(msg)


# ======================================
# FORGOT PASSWORD API
# ======================================
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
            return jsonify({"success": True, "message": "Password sent to Gmail successfully!"})
        except Exception as e:
            return jsonify({"success": False, "message": f"Email sending failed: {str(e)}"})
    else:
        return jsonify({"success": False, "message": "Email not registered!"})


# ======================================
# RUN APP
# ======================================
if __name__ == "__main__":
    app.run(debug=True)

