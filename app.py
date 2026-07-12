import streamlit as st
import pandas as pd
import sqlite3
import datetime
from PIL import Image
import io

# ตั้งค่าหน้าจอ
st.set_page_config(
    page_title="ChequeOut Pro Max",
    page_icon="💵",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_NAME = "cheque_private.db"

# ฟังก์ชันจัดการฐานข้อมูล
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS cheques (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cheque_no TEXT,
            payee TEXT,
            amount REAL,
            date TEXT,
            status TEXT,
            tax REAL,
            image_bytes BLOB,
            note TEXT
        )
    ''')
    conn.commit()
    
    # ดึงข้อมูลจาก Excel เริ่มต้นครั้งแรก (ถ้าในระบบยังไม่มีข้อมูลเลย)
    c.execute("SELECT COUNT(*) FROM cheques")
    if c.fetchone()[0] == 0:
        try:
            df = pd.read_excel("ออกเช็ค 2.xlsx")
            import_dataframe_to_db(df)
        except Exception:
            pass
    conn.close()

# ฟังก์ชันสำหรับบันทึก Dataframe เข้า Database
def import_dataframe_to_db(df):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    df.columns = df.columns.str.strip()
    
    for _, row in df.iterrows():
        cheque_no = str(row.get('เลขที่เช็ค', '')).strip()
        payee =
