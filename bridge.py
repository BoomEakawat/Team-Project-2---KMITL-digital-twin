from flask import Flask, request
import sqlite3
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)
DB_PATH = r"C:\Users\Boom\Documents\_University\_Classroom\2nd YEAR\2.2\Team Project\database\sensor_data.db"

# --- ส่วนตั้งค่า Google Sheets ---
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
# มั่นใจว่าไฟล์ creds.json อยู่โฟลเดอร์เดียวกับไฟล์นี้
CREDS_FILE = "creds.json" 
SHEET_NAME = "IoT_Data" # แก้ให้ตรงกับชื่อไฟล์ Google Sheet ของคุณ

def update_google_sheets(now, min_v, max_v):
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
        client = gspread.authorize(creds)
        # เปิด Sheet และอัปเดตแถวที่ 2 (คอลัมน์ A, B, C)
        sheet = client.open(SHEET_NAME).sheet1
        sheet.update('A2:C2', [[now, min_v, max_v]])
        print(f"☁️ Synced to Sheets: Now={now}")
    except Exception as e:
        print(f"❌ Sheets Error: {e}")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS "water distance" (
            timestamp TEXT,
            sensor_1 REAL,
            min_val REAL,
            max_val REAL
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/data', methods=['POST'])
def receive_data():
    data = request.get_json()
    if data:
        now = data.get("x")
        min_val = data.get("y")
        max_val = data.get("z")
        ts = datetime.datetime.now().isoformat()

        # 1. บันทึกลง SQLite (เหมือนเดิม)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO "water distance" VALUES (?,?,?,?)',
                       (ts, now, min_val, max_val))
        conn.commit()
        conn.close()

        # 2. ส่งข้อมูลไป Google Sheets (เพิ่มมาใหม่)
        update_google_sheets(now, min_val, max_val)

        print(f"✅ Saved: Now={now}, Min={min_val}, Max={max_val}")
    return "OK"

if __name__ == '__main__':
    init_db()
    app.run(host="0.0.0.0", port=8080)
