from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import sqlite3
import csv
from io import StringIO
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

def init_db():
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS students (
        rollno TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        dept TEXT,
        year TEXT,
        division TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rollno TEXT,
        date TEXT,
        status TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (rollno) REFERENCES students (rollno)
    )''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/admin_login', methods=['POST'])
def admin_login():
    data = request.json
    if data.get('username') == 'admin' and data.get('password') == 'password123':
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Invalid credentials'})

@app.route('/api/student_login', methods=['POST'])
def student_login():
    data = request.json
    rollno = data.get('rollno', '').strip().upper()
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    c.execute("SELECT rollno, name FROM students WHERE rollno = ?", (rollno,))
    student = c.fetchone()
    conn.close()
    if student:
        return jsonify({'success': True, 'rollno': student[0], 'name': student[1]})
    return jsonify({'success': False, 'message': 'Student not found'})

@app.route('/api/students')
def get_students():
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    c.execute("SELECT rollno, name, dept, year, division FROM students ORDER BY rollno")
    students = [{'rollno': r[0], 'name': r[1], 'dept': r[2], 'year': r[3], 'division': r[4]} for r in c.fetchall()]
    conn.close()
    return jsonify(students)

@app.route('/api/add_student', methods=['POST'])
def add_student():
    data = request.json
    rollno = data.get('rollno', '').strip().upper()
    name = data.get('name', '').strip()
    dept = data.get('dept', 'CSE')
    year = data.get('year', 'B.Tech 1st Year')
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO students (rollno, name, dept, year) VALUES (?, ?, ?, ?)", 
                 (rollno, name, dept, year))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': f'Student {name} added successfully'})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'message': 'Roll number already exists'})

@app.route('/api/mark_attendance', methods=['POST'])
def mark_attendance():
    data = request.json
    rollno, date, status = data['rollno'].strip().upper(), data['date'], data['status']
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    c.execute("SELECT id FROM attendance WHERE rollno = ? AND date = ?", (rollno, date))
    existing = c.fetchone()
    if existing:
        c.execute("UPDATE attendance SET status = ? WHERE rollno = ? AND date = ?", (status, rollno, date))
        msg = f'{rollno} updated to {status}'
    else:
        c.execute("INSERT INTO attendance (rollno, date, status) VALUES (?, ?, ?)", (rollno, date, status))
        msg = f'{rollno} marked as {status}'
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': msg})

@app.route('/api/attendance_status')
def attendance_status():
    date = request.args.get('date')
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    c.execute("SELECT rollno, status FROM attendance WHERE date = ?", (date,))
    statuses = [{'rollno': r[0], 'status': r[1]} for r in c.fetchall()]
    conn.close()
    return jsonify(statuses)

@app.route('/api/today_status')
def today_status():
    rollno = request.args.get('rollno').strip().upper()
    today = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    c.execute("SELECT status FROM attendance WHERE rollno = ? AND date = ?", (rollno, today))
    result = c.fetchone()
    conn.close()
    return jsonify({'status': result[0] if result else 'Not Marked'})

@app.route('/api/student_history')
def student_history():
    rollno = request.args.get('rollno').strip().upper()
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    c.execute("SELECT date, status FROM attendance WHERE rollno = ? ORDER BY date DESC LIMIT 30", (rollno,))
    history = [{'date': r[0], 'status': r[1]} for r in c.fetchall()]
    conn.close()
    return jsonify(history)

@app.route('/api/download_csv')
def download_csv():
    date = request.args.get('date')
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    c.execute("""
        SELECT s.rollno, s.name, s.dept, s.year, COALESCE(a.status, 'Not Marked') as status
        FROM students s LEFT JOIN attendance a ON s.rollno = a.rollno AND a.date = ?
        ORDER BY s.rollno
    """, (date,))
    rows = c.fetchall()
    conn.close()
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Roll No', 'Name', 'Department', 'Year', f'{date} Status'])
    cw.writerows(rows)
    return send_file(
        StringIO(si.getvalue()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'attendance_{date}.csv'
    )

@app.route('/api/forgot_password', methods=['POST'])
def forgot_password():
    return jsonify({'success': True, 'message': 'Reset link sent to your email'})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)

