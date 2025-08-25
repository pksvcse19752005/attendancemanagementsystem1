    from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import smtplib
from email.mime.text import MIMEText
from io import StringIO

app = Flask(__name__)
CORS(app)

# Simple user authentication (use a database in production!)
users = {
    "admin": "adminpassword"
}

attendance_data = {}  # {date: {regno: {"name": name, "status": status}}}

EMAIL_ADDRESS = "vinaypydi85@gmail.com"
EMAIL_PASSWORD = "pxbntsohbnbojhtw"  # Use an app password or env variable

@app.route('/')
def home():
    return render_template('attendance.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    message = None
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        if new_password != confirm_password:
            message = "Passwords do not match."
        elif not new_password:
            message = "Password cannot be empty."
        else:
            users['admin'] = new_password
            message = "Password successfully reset for 'admin' user!"
    return render_template('reset_password.html', message=message)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if username in users and users[username] == password:
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Invalid username or password"})

@app.route('/api/forgot_password', methods=['POST'])
def forgot_password():
    data = request.json
    username = data.get('username')
    if username in users:
        try:
            send_reset_email()
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": False, "error": "Failed to send reset email"})
    return jsonify({"success": False, "error": "Username not found"})

def send_reset_email():
    msg = MIMEText('Click this link to reset your password: https://attendancemanagementsystem1-6.onrender.com/reset-password')
    msg['Subject'] = 'Password Reset Link'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = EMAIL_ADDRESS  # For demo, send to self; for real use, send to the user
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    server.send_message(msg)
    server.quit()

@app.route('/api/save', methods=['POST'])
def save_attendance():
    data = request.json
    date = data.get('date')
    attendance = data.get('attendance')
    if not date or not attendance:
        return jsonify({"success": False, "error": "Date or attendance missing"})
    attendance_data[date] = attendance
    return jsonify({"success": True})

@app.route('/api/check')
def check_attendance():
    regno = request.args.get('regno')
    date = request.args.get('date')
    if not regno or not date:
        return jsonify({"status": "Absent"})
    status = attendance_data.get(date, {}).get(regno, {}).get('status', "Absent")
    return jsonify({"status": status})

@app.route('/api/export_absentees/')
def export_absentees():
    date = request.args.get('date')
    if not date or date not in attendance_data:
        return "No attendance data found for this date", 404
    absentees = []
    for regno, info in attendance_data[date].items():
        if info.get('status') != 'Present':
            absentees.append(f"{regno} - {info.get('name')} - {info.get('status')}")
    absentees_str = "\n".join(absentees)
    return send_file(
        StringIO(absentees_str),
        mimetype="text/plain",
        as_attachment=True,
        download_name=f"absentees-{date}.txt"
    )

if __name__ == '__main__':
    app.run(port=5000, debug=True)
    
