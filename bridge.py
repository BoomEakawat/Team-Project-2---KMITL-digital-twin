from flask import Flask, request
import sqlite3
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)
DB_PATH = r"C:\Users\Boom\Documents\_University\_Classroom\2nd YEAR\2.2\Team Project\database\sensor_data.db"

# --- ส่วนตั้งค่า Google Sheets ---
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS_FILE = "creds.json" 
SHEET_NAME = "IoT_Data"

# --- ส่วนของ Buffer (ตัวพักข้อมูล) ---
data_buffer = [] 
BUFFER_SIZE = 10 

def sync_to_sheets_batch(rows):
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
        client = gspread.authorize(creds)
        sheet = client.open(SHEET_NAME).sheet1
        
        # 1. ส่งข้อมูลชุดใหม่ไปต่อท้ายก่อน (Buffer 10 แถว)
        sheet.append_rows(rows)
        
        # 2. นับจำนวนแถวทั้งหมดที่มีใน Sheet ตอนนี้
        all_values = sheet.get_all_values()
        current_rows = len(all_values)
        
        # 3. ถ้าเกิน 201 แถว (หัวตาราง 1 + ข้อมูล 200)
        if current_rows > 288:
            # คำนวณว่าเกินมาเท่าไหร่
            excess = current_rows - 288
            
            # สั่งลบแถวที่ 2 (ข้อมูลเก่าสุด) แบบ "ลบทีเดียวหลายแถวรวด" 
            # เช่น ถ้าเกินมา 10 แถว จะลบแถวที่ 2 ถึง 11 ในคำสั่งเดียว
            sheet.delete_rows(2, 2 + excess - 1)
            print(f"🗑️ Deleted {excess} old rows. Maintained exactly 200 entries.")
        
        print(f"☁️ Successfully synced {len(rows)} rows to Google Sheets!")
        
    except Exception as e:
        print(f"❌ Sheets Batch Error: {e}")

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
    global data_buffer
    data = request.get_json()
    if data:
        now = data.get("x")
        min_val = data.get("y")
        max_val = data.get("z")
        
        # สำหรับ Database
        ts = datetime.datetime.now().isoformat()
        
        # สำหรับ Google Sheets (แก้ Format วันที่แล้ว!)
        ts_display = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. บันทึกลง SQLite
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO "water distance" VALUES (?,?,?,?)',
                       (ts, now, min_val, max_val))
        conn.commit()
        conn.close()

        # 2. เก็บข้อมูลลง Buffer (ใช้วันที่ที่แก้แล้ว)
        data_buffer.append([ts_display, now, min_val, max_val])

        # 3. ตรวจสอบว่า Buffer เต็มหรือยัง
        if len(data_buffer) >= BUFFER_SIZE:
            sync_to_sheets_batch(data_buffer)
            data_buffer = [] # ล้าง Buffer

        print(f"✅ Saved to DB: Now={now} (Buffer: {len(data_buffer)}/{BUFFER_SIZE})")
    return "OK"

if __name__ == '__main__':
    init_db()
    app.run(host="0.0.0.0", port=8080)
