from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from datetime import date
import csv
from flask import Response

app = Flask(__name__)
CORS(app)

DB_NAME = "attendance.db"

ADMIN_EMAIL    = "vinaypydi6@gmail.com"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

STUDENTS_DATA = [
    ('23KD1A0501','ABDUL GUFFRAN','A'),('23KD1A0502','ADAPAKA TEJASRI','A'),('23KD1A0503','ADDANKI MAHESWARI','A'),('23KD1A0504','ALAMANDA SANJANA BLESSY','A'),
    ('23KD1A0505','ALAVELLI SRIPRIYA','A'),('23KD1A0506','AAMUDALA RAJESH','A'),('23KD1A0507','APPANA PRANEETH KUMAR','A'),('23KD1A0508','BADIGANTI MANOJ','A'),
    ('23KD1A0509','BAGGAM BHAVANASRI','A'),('23KD1A0510','BALIVADA MRUDULA','A'),('23KD1A0511','BANGARU VANDHANA','A'),('23KD1A0512','BANKI SAI MONISH','A'),
    ('23KD1A0513','BATTULA SAI KUMAR','A'),('23KD1A0514','BAYYA AKHIL','A'),('23KD1A0515','BEVARA DEVI PRASAD','A'),('23KD1A0516','BHASKARA AKSHAYA KUNDANIKA','A'),
    ('23KD1A0517','BHOGAPURAPU SAI MEGHANA','A'),('23KD1A0518','BITRA GIRIDDHAR','A'),('23KD1A0519','BODASINGI SIRISHA','A'),('23KD1A0520','BODDETI VYSHNAVI','A'),
    ('23KD1A0521','BODDU APPALA RAJU','A'),('23KD1A0522','BOGADI NAGAMANI','A'),('23KD1A0523','BONTHU SRUTHI','A'),('23KD1A0524','BURADA MEGHANA','A'),
    ('23KD1A0525','CHALICHAMA LOKESH SEETHARAM','A'),('23KD1A0526','CHANDAKA BHARATH KUMAR','A'),('23KD1A0527','CHANDAKA PAVITHRA','A'),('23KD1A0528','CHAPPA BHUVANA SAI','A'),
    ('23KD1A0529','CHILAKALAPUDI SRIVALLI','A'),('23KD1A0530','CHINTALAPATI LAKSHMI','A'),('23KD1A0531','CHITROTHU RAHUL KRISHNA','A'),('23KD1A0532','CHOKKAPU MOHAN SATHVIK','A'),
    ('23KD1A0533','CHUKKA JNANACHARAN','A'),('23KD1A0534','CHUKKA SAI KIRAN','A'),('23KD1A0535','DACHEPALLI MADHUMITHA','A'),('23KD1A0537','DANDU UDAY KIRAN','A'),
    ('23KD1A0538','DASARI LOVA RAJU','A'),('23KD1A0539','DASARI MOHAN','A'),('23KD1A0540','DASARI SURESH','A'),('23KD1A0541','DATLA SEETHARAMARAJU','A'),
    ('23KD1A0542','DATTI ANU','A'),('23KD1A0543','DEEPATI MOHITH','A'),('23KD1A0544','DEVU VENKATAVIVEK','A'),('23KD1A0545','DOKARA SURESH','A'),
    ('23KD1A0546','DORA KARTHIK','A'),('23KD1A0547','DUMPALA SANYASIRAO','A'),('23KD1A0548','DUVVU TEJESWAR','A'),('23KD1A0549','ELURU BHANUSHANKAR','A'),
    ('23KD1A0550','ESSARAPU AVINASH','A'),('23KD1A0551','ETTLA MARY AKSHITHA','A'),('23KD1A0552','FARHEEN MUNAVVAR FATHIMA','A'),('23KD1A0553','GADABANTI GANESH','A'),
    ('23KD1A0554','GANDATE ROHIT KUMAR','A'),('23KD1A0555','GANDHULI MONIKA','A'),('23KD1A0556','GANDRETI GEETHA SRI','A'),('23KD1A0557','GANDUBARIKI PRAGNA','A'),
    ('23KD1A0558','GARE TEJASWINI','A'),('23KD1A0559','GARI VENKATAMANIKANTA','A'),('23KD1A0560','GEDALA CHARMILA DEVI SRI','A'),('23KD1A0561','GEDALA DIVYA','A'),
    ('23KD1A0562','GEDELA SATEESH','A'),('23KD1A0563','GOLLU ADITYA','A'),('23KD1A0564','GOLLU PAVAN KUMAR','A'),('23KD1A0565','GORLE HARITHA','A'),
    ('23KD1A0566','GOTTAPU LAKSHMI CHARAN','A'),('22KD1A0575','KANDUKURI ABHILASH','A'),('24KD5A0501','BANDARU SREERAM','A'),('24KD5A0502','BAVISETTI MANOJ KUMAR','A'),
    ('24KD5A0503','BENDI BHAVANI','A'),('24KD5A0504','BONDA SURESH','A'),('24KD5A0505','GOLAJANI JHANSI','A'),('20KD1A05G5','SIMMITI KARUNA BABU','A'),
    ('23KD1A0567','GRANDHI MANASA','B'),('23KD1A0568','GUDDALA JAHNAVI','B'),('23KD1A0569','GUDEPU YASWANTH','B'),('23KD1A0570','GUDLA BHARATHI RATHNA KUMARI','B'),
    ('23KD1A0571','GULAMAJJI BHARGAV','B'),('23KD1A0572','GUNANA SAILAJA','B'),('23KD1A0573','GUNDU PRIYANKA','B'),('23KD1A0574','GUNTUKU ABHISHEK SAI','B'),
    ('23KD1A0575','GURRALA NAGA VARSHITHA','B'),('23KD1A0576','GURUGU VINAY KUMAR','B'),('23KD1A0577','HARIDASULA HARSHA VARDHAN','B'),('23KD1A0578','IMANDI HARISH','B'),
    ('23KD1A0579','IMANDI MYTHRI','B'),('23KD1A0580','IMMIDISETTI SNEHITHA','B'),('23KD1A0581','JAMI INDUMATHI','B'),('23KD1A0582','JAMPA HARSHITHA','B'),
    ('23KD1A0583','JAMPARANGI DINESH KUMAR','B'),('23KD1A0584','JARAJAPU DURGA PRASAD','B'),('23KD1A0585','JARJAPU PRASANTH','B'),('23KD1A0586','JUTTADA SWETHA','B'),
    ('23KD1A0587','JYOTHSNA ARDHAHAKULA','B'),('23KD1A0588','KAKARLAPUDI NARASIMHA ANIRUDH VARMA','B'),('23KD1A0589','KALISETTI DEEPAK','B'),('23KD1A0590','KALISETTI HARINI','B'),
    ('23KD1A0591','KALIVARAPU NAMRATHA','B'),('23KD1A0592','KALLA VENKATA HIRAN MAAVI','B'),('23KD1A0593','KALYAMPUDI RAVI KIRAN','B'),('23KD1A0594','KALYANAM GOWTHAMI','B'),
    ('23KD1A0596','KANCHUPARTHI JYOTHSNA','B'),('23KD1A0597','KANDI ASHISH','B'),('23KD1A0598','KANURI PUJITHA','B'),('23KD1A0599','KARRI DIVYA RANI','B'),
    ('23KD1A05A0','KARRI RAKSHITHA','B'),('23KD1A05A1','KARRI SATYA GOWTHAM KUMAR REDDY','B'),('23KD1A05A2','KASIREDDY JYOTHI SHIVANANDH','B'),('23KD1A05A3','KATTAMURI PRAVALLIKA','B'),
    ('23KD1A05A4','KATTOJU ABILESH','B'),('23KD1A05A5','KELLA MITHIN KUMAR','B'),('23KD1A05A6','KILLO CHINNI PRAKASH','B'),('23KD1A05A8','KOLA ABHISHEK','B'),
    ('23KD1A05A9','KOLA VARSHINI','B'),('23KD1A05B0','KOLAGANA POORNA CHANDRA RAO','B'),('23KD1A05B1','KOLLA SRAVANI','B'),('23KD1A05B2','KOLUSU ABHINAYA ANJALI','B'),
    ('23KD1A05B3','KONADA RASHMITHA','B'),('23KD1A05B4','KONDAKA SOWMYA','B'),('23KD1A05B5','KONDAPU RAMI REDDY','B'),('23KD1A05B6','KORADA JAGADEESH','B'),
    ('23KD1A05B7','KORADA NAGA DEVI','B'),('23KD1A05B8','KOSARA AKASH','B'),('23KD1A05B9','KOSIREDDY SAI KUMAR','B'),('23KD1A05C0','KOTTAKOTA KAVERI','B'),
    ('23KD1A05C1','KOTYADA BHARGAVI','B'),('23KD1A05C2','KOTYADA MAHESH','B'),('23KD1A05C3','KOVVURI CHARAN KUMAR REDDY','B'),('23KD1A05C5','KOVVURU KIRANSAI','B'),
    ('23KD1A05C6','KURIMINELLI POOJITHA','B'),('23KD1A05C7','LENKA BHARGAVI','B'),('23KD1A05C8','LODAGALA THARUN','B'),('23KD1A05C9','MADHABATHULA MANOJ KUMAR','B'),
    ('23KD1A05D0','MAJJI BHANUSRI','B'),('23KD1A05D1','MAMIDI MARUTHI PRASAD','B'),('23KD1A05D2','NAGIREDLA SRAVANI','B'),('24KD5A0506','GOLLU DURGAPRASAD','B'),
    ('24KD5A0507','GUNDU BALU','B'),('24KD5A0508','JAJIMOGGALA SRAVANTHI','B'),('24KD5A0509','KOTNANA LAHARI','B'),('24KD5A0510','MADDI KUMAR','B'),('24KD5A0511','MANDALA MAHESH NAIDU','B'),
    ('23KD1A05D3','M BHARGAVI','C'),('23KD1A05D4','M PRAVALLIKA','C'),('23KD1A05D5','M VARAPRASAD','C'),('23KD1A05D6','M MEGHANA','C'),
    ('23KD1A05D7','M SWETHA','C'),('23KD1A05D8','M ABHINAV','C'),('23KD1A05D9','M NAVYATHA','C'),('23KD1A05E0','M SINDHUJA','C'),
    ('23KD1A05E1','M PRANATHI','C'),('23KD1A05E2','M HARSHITHA','C'),('23KD1A05E3','M SHARMILA','C'),('23KD1A05E4','M SHAILAJA','C'),
    ('23KD1A05E5','MOHSIN ALI','C'),('23KD1A05E6','M FARHEEN BEGUM','C'),('23KD1A05E7','M VAMSI KRISHNA','C'),('23KD1A05E8','M MADHURI','C'),
    ('23KD1A05E9','M SARAYU SRI','C'),('23KD1A05F0','M YUVA KIRAN','C'),('23KD1A05F1','M JYOTHSNA','C'),('23KD1A05F2','M BENSON','C'),
    ('23KD1A05F3','M BHARAT','C'),('23KD1A05F4','M MANOJ KUMAR','C'),('23KD1A05F5','N DEVI','C'),('23KD1A05F6','N ADHARSH','C'),
    ('23KD1A05F7','N SUBHASH','C'),('23KD1A05F9','N PRAVEEN KUMAR','C'),('23KD1A05G0','N KYATHI','C'),('23KD1A05G1','N PRANATHI','C'),
    ('23KD1A05G2','N HARI CHARAN','C'),('23KD1A05G3','NANADHINI M','C'),('23KD1A05G4','N CHANIKYA','C'),('23KD1A05G5','N MEGHANA','C'),
    ('23KD1A05G6','N SAITEJA','C'),('23KD1A05G7','N DRAKSHAMANI','C'),('23KD1A05G8','N LAVANYA','C'),('23KD1A05G9','N AISHWARYA','C'),
    ('23KD1A05H0','N GEETHA','C'),('23KD1A05H1','P CHIDVILAS','C'),('23KD1A05H2','P KIRAN','C'),('23KD1A05H3','P HARISHANKAR','C'),
    ('23KD1A05H4','P SAIKIRAN','C'),('23KD1A05H5','PVS POORNANANDA','C'),('23KD1A05H7','P GEETHASRI','C'),('23KD1A05H8','P KAVITHA','C'),
    ('23KD1A05I0','P VINEELA','C'),('23KD1A05I1','P SUMANTH','C'),('23KD1A05I2','P GEETHANJALI','C'),('23KD1A05I3','P DEEPIKA','C'),
    ('23KD1A05I4','P AMRUTHA','C'),('23KD1A05I6','P SRIVALLI','C'),('23KD1A05I7','P JAHNAVI','C'),('23KD1A05I8','P SURENDRA REDDY','C'),
    ('23KD1A05I9','P SRAVYA','C'),('23KD1A05J0','P SAHITH','C'),('23KD1A05J1','P BHAVYA SRI','C'),('23KD1A05J2','P MEENAKSHI','C'),
    ('23KD1A05J3','P PRIYANKA','C'),('23KD1A05J4','P CHITTI BABU','C'),('23KD1A05J5','P MYTHRI','C'),('23KD1A05J6','JAHNAVI LATHA','C'),
    ('23KD1A05J8','P VARUDHINI','C'),('24KD5A0512','P REENUKA','C'),('24KD5A0513','P NAGESHWARI','C'),('24KD5A0514','P VINAY','C'),
    ('24KD5A0515','R PREMKUMAR','C'),('24KD5A0516','S SUJATHA','C'),('24KD5A0517','S KUMARRAJA','C'),
    ('23KD1A05J9','PORAPU PADMA','D'),('23KD1A05K0','POTHINA APPALA DURGA GUNA MANASA SREE','D'),('23KD1A05K1','POTIPARTHI CHARISHMA','D'),('23KD1A05K2','POTIPIREDDI VANDANA','D'),
    ('23KD1A05K3','POTNURU LEELA KUMARI','D'),('23KD1A05K4','PUDI SANJANA','D'),('23KD1A05K5','PURIJALA RAMACHANDRA RAO','D'),('23KD1A05K6','PUSAPATI SATWIK VARMA','D'),
    ('23KD1A05K7','PUVVALA SAI BHARADWAJ','D'),('23KD1A05K8','PYLA SRAVYA','D'),('23KD1A05K9','RAGHUMANDA SAITEJA','D'),('23KD1A05L0','RAGHUMANDA SRAVANTHI','D'),
    ('23KD1A05L1','RAI CHIRANJEEVI','D'),('23KD1A05L2','RAJANA LIKHITHA','D'),('23KD1A05L3','RAJANA NAVEEN','D'),('23KD1A05L4','RAPARTHI CHANDU','D'),
    ('23KD1A05L5','REGETI SOWJANYA','D'),('23KD1A05L6','RIKKA KALYANI','D'),('23KD1A05L7','SAMBANA HARSHIT','D'),('23KD1A05L8','SANAPATHI MANJULA','D'),
    ('23KD1A05L9','SARIKI HEMANTH','D'),('23KD1A05M0','SATHI CHANDRA SEKHAR MANIKANTA REDDY','D'),('23KD1A05M1','SATHI SASINDRA CHAITANYA REDDY','D'),('23KD1A05M2','SATYAVARAPU RADHA','D'),
    ('23KD1A05M3','SETTY MOUNIKA TEJASWINI','D'),('23KD1A05M4','SHAIK ABEED','D'),('23KD1A05M5','SHEIK UMAR RAFEE','D'),('23KD1A05M6','SIDDA HITANSHA','D'),
    ('23KD1A05M7','SIMHADRI YASASWI','D'),('23KD1A05M8','SINGARAPU DIVYA','D'),('23KD1A05M9','SINKA VENU SREE','D'),('23KD1A05N0','SIRUVURI RAMYA','D'),
    ('23KD1A05N1','SRIDHARALA JASWANTH','D'),('23KD1A05N2','SUNKARI INDHU','D'),('23KD1A05N3','SUNKARI MOUNIKA','D'),('23KD1A05N4','SUNKARI VENKATA APOORVA','D'),
    ('23KD1A05N5','TADANGI KARTHIK','D'),('23KD1A05N6','TALADA VINAY KUMAR','D'),('23KD1A05N7','TALLAPUDI SALMON RAJ','D'),('23KD1A05N8','TANAVARAPU HARSHA VARDHAN','D'),
    ('23KD1A05N9','TELUKALA VIJAYKUMAR SAHU','D'),('23KD1A05O0','THAPPITA CHANDRA SEKHAR','D'),('23KD1A05O1','THONANGI KIRAN REDDY','D'),('23KD1A05O2','TIRUVEEDHULA KARTHIK','D'),
    ('23KD1A05O3','TOMPALA KARTHIK','D'),('23KD1A05O4','TULA SAI NAGA VENKATA SIRI','D'),('23KD1A05O5','UMMIREDDY GAYATRI','D'),('23KD1A05O6','UPPILI HARSHAVARDHAN','D'),
    ('23KD1A05O7','UTTARAVELLI NAVEEN KUMAR','D'),('23KD1A05O8','UYAKA SAILAJA','D'),('23KD1A05O9','VARANASI KEERTHANA','D'),('23KD1A05P0','VEJENDLA CHATURYA PHANI','D'),
    ('23KD1A05P1','VELUVALI NAVYA SREE','D'),('23KD1A05P2','VEMPADAPU SUCHITRA','D'),('23KD1A05P3','VEMPALI SAMPATH KUMAR','D'),('23KD1A05P4','VENDRAPU RAMYA SREE','D'),
    ('23KD1A05P5','VIJINIGIRI LATHA','D'),('23KD1A05P6','VUDA GEETHA MADHURI','D'),('23KD1A05P7','YANDRAPU RAJESWARI','D'),('23KD1A05P8','YARABALA USHA SREE','D'),
    ('23KD1A05P9','YAVARNA SIREESHA','D'),('23KD1A05Q0','YEJJALA SIRI','D'),('23KD1A05Q1','YENDUVA VIKRAMADITYA NAIDU','D'),('23KD1A05Q2','YERRAMSETTI GOVARDHINI','D'),
    ('23KD1A05Q3','YERUBOTHU THANEESH KARTHEEK','D'),('24KD5A0518','SURAVARAPU DURGAPRASAD','D'),('24KD5A0519','TEEDA SIRISHA','D'),('24KD5A0520','TEJA SREE PENTYALA','D'),
    ('24KD5A0521','TETAKALI LAVANYA','D'),('24KD5A0522','VADAVALASA INDRASENA','D'),('24KD5A0523','YENUGULA ANITHA','D'),('24KD5A0524','YERLAJELLA KARTHIK','D'),
    ('24KD5A0525','REDDI SANDHYA','D'),
]

def connect_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY AUTOINCREMENT, rollno TEXT UNIQUE, name TEXT, section TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY AUTOINCREMENT, rollno TEXT, date TEXT, status TEXT, UNIQUE(rollno, date))")
    for rollno, name, section in STUDENTS_DATA:
        cur.execute("INSERT OR IGNORE INTO students (rollno, name, section) VALUES (?, ?, ?)", (rollno, name, section))
    conn.commit()
    conn.close()

create_tables()

@app.route("/")
def home():
    return send_from_directory("static", "attendance1.html")

@app.route("/admin_login", methods=["POST"])
def admin_login():
    data = request.json
    if data.get("username") == ADMIN_USERNAME and data.get("password") == ADMIN_PASSWORD:
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Invalid Username or Password"})

@app.route("/student_login", methods=["POST"])
def student_login():
    rollno = request.json.get("rollno", "").upper().strip()
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM students WHERE rollno=?", (rollno,))
    s = cur.fetchone()
    conn.close()
    if s:
        return jsonify({"success": True, "rollno": s["rollno"], "name": s["name"], "section": s["section"]})
    return jsonify({"success": False, "message": "Student Not Found"})

@app.route("/get_stats", methods=["GET"])
def get_stats():
    today = date.today().isoformat()
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as total FROM students")
    total = cur.fetchone()["total"]
    cur.execute("SELECT COUNT(*) as cnt FROM attendance WHERE date=? AND status='Present'", (today,))
    present = cur.fetchone()["cnt"]
    cur.execute("SELECT COUNT(*) as cnt FROM attendance WHERE date=? AND status='Absent'", (today,))
    absent = cur.fetchone()["cnt"]
    section_counts = {}
    for sec in ['A','B','C','D']:
        cur.execute("SELECT COUNT(*) as cnt FROM students WHERE section=?", (sec,))
        section_counts[sec] = cur.fetchone()["cnt"]
    conn.close()
    rate = round((present / total) * 100, 1) if total > 0 else 0
    return jsonify({"success": True, "total": total, "present": present, "absent": absent, "rate": rate, "section_counts": section_counts})

@app.route("/get_section_students", methods=["POST"])
def get_section_students():
    data = request.json
    section = data.get("section", "A")
    att_date = data.get("date", date.today().isoformat())
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.rollno, s.name, COALESCE(a.status, 'Not Marked') as status
        FROM students s
        LEFT JOIN attendance a ON s.rollno = a.rollno AND a.date = ?
        WHERE s.section = ? ORDER BY s.rollno
    """, (att_date, section))
    students = cur.fetchall()
    conn.close()
    return jsonify({"success": True, "students": [{"rollno": r["rollno"], "name": r["name"], "status": r["status"]} for r in students]})

@app.route("/bulk_attendance", methods=["POST"])
def bulk_attendance():
    records = request.json.get("records", [])
    if not records:
        return jsonify({"success": False, "message": "No records provided"})
    conn = connect_db()
    cur = conn.cursor()
    for r in records:
        cur.execute("INSERT INTO attendance (rollno, date, status) VALUES (?, ?, ?) ON CONFLICT(rollno, date) DO UPDATE SET status=excluded.status",
                    (r["rollno"], r["date"], r["status"]))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": f"Attendance saved for {len(records)} students!"})

@app.route("/student_attendance/<rollno>", methods=["GET"])
def student_attendance(rollno):
    rollno = rollno.upper().strip()
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT date, status FROM attendance WHERE rollno=? ORDER BY date DESC", (rollno,))
    records = cur.fetchall()
    cur.execute("SELECT COUNT(*) as cnt FROM attendance WHERE rollno=? AND status='Present'", (rollno,))
    present_count = cur.fetchone()["cnt"]
    cur.execute("SELECT COUNT(*) as cnt FROM attendance WHERE rollno=? AND status='Absent'", (rollno,))
    absent_count = cur.fetchone()["cnt"]
    conn.close()
    return jsonify({"success": True, "history": [{"date": r["date"], "status": r["status"]} for r in records],
                    "present_count": present_count, "absent_count": absent_count})

@app.route("/attendance_report", methods=["POST"])
def attendance_report():
    att_date = request.json.get("date", date.today().isoformat())
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.rollno, s.name, s.section, COALESCE(a.status, 'Not Marked') as status
        FROM students s
        LEFT JOIN attendance a ON s.rollno = a.rollno AND a.date = ?
        ORDER BY s.section, s.rollno
    """, (att_date,))
    records = cur.fetchall()
    conn.close()
    return jsonify({"success": True, "report": [{"rollno": r["rollno"], "name": r["name"], "section": r["section"], "status": r["status"]} for r in records]})
@app.route('/download_report', methods=['GET'])
def download_report():
    date = request.args.get('date')
    
    if not date:
        return {"success": False, "message": "Date is required"}, 400
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.rollno, s.name, s.section, COALESCE(a.status, 'Not Marked') as status
        FROM students s
        LEFT JOIN attendance a ON s.rollno = a.rollno AND a.date = ?
        ORDER BY s.section, s.rollno
    """, (att_date,))
    records = cur.fetchall()
    conn.close()

    # Create CSV
    def generate():
        data = [["Roll No", "Name", "Section", "Status"]]
        for r in records:
            data.append([r["rollno"], r["name"], r["section"], r["status"]])

        for row in data:
            yield ",".join(row) + "\n"

    return Response(
        generate(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=attendance_{att_date}.csv"
        }
    )

# ==========================================
# FORGOT PASSWORD — SendGrid
#
# Render Dashboard → Environment → Add:
#   SENDGRID_API_KEY = SG.xxxxxxxxxxxxxxxx
#   SENDER_EMAIL     = vinaypydi6@gmail.com
#
# IMPORTANT — Verify sender in SendGrid (one time):
#   app.sendgrid.com → Settings → Sender Authentication
#   → Verify a Single Sender → use vinaypydi6@gmail.com
#   → Check Gmail inbox → click verify link → Done
# ==========================================
@app.route("/forgot_password", methods=["POST"])
def forgot_password():
    api_key = os.environ.get("SENDGRID_API_KEY", "").strip()
    sender  = os.environ.get("SENDER_EMAIL", "").strip()

    if not api_key:
        return jsonify({"success": False, "message": "SENDGRID_API_KEY not set in Render env vars"})
    if not sender:
        return jsonify({"success": False, "message": "SENDER_EMAIL not set in Render env vars"})

    try:
        message = Mail(
            from_email=sender,
            to_emails=ADMIN_EMAIL,
            subject="Attendance System - Password Recovery",
            plain_text_content=(
                "Hello Sir / Leader,\n\n"
                "Your Admin Login Credentials:\n\n"
                f"  Username : {ADMIN_USERNAME}\n"
                f"  Password : {ADMIN_PASSWORD}\n\n"
                "Thank You,\nAttendance Management System"
            )
        )
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        print(f"[SENDGRID] Status: {response.status_code}")

        if response.status_code in (200, 202):
            return jsonify({"success": True, "message": f"Password sent to {ADMIN_EMAIL}"})
        else:
            return jsonify({"success": False, "message": f"SendGrid status: {response.status_code}"})

    except Exception as e:
        err = str(e)
        print(f"[SENDGRID ERROR] {err}")
        if "401" in err:
            return jsonify({"success": False, "message": "401: Wrong API Key — check SENDGRID_API_KEY in Render"})
        if "403" in err:
            return jsonify({"success": False, "message": "403: Sender not verified — go to app.sendgrid.com → Sender Authentication → verify vinaypydi6@gmail.com"})
        return jsonify({"success": False, "message": f"Email error: {err}"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
