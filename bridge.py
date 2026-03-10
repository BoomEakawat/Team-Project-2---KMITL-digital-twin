from flask import Flask, request
import sqlite3
import datetime

app = Flask(__name__)
DB_PATH = r"C:\Users\Boom\Documents\_University\_Classroom\2nd YEAR\2.2\Team Project\database\sensor_data.db"

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

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO "water distance" VALUES (?,?,?,?)',
                       (ts, now, min_val, max_val))
        conn.commit()
        conn.close()

        print(f"✅ Saved: Now={now}, Min={min_val}, Max={max_val}")
    return "OK"

if __name__ == '__main__':
    init_db()
    app.run(host="0.0.0.0", port=8080)
