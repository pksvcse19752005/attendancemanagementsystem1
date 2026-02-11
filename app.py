from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from datetime import date
import sqlite3
import hashlib
import os

app = Flask(__name__)
CORS(app, origins="*")
app.config['SECRET_KEY'] = 'your-secret-key'

DB_PATH = 'attendance.db'

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Attendance System</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-gradient-to-br from-purple-500 to-pink-500 min-h-screen py-12 px-4">
    
    <!-- LOGIN SCREEN -->
    <div id="loginScreen" class="max-w-4xl mx-auto">
        <div class="grid md:grid-cols-2 gap-8">
            <!-- ADMIN LOGIN -->
            <div class="bg-white/10 backdrop-blur-xl rounded-3xl p-12 border border-white/20 hover:scale-[1.02] transition-all duration-300">
                <h2 class="text-4xl font-bold text-white mb-8 text-center">👨‍💼 Admin Login</h2>
                <div class="space-y-4">
                    <input id="adminUser" type="text" placeholder="Username" 
                           class="w-full p-4 bg-white/20 border border-white/30 rounded-xl text-white placeholder-white/70 focus:outline-none focus:ring-2 focus:ring-white">
                    <input id="adminPass" type="password" placeholder="Password" 
                           class="w-full p-4 bg-white/20 border border-white/30 rounded-xl text-white placeholder-white/70 focus:outline-none focus:ring-2 focus:ring-white">
                    <button onclick="adminLogin()" 
                            class="w-full bg-gradient-to-r from-red-500 to-orange-500 p-4 rounded-xl text-white font-bold text-lg hover:scale-105 transition-all duration-200">
                        Login
                    </button>
                </div>
            </div>
            
            <!-- STUDENT LOGIN -->
            <div class="bg-white/10 backdrop-blur-xl rounded-3xl p-12 border border-white/20 hover:scale-[1.02] transition-all duration-300">
                <h2 class="text-4xl font-bold text-white mb-8 text-center">👨‍🎓 Student Login</h2>
                <div class="space-y-4">
                    <input id="studentRoll" type="text" placeholder="Roll Number (23KD1A0501)" 
                           class="w-full p-4 bg-white/20 border border-white/30 rounded-xl text-white placeholder-white/70 focus:outline-none focus:ring-2 focus:ring-white">
                    <button onclick="studentLogin()" 
                            class="w-full bg-gradient-to-r from-teal-500 to-emerald-500 p-4 rounded-xl text-white font-bold text-lg hover:scale-105 transition-all duration-200">
                        Check Status
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- ADMIN DASHBOARD -->
    <div id="adminDash" class="hidden max-w-6xl mx-auto">
        <div class="flex justify-between items-center mb-12">
            <h1 class="text-5xl font-bold text-white">📊 Admin Dashboard</h1>
            <button onclick="logout()" class="bg-red-500 hover:bg-red-600 text-white px-8 py-4 rounded-2xl font-bold text-xl transition-all duration-200">
                Logout
            </button>
        </div>
        
        <div class="grid md:grid-cols-3 gap-8 mb-12">
            <div class="bg-white/10 backdrop-blur-xl rounded-3xl p-8 border border-white/20 text-center">
                <div class="text-4xl font-bold text-green-400 mb-2" id="totalStudents">0</div>
                <div class="text-white text-xl">Total Students</div>
            </div>
            <div class="bg-white/10 backdrop-blur-xl rounded-3xl p-8 border border-white/20 text-center">
                <div class="text-4xl font-bold text-blue-400 mb-2" id="presentToday">0</div>
                <div class="text-white text-xl">Present Today</div>
            </div>
            <div class="bg-white/10 backdrop-blur-xl rounded-3xl p-8 border border-white/20 text-center">
                <div class="text-4xl font-bold text-yellow-400 mb-2" id="attendanceRate">0%</div>
                <div class="text-white text-xl">Attendance Rate</div>
            </div>
        </div>
        
        <div class="bg-white/10 backdrop-blur-xl rounded-3xl p-8 border border-white/20">
            <canvas id="analyticsChart" height="100"></canvas>
        </div>
    </div>

    <!-- STUDENT DASHBOARD -->
    <div id="studentDash" class="hidden max-w-2xl mx-auto">
        <div class="flex justify-between items-center mb-12">
            <h1 class="text-5xl font-bold text-white">🎯 Your Status</h1>
            <button onclick="logout()" class="bg-red-500 hover:bg-red-600 text-white px-8 py-4 rounded-2xl font-bold text-xl transition-all duration-200">
                Logout
            </button>
        </div>
        <div class="bg-white/10 backdrop-blur-xl rounded-3xl p-12 border border-white/20 text-center">
            <h2 id="studentName" class="text-3xl font-bold text-white mb-8">Student Name</h2>
            <div id="statusBadge" class="inline-block px-12 py-8 rounded-full text-4xl font-bold mx-auto mb-12 bg-gradient-to-r from-green-500 to-emerald-500 text-white shadow-2xl">
                Present
            </div>
            <canvas id="studentChart" height="200"></canvas>
        </div>
    </div>

    <!-- TOAST NOTIFICATION -->
    <div id="toast" class="fixed top-4 right-4 bg-green-500 text-white px-8 py-4 rounded-xl shadow-2xl transform translate-x-full transition-transform duration-300 font-bold z-50 hidden">
        Message
    </div>

    <script>
        let currentUser = null;
        let charts = {};

        // SIMPLE LOGIN - NO DATABASE REQUIRED
        function adminLogin() {
            const username = document.getElementById('adminUser').value.trim();
            const password = document.getElementById('adminPass').value.trim();
            
            if(username === 'admin' && password === 'admin123') {
                currentUser = { role: 'admin' };
                showScreen('adminDash');
                loadAdminStats();
                showToast('Admin login successful!');
                return;
            }
            showToast('Invalid credentials!', 'error');
        }

        function studentLogin() {
            const rollno = document.getElementById('studentRoll').value.trim().toUpperCase();
            if(!rollno) {
                showToast('Enter roll number!', 'error');
                return;
            }
            
            // Simulate student data lookup
            fetch('/api/student_status?rollno=' + rollno)
                .then(res => res.json())
                .then(data => {
                    if(data.found) {
                        currentUser = { rollno: rollno, name: data.name };
                        showScreen('studentDash');
                        document.getElementById('studentName').textContent = data.name;
                        updateStudentStatus(data.status);
                        showToast('Welcome ' + data.name + '!');
                    } else {
                        showToast('Student not found!', 'error');
                    }
                });
        }

        function showScreen(screenId) {
            document.querySelectorAll('[id$="Screen"], [id$="Dash"]').forEach(el => el.classList.add('hidden'));
            document.getElementById(screenId).classList.remove('hidden');
        }

        function logout() {
            currentUser = null;
            showScreen('loginScreen');
            document.getElementById('adminUser').value = '';
            document.getElementById('adminPass').value = '';
            document.getElementById('studentRoll').value = '';
            if(charts.analytics) charts.analytics.destroy();
            if(charts.student) charts.student.destroy();
        }

        function showToast(message, type = 'success') {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.className = `fixed top-4 right-4 px-8 py-4 rounded-xl shadow-2xl transform transition-transform duration-300 font-bold z-50 ${
                type === 'error' ? 'bg-red-500 text-white translate-x-0' : 'bg-green-500 text-white translate-x-0'
            }`;
            setTimeout(() => {
                toast.classList.add('translate-x-full');
            }, 3000);
        }

        function loadAdminStats() {
            fetch('/api/stats')
                .then(res => res.json())
                .then(data => {
                    document.getElementById('totalStudents').textContent = data.total;
                    document.getElementById('presentToday').textContent = data.present;
                    document.getElementById('attendanceRate').textContent = data.rate + '%';
                    
                    // Analytics chart
                    const ctx = document.getElementById('analyticsChart').getContext('2d');
                    if(charts.analytics) charts.analytics.destroy();
                    charts.analytics = new Chart(ctx, {
                        type: 'doughnut',
                        data: {
                            labels: ['Present', 'Absent', 'Not Marked'],
                            datasets: [{
                                data: [data.present, data.absent, data.total - data.present - data.absent],
                                backgroundColor: ['#10b981', '#ef4444', '#f59e0b']
                            }]
                        },
                        options: { responsive: true, maintainAspectRatio: false }
                    });
                });
        }

        function updateStudentStatus(status) {
            const badge = document.getElementById('statusBadge');
            badge.textContent = status;
            if(status === 'Present') {
                badge.className = 'inline-block px-12 py-8 rounded-full text-4xl font-bold mx-auto mb-12 bg-gradient-to-r from-green-500 to-emerald-500 text-white shadow-2xl';
            } else if(status === 'Absent') {
                badge.className = 'inline-block px-12 py-8 rounded-full text-4xl font-bold mx-auto mb-12 bg-gradient-to-r from-red-500 to-rose-500 text-white shadow-2xl';
            } else {
                badge.className = 'inline-block px-12 py-8 rounded-full text-4xl font-bold mx-auto mb-12 bg-gradient-to-r from-yellow-500 to-orange-500 text-white shadow-2xl';
            }
        }

        // Enter key support
        document.addEventListener('keypress', (e) => {
            if(e.key === 'Enter') {
                if(!document.getElementById('adminDash').classList.contains('hidden') || 
                   !document.getElementById('studentDash').classList.contains('hidden')) return;
                adminLogin();
            }
        });
    </script>
</body>
</html>
"""

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS attendance 
                 (rollno TEXT, date TEXT, status TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return Response(HTML_CONTENT, mimetype='text/html')

@app.route('/api/stats')
def stats():
    today = date.today().strftime('%Y-%m-%d')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Demo data
    c.execute("SELECT COUNT(*) FROM attendance WHERE date=?", (today,))
    total_records = c.fetchone()[0]
    
    conn.close()
    return jsonify({
        'total': 242,  # Your total students
        'present': min(200, total_records),
        'absent': max(0, total_records - 200),
        'rate': 85.5
    })

@app.route('/api/student_status')
def student_status():
    rollno = request.args.get('rollno', '').upper()
    today = date.today().strftime('%Y-%m-%d')
    
    # Demo student data
    students = {
        '23KD1A0501': 'ABDUL GUFFRAN',
        '23KD1A0502': 'ADAPAKA TEJASRI',
        '23KD1A0503': 'ADDANKI MAHESWARI'
    }
    
    name = students.get(rollno, f'Student {rollno}')
    status = 'Present' if rollno in students else 'Not Marked'
    
    return jsonify({
        'found': rollno in students,
        'name': name,
        'status': status
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)


