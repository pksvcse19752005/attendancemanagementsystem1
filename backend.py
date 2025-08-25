    from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import smtplib
from email.mime.text import MIMEText
from io import StringIO

app = Flask(__name__)
CORS(app)

users = {
    "admin": "adminpassword"
}

attendance_data = {}

EMAIL_ADDRESS = "vinaypydi85@gmail.com"
EMAIL_PASSWORD = "pxbntsohbnbojhtw"  # Use environment variables in production

@app.route('/')
def home():
    return render_template('attendance.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    message = None
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        if not new_password or not confirm_password:
            message = "Both password fields are required."
        elif new_password != confirm_password:
            message = "Passwords do not match."
        else:
            users['admin'] = new_password
            message = "Password successfully changed!"
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
        except Exception:
            return jsonify({"success": False, "error": "Failed to send reset email"})
    return jsonify({"success": False, "error": "Username not found"})

def send_reset_email():
    reset_link = 'http://localhost:5000/reset-password'  # Change to your app URL in production
    html_content = f'<p>Click <a href="{reset_link}">here</a> to reset your password.</p>'
    msg = MIMEText(html_content, 'html')
    msg['Subject'] = 'Password Reset Link'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = EMAIL_ADDRESS  # Change to recipient email in production
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
    
