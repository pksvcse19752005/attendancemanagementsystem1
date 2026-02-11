from flask import Flask, request, jsonify, Response, send_file
from flask_cors import CORS
import sqlite3
import csv
import io
import json
from datetime import date, datetime
import hashlib
import os

app = Flask(__name__)
CORS(app)

DB_PATH = 'attendance.db'

# COMPLETE HTML EMBEDDED (No separate file needed)
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Attendance Management System</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:'Poppins',sans-serif;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh}
        .glass{background:rgba(255,255,255,0.1);backdrop-filter:blur(20px);border-radius:20px;border:1px solid rgba(255,255,255,0.2);box-shadow:0 25px 45px rgba(0,0,0,0.1)}
        .glass:hover{transform:translateY(-5px)}
        .container{min-height:100vh;padding:20px;display:flex;align-items:center;justify-content:center}
        .login-grid{display:grid;grid-template-columns:1fr 1fr;gap:50px;max-width:1000px;width:100%}
        .login-card{padding:40px;color:white}
        .login-card h2{font-size:2.5rem;margin-bottom:20px;background:linear-gradient(45deg,#fff,rgba(255,255,255,0.8));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
        .input-group{position:relative;margin-bottom:25px}
        .input-group input{width:100%;padding:15px 20px 15px 50px;background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.3);border-radius:12px;color:white;font-size:16px}
        .input-group input::placeholder{color:rgba(255,255,255,0.7)}
        .input-group i{position:absolute;left:18px;top:50%;transform:translateY(-50%);color:rgba(255,255,255,0.7)}
        .btn{width:100%;padding:15px;background:linear-gradient(45deg,#ff6b6b,#feca57);border:none;border-radius:12px;color:white;font-weight:600;cursor:pointer;transition:all 0.3s;margin-bottom:15px}
        .btn:hover{transform:translateY(-2px);box-shadow:0 15px 30px rgba(255,107,107,0.4)}
        .btn-secondary{background:linear-gradient(45deg,#4ecdc4,#44a08d)}
        .dashboard{display:none;padding:30px;max-width:1400px;margin:0 auto}
        .header{display:flex;justify-content:space-between;align-items:center;margin-bottom:30px;padding-bottom:20px;border-bottom:1px solid rgba(255,255,255,0.1)}
        .logout-btn{background:linear-gradient(45deg,#ff4757,#ff3838);padding:12px 25px;border-radius:25px;color:white;text-decoration:none;font-weight:500}
        .stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:20px;margin-bottom:30px}
        .stat-card{padding:25px;text-align:center}
        .stat-number{font-size:2.5rem;font-weight:700;margin-bottom:10px}
        .chart-container{height:400px;margin:20px 0}
        .section-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px}
        .section-card{padding:25px}
        .loading{display:inline-block;width:20px;height:20px;border:3px solid rgba(255,255,255,.3);border-radius:50%;border-top-color:#fff;animation:spin 1s infinite}
        @keyframes spin{to{transform:rotate(360deg)}}
        .toast{position:fixed;top:20px;right:20px;padding:15px 20px;border-radius:10px;color:white;font-weight:500;transform:translateX(400px);transition:all 0.3s;z-index:1000}
        .toast.show{transform:translateX(0)}
        .toast.success{background:#4caf50}.toast.error{background:#f44336}
        @media(max-width:768px){.login-grid{grid-template-columns:1fr;gap:20px}.dashboard{padding:20px}}
    </style>
</head>
<body>
    <div id="landing" class="container">
        <div class="login-grid">
            <div class="glass login-card">
                <h2><i class="fas fa-user-shield"></i> Admin Login</h2>
                <div class="input-group"><i class="fas fa-user"></i><input id="adminUser" placeholder="Username"></div>
                <div class="input-group"><i class="fas fa-lock"></i><input type="password" id="adminPass" placeholder="Password"></div>
                <button class="btn" onclick="adminLogin()"><span id="adminLoginText">Login</span><span id="adminLoading" class="loading" style="display:none"></span></button>
            </div>
            <div class="glass login-card">
                <h2><i class="fas fa-user-graduate"></i> Student Login</h2>
                <div class="input-group"><i class="fas fa-id-card"></i><input id="studentRoll" placeholder="Roll Number"></div>
                <button class="btn btn-secondary" onclick="studentLogin()"><span id="studentLoginText">Check Attendance</span><span id="studentLoading" class="loading" style="display:none"></span></button>
            </div>
        </div>
    </div>

    <div id="adminDashboard" class="dashboard">
        <div class="header">
            <h1><i class="fas fa-chalkboard-teacher"></i> Admin Dashboard</h1>
            <a class="logout-btn" onclick="logout()">Logout</a>
        </div>
        <div class="stats-grid">
            <div class="glass stat-card">
                <div class="stat-number" style="color:#4caf50" id="totalStudents">0</div>
                <div>Total Students</div>
            </div>
            <div class="glass stat-card">
                <div class="stat-number" style="color:#2196f3" id="presentCount">0</div>
                <div>Present Today</div>
            </div>
            <div class="glass stat-card">
                <div class="stat-number" style="color:#ff9800" id="attendanceRate">0%</div>
                <div>Attendance Rate</div>
            </div>
        </div>
        <div class="glass">
            <h2 style="padding:20px;color:#333">📊 Analytics</h2>
            <div class="section-grid">
                <div class="chart-container"><canvas id="analyticsChart"></canvas></div>
            </div>
        </div>
    </div>

    <div id="studentDashboard" class="dashboard">
        <div class="header">
            <h1><i class="fas fa-user-graduate"></i> Your Attendance</h1>
            <a class="logout-btn" onclick="logout()">Logout</a>
        </div>
        <div class="glass" style="padding:40px;text-align:center">
            <h2 id="studentName"></h2>
            <div style="font-size:4rem;margin:20px 0">
                <span id="todayStatus" style="padding:20px;border-radius:50%;background:linear-gradient(45deg,#4caf50,#45a049);color:white;display:inline-block">Present</span>
            </div>
        </div>
    </div>

    <div id="toast" class="toast"></div>

    <script>
        let currentUser = null;
        
        function showToast(message, type='success') {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.className = `toast ${type} show`;
            setTimeout(() => toast.classList.remove('show'), 3000);
        }

        function setLoading(btnId, show) {
            const text = document.getElementById(btnId + 'Text');
            const loading = document.getElementById(btnId + 'Loading');
            text.style.display = show ? 'none' : 'inline';
            loading.style.display = show ? 'inline-block' : 'none';
        }

        function adminLogin() {
            const username = document.getElementById('adminUser').value;
            const password = document.getElementById('adminPass').value;
            
            setLoading('adminLogin', true);
            
            fetch('/api/admin_login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username, password})
            })
            .then(res => res.json())
            .then(data => {
                setLoading('adminLogin', false);
                if(data.success) {
                    currentUser = {role: 'admin'};
                    showDashboard('admin');
                    loadAdminStats();
                } else {
                    showToast(data.message, 'error');
                }
            });
        }

        function studentLogin() {
            const rollno = document.getElementById('studentRoll').value.trim().toUpperCase();
            if(!rollno) return showToast('Enter roll number', 'error');
            
            setLoading('studentLogin', true);
            
            fetch('/api/student_login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({rollno})
            })
            .then(res => res.json())
            .then(data => {
                setLoading('studentLogin', false);
                if(data.success) {
                    currentUser = data;
                    showDashboard('student');
                    document.getElementById('studentName').textContent = data.name;
                    loadStudentStatus(data.rollno);
                } else {
                    showToast(data.message, 'error');
                }
            });
        }

        function showDashboard(type) {
            document.getElementById('landing').style.display = 'none';
            document.getElementById(type + 'Dashboard').style.display = 'block';
        }

        function logout() {
            currentUser = null;
            document.getElementById('landing').style.display = 'flex';
            document.getElementById('adminDashboard').style.display = 'none';
            document.getElementById('studentDashboard').style.display = 'none';
            document.getElementById('adminUser').value = '';
            document.getElementById('adminPass').value = '';
            document.getElementById('studentRoll').value = '';
        }

        function loadAdminStats() {
            fetch('/api/stats')
            .then(res => res.json())
            .then(data => {
                document.getElementById('totalStudents').textContent = data.total || 0;
                document.getElementById('presentCount').textContent = data.present || 0;
                document.getElementById('attendanceRate').textContent = data.rate ? data.rate + '%' : '0%';
            });
        }

        function loadStudentStatus(rollno) {
            fetch(`/api/today_status?rollno=${rollno}`)
            .then(res => res.json())
            .then(data => {
                const statusEl = document.getElementById('todayStatus');
                statusEl.textContent = data.status;
                statusEl.style.background = data.status === 'Present' ? 
                    'linear-gradient(45deg,#4caf50,#45a049)' : 
                    data.status === 'Absent' ? 'linear-gradient(45deg,#f44336,#da190b)' : 
                    'linear-gradient(45deg,#ff9800,#f57c00)';
            });
        }

        document.addEventListener('keypress', function(e) {
            if(e.key === 'Enter') {
                if(document.getElementById('landing').style.display !== 'none') {
                    if(document.activeElement.id === 'adminPass') adminLogin();
                }
            }
        });
    </script>
</body>
</html>
"""

def init_db():
    """Initialize database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS admins 
                 (username TEXT PRIMARY KEY, password_hash TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS students 
                 (rollno TEXT PRIMARY KEY, name TEXT, dept TEXT, year TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS attendance 
                 (rollno TEXT, date TEXT, status TEXT, 
                  PRIMARY KEY (rollno, date))''')
    
    # Default admin account
    default_hash = hashlib.sha256(b'admin123').hexdigest()
    c.execute('INSERT OR IGNORE INTO admins VALUES (?, ?)', ('admin', default_hash))
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

@app.route('/')
def index():
    """Serve the main application"""
    return Response(HTML_CONTENT, mimetype='text/html')

@app.route('/api/admin_login', methods=['POST'])
def admin_login():
    """Admin authentication endpoint"""
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')
    
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
    """Student authentication endpoint"""
    data = request.get_json()
    rollno = data.get('rollno', '').upper()
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT rollno, name FROM students WHERE rollno = ?', (rollno,))
    student = c.fetchone()
    conn.close()
    
    if student:
        return jsonify({
            'success': True, 
            'rollno': student[0], 
            'name': student[1]
        })
    
    return jsonify({'success': False, 'message': 'Student not found'})

@app.route('/api/stats')
def get_stats():
    """Get attendance statistics"""
    today = date.today().strftime('%Y-%m-%d')
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Total students
    c.execute('SELECT COUNT(*) FROM students')
    total_students = c.fetchone()[0]
    
    # Present students today
    c.execute('SELECT COUNT(*) FROM attendance WHERE date = ? AND status = ?', (today, 'Present'))
    present_students = c.fetchone()[0]
    
    conn.close()
    
    rate = round((present_students / total_students * 100), 1) if total_students > 0 else 0
    
    return jsonify({
        'total': total_students,
        'present': present_students,
        'rate': rate
    })

@app.route('/api/today_status')
def today_status():
    """Get today's attendance status for a student"""
    rollno = request.args.get('rollno', '').upper()
    today = date.today().strftime('%Y-%m-%d')
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT status FROM attendance WHERE rollno = ? AND date = ?', (rollno, today))
    result = c.fetchone()
    conn.close()
    
    status = result[0] if result else 'Not Marked'
    return jsonify({'status': status})

@app.route('/api/add_student', methods=['POST'])
def add_student():
    """Add new student"""
    data = request.get_json()
    rollno = data.get('rollno', '').upper()
    name = data.get('name', '')
    dept = data.get('dept', 'CSE')
    year = data.get('year', '1')
    
    if not all([rollno, name]):
        return jsonify({'success': False, 'message': 'Roll number and name required'})
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        c.execute('INSERT INTO students (rollno, name, dept, year) VALUES (?, ?, ?, ?)',
                 (rollno, name, dept, year))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': f'Student {name} added successfully'})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'message': 'Roll number already exists'})

@app.route('/api/mark_attendance', methods=['POST'])
def mark_attendance():
    """Mark student attendance"""
    data = request.get_json()
    rollno = data.get('rollno', '').upper()
    date_str = data.get('date', date.today().strftime('%Y-%m-%d'))
    status = data.get('status', 'Present')
    
    if not rollno:
        return jsonify({'success': False, 'message': 'Roll number required'})
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO attendance (rollno, date, status) VALUES (?, ?, ?)',
             (rollno, date_str, status))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': f'{rollno} marked as {status}'})

@app.route('/api/students')
def get_students():
    """Get all students"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT rollno, name, dept, year FROM students ORDER BY rollno')
    students = [{'rollno': row[0], 'name': row[1], 'dept': row[2], 'year': row[3]} 
                for row in c.fetchall()]
    conn.close()
    return jsonify(students)

@app.route('/api/download_csv')
def download_csv():
    """Download attendance as CSV"""
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
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'attendance_{date_str}.csv'
    )

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)


