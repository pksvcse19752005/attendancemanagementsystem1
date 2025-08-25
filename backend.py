from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import smtplib
from email.mime.text import MIMEText
from io import StringIO

app = Flask(__name__)
CORS(app)

# Simple user authentication storage (replace with secure DB)
users = {
    "admin": "adminpassword"  # Change as needed
}

attendance_data = {}  # Format: {date: {regno: {"name": name, "status": status}}}

# Gmail SMTP configuration
EMAIL_ADDRESS = "vinaypydi85@gmail.com"
EMAIL_PASSWORD = "pxbntsohbnbojhtw"  # Use without spaces

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if username in users and users[username] == password:
        return jsonify({"success": True})
    else:
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
    else:
        return jsonify({"success": False, "error": "Username not found"})

def send_reset_email():
    msg = MIMEText('Click this link to reset your password: http://yourdomain.com/reset-password')
    msg['Subject'] = 'Password Reset Link'
    msg['From'] = EMAIL_ADDRESS
    # Adjust recipient as needed
    msg['To'] = EMAIL_ADDRESS  

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

@app.route('/api/export_absentees/<date>')
def export_absentees(date):
    if date not in attendance_data:
        return "No attendance data found for this date", 404
    absentees = []
    for reg, info in attendance_data[date].items():
        if info.get('status') != 'Present':
            absentees.append(f"{reg} - {info.get('name')} - {info.get('status')}")
    absentees_str = "\n".join(absentees)
    # Send as a text file
    return send_file(
        StringIO(absentees_str),
        mimetype="text/plain",
        as_attachment=True,
        download_name=f"absentees-{date}.txt"
    )

if __name__ == '__main__':
    app.run(port=5000, debug=True)
