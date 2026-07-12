import streamlit as st
import pandas as pd
import sqlite3
import datetime
from PIL import Image
import io
import json

# 1. ตั้งค่าหน้าจอธีมสว่าง Modern & Clean รองรับหน้าจอมือถือและคอมพิวเตอร์
st.set_page_config(
    page_title="ChequeOut Modern Pro",
    page_icon="💵",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DB_NAME = "cheque_data_v3.db"

# 2. ฟังก์ชันจัดการฐานข้อมูล
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
            cheque_type TEXT,
            images_json TEXT,
            note TEXT
        )
    ''')
    conn.commit()
    conn.close()

# ฟังก์ชันบันทึกกลุ่มข้อมูลจาก Excel โดยตัดคำว่า "นำเข้าจาก excel" ออกตามคำขอ
def import_dataframe_to_db(df):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    df.columns = df.columns.str.strip()
    
    for _, row in df.iterrows():
        cheque_no = str(row.get('เลขที่เช็ค', '')).strip()
        payee = str(row.get('ชื่อผู้รับเงิน', '')).strip()
        amount = pd.to_numeric(row.get('ยอดสุทธิในเช็ค (บาท)', 0), errors='coerce')
        
        dt = row.get('วันที่ออกเช็ค', datetime.date.today())
        if isinstance(dt, pd.Timestamp) or isinstance(dt, datetime.date):
            date_str = dt.strftime('%Y-%m-%d')
        else:
            date_str = str(dt)
            
        status = str(row.get('สถานะ', 'จ่ายแล้ว')).strip()
        c_type = str(row.get('ประเภทเช็ค', 'เช็ครายได้')).strip()
        # ปรับให้หมายเหตุว่างไว้ (ไม่มีคำว่านำเข้าจาก Excel กวนใจ)
        note_val = str(row.get('หมายเหตุ', '')).strip() if pd.notna(row.get('หมายเหตุ')) else ''
        
        tax = 0
        for col in df.columns:
            if 'ภาษี' in str(col):
                tax = pd.to_numeric(row.get(col, 0), errors='coerce')
                break
        
        c.execute('''
            INSERT INTO cheques (cheque_no, payee, amount, date, status, tax, cheque_type, images_json, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (cheque_no, payee, float(amount) if not pd.isna(amount) else 0.0, date_str, status, float(tax) if not pd.isna(tax) else 0.0, c_type, "[]", note_val))
    conn.commit()
    conn.close()

init_db()

# 3. ตกแต่งหน้าตาแอปด้วย CSS และกำหนดสีสถานะตามสั่ง
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&display=swap');
    html, body, [class*="css"]  { font-family: 'Sarabun', sans-serif !important; }
    .main { background-color: #f0f2f6; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border-radius: 10px 10px 0px 0px;
        padding: 10px 20px;
        border: 1px solid #e6e9ef;
        font-weight: bold;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        text-align: center;
        border-top: 5px solid #007bff;
    }
    .cheque-box {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 15px;
        border: 1px solid #e1e4e8;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        margin-bottom: 5px;
    }
    .label-blue { color: #007bff; font-weight: bold; }
    
    /* สีของสถานะตามเงื่อนไข */
    .status-green { background-color: #d1e7dd; color: #0f5132; padding: 4px 12px; border-radius: 10px; font-size
