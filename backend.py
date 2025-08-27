from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import smtplib
from email.mime.text import MIMEText
from io import BytesIO
import random
import string
import pandas as pd

app = Flask(__name__)
CORS(app)

users = {
    "DEPTCSE": "pksv"
}

attendance_data = {}  # {date: {regno: {"name": name, "status": status, "section": section}}}

EMAIL_ADDRESS = "vinaypydi85@gmail.com"
EMAIL_PASSWORD = "pxbntsohbnbojhtw"

@app.route('/')
def home():
    return render_template('attendance.html')

@app.route('/reset-password')
def reset_password():
    return "<h2>Password Reset Page - Feature under construction.</h2>"

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
            temp_password = ''.join(random.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(8))
            users[username] = temp_password
            msg = MIMEText(f'Your temporary password is: {temp_password}\nPlease use this password to login and change it immediately.')
            msg['Subject'] = 'Your Temporary Password'
            msg['From'] = EMAIL_ADDRESS
            msg['To'] = EMAIL_ADDRESS
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": False, "error": "Failed to send reset email"})
    return jsonify({"success": False, "error": "Username not found"})

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

@app.route('/api/export_all_attendance/')
def export_all_attendance():
    # Combine all dates/sections into a single Excel sheet
    combined_rows = []
    for date, daily_data in attendance_data.items():
        for regno, info in daily_data.items():
            combined_rows.append({
                "Date": date,
                "Reg No": regno,
                "Name": info.get('name', ''),
                "Section": info.get('section', ''),
                "Status": info.get('status', '')
            })
    if not combined_rows:
        return "No attendance data found", 404

    df = pd.DataFrame(combined_rows)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name="Attendance", index=False)
    output.seek(0)

    filename = "full_attendance_history.xlsx"
    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=filename
    )

if __name__ == '__main__':
    app.run(port=5000, debug=True)
