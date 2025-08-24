from flask import Flask, request, jsonify
from flask_cors import CORS
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
CORS(app)  # Allow CORS for frontend locally or different origin

# Hardcoded credentials (should be in a config or env in production)
VALID_USERNAME = "DEPTCSE"
VALID_PASSWORD = "pksv"

# In-memory attendance storage: { section: { date: { regd: status } } }
attendance_data = {}

# Gmail credentials for sending mail
sender_email = "vinaypydi85@gmail.com"
sender_pass = "gbohosjvdquzkzlr"  # Use app password for Gmail SMTP


@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if username != VALID_USERNAME or password != VALID_PASSWORD:
        return jsonify({"success": False, "message": "Password is incorrect"}), 401
    return jsonify({"success": True, "message": "Login successful"}), 200

@app.route('/api/save_attendance', methods=['POST'])
def save_attendance():
    data = request.json
    section = data.get('section')
    date = data.get('date')
    records = data.get('records')  # dict of regd: status

    if not section or not date or not isinstance(records, dict):
        return jsonify({"success": False, "message": "Invalid data"}), 400

    if section not in attendance_data:
        attendance_data[section] = {}
    attendance_data[section][date] = records

    return jsonify({"success": True, "message": "Attendance saved."}), 200

@app.route('/api/load_attendance', methods=['GET'])
def load_attendance():
    section = request.args.get('section')
    date = request.args.get('date')
    if not section or not date:
        return jsonify({"success": False, "message": "Missing parameters"}), 400

    records = attendance_data.get(section, {}).get(date, {})
    return jsonify({"success": True, "records": records}), 200

@app.route('/api/reset_password', methods=['POST'])
def reset_password():
    data = request.json
    user_email = data.get('email')
    # For demo, we send a simple link or message for password reset.
    # In production, generate a tokenized link and handle securely.

    if not user_email:
        return jsonify({"success": False, "message": "Email required"}), 400

    try:
        send_reset_email(user_email)
        return jsonify({"success": True, "message": "Password reset email sent."}), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to send email: {str(e)}"}), 500

def send_reset_email(to_email):
    # Prepare message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = "Password Reset for Attendance System"
    body = (
        "Dear User,\n\n"
        "You requested a password reset for the Attendance Management System.\n"
        "Your username remains: DEPTCSE\n"
        "Your password is: pksv\n\n"
        "If you did not request this, please contact admin immediately.\n\n"
        "Best Regards,\nAttendance System Team"
    )
    msg.attach(MIMEText(body, 'plain'))

    # Connect to Gmail SMTP and send mail
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender_email, sender_pass)
        server.send_message(msg)

if __name__ == "__main__":
    # For debugging only; use proper production server for deployment
    app.run(host='0.0.0.0', port=5000, debug=True)
