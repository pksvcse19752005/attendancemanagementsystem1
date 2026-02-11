from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import sqlite3
import csv
import io
from datetime import date
import hashlib

app = Flask(__name__)
CORS(app)

DB_PATH = 'attendance.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Only create tables - NO student data
    c.execute('''CREATE TABLE IF NOT EXISTS admins 
                 (username TEXT PRIMARY KEY, password_hash TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS students 
                 (rollno TEXT PRIMARY KEY, name TEXT, dept TEXT, year TEXT, section TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS attendance 
                 (rollno TEXT, date TEXT, status TEXT, 
                  PRIMARY KEY (rollno, date))''')
    
    # Default admin only
    default_hash = hashlib.sha256(b'admin123').hexdigest()
    c.execute('INSERT OR IGNORE INTO admins VALUES (?, ?)', ('admin', default_hash))
    
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return send_file('attendance1.html')

@app.route('/api/admin_login', methods=['POST'])
def admin_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT password_hash FROM admins WHERE username = ?', (username,))
    result = c.fetchone()
    conn.close()
    
    if result and hashlib.sha256(password.encode()).hexdigest() == result[0]:
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Invalid credentials'})

@app.route('/api/student_login', methods=['POST'])
def student_login():
    data = request.json
    rollno = data.get('rollno', '').upper()
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT rollno, name FROM students WHERE rollno = ?', (rollno,))
    student = c.fetchone()
    conn.close()
    
    if student:
        return jsonify({'success': True, 'rollno': student[0], 'name': student[1]})
    return jsonify({'success': False, 'message': 'Student not found'})

@app.route('/api/students')
def get_students():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT rollno, name, dept, year FROM students ORDER BY rollno')
    students = [{'rollno': r[0], 'name': r[1], 'dept': r[2], 'year': r[3]} for r in c.fetchall()]
    conn.close()
    return jsonify(students)

@app.route('/api/stats')
def get_stats():
    today = date.today().strftime('%Y-%m-%d')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('SELECT COUNT(*) FROM students')
    total = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM attendance WHERE date = ? AND status = "Present"', (today,))
    present = c.fetchone()[0]
    
    conn.close()
    return jsonify({
        'total': total,
        'present': present,
        'rate': round((present/total)*100, 1) if total > 0 else 0
    })

@app.route('/api/add_student', methods=['POST'])
def add_student():
    data = request.json
    rollno = data.get('rollno', '').upper()
    name = data.get('name', '')
    dept = data.get('dept', '')
    year = data.get('year', '')
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO students (rollno, name, dept, year) VALUES (?, ?, ?, ?)',
                  (rollno, name, dept, year))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Student added'})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'message': 'Roll number exists'})

@app.route('/api/mark_attendance', methods=['POST'])
def mark_attendance():
    data = request.json
    rollno, date_str, status = data['rollno'], data['date'], data['status']
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO attendance (rollno, date, status) VALUES (?, ?, ?)',
              (rollno, date_str, status))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': f'{rollno} marked as {status}'})

@app.route('/api/today_status')
def today_status():
    rollno = request.args.get('rollno')
    today = date.today().strftime('%Y-%m-%d')
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT status FROM attendance WHERE rollno = ? AND date = ?', (rollno, today))
    result = c.fetchone()
    conn.close()
    
    status = result[0] if result else 'Not Marked'
    return jsonify({'status': status})

@app.route('/api/download_csv')
def download_csv():
    date_str = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT s.rollno, s.name, COALESCE(a.status, 'Absent')
                 FROM students s LEFT JOIN attendance a ON s.rollno = a.rollno AND a.date = ?
                 ORDER BY s.rollno''', (date_str,))
    records = c.fetchall()
    conn.close()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Roll No', 'Name', 'Status'])
    writer.writerows(records)
    
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'attendance_{date_str}.csv'
    )

if __name__ == '__main__':
    app.run(debug=True, port=5000)


