import streamlit as st
import pandas as pd
import sqlite3
import datetime
from PIL import Image
import io

# 1. ตั้งค่าหน้าจอธีมสว่างและรองรับการใช้งานบนมือถือ
st.set_page_config(
    page_title="ChequeOut Dashboard Pro",
    page_icon="💵",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_NAME = "cheque_private.db"

# 2. ฟังก์ชันจัดการระบบฐานข้อมูล SQLite
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
    
    # ย้ายข้อมูลจาก Excel เริ่มต้นเข้าสู่ฐานข้อมูล (เฉพาะครั้งแรกที่ระบบว่าง)
    c.execute("SELECT COUNT(*) FROM cheques")
    if c.fetchone()[0] == 0:
        try:
            df = pd.read_excel("ออกเช็ค 2.xlsx")
            import_dataframe_to_db(df)
        except Exception:
            pass
    conn.close()

def import_dataframe_to_db(df):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    df.columns = df.columns.str.strip()
    
    for _, row in df.iterrows():
        cheque_no = str(row.get('เลขที่เช็ค', '')).strip()
        payee = str(row.get('ชื่อผู้รับเงิน', '')).strip()
        amount = pd.to_numeric(row.get('ยอดสุทธิในเช็ค (บาท)', 0), errors='coerce')
        
        dt = row.get('วันที่ออกเช็ค', datetime.date.today())
        if isinstance(dt, pd.Timestamp):
            date_str = dt.strftime('%Y-%m-%d')
        elif isinstance(dt, datetime.date):
            date_str = dt.strftime('%Y-%m-%d')
        else:
            date_str = str(dt)
            
        status = str(row.get('สถานะ', 'จ่ายแล้ว')).strip()
        
        tax = 0
        for col in df.columns:
            if 'ภาษี' in str(col):
                tax = pd.to_numeric(row.get(col, 0), errors='coerce')
                break
        
        c.execute('''
            INSERT INTO cheques (cheque_no, payee, amount, date, status, tax, note)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (cheque_no, payee, float(amount) if not pd.isna(amount) else 0.0, date_str, status, float(tax) if not pd.isna(tax) else 0.0, 'นำเข้าผ่านระบบ'))
    conn.commit()
    conn.close()

init_db()

# 3. ปรับแต่ง UI ด้วย CSS ให้เป็นโทนสว่าง ทันสมัย ดูง่ายสบายตา
st.markdown("""
    <style>
    .main { background-color: #fcfdfe; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.03); border-top: 4px solid #0d6efd; }
    div[data-testid="stExpander"] { background-color: #ffffff; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); margin-bottom: 12px; border: 1px solid #eef1f6; }
    .stButton>button { border-radius: 8px; font-weight: 500; }
    .css-17l4543 { background-color: #f8f9fa; }
    h1, h2, h3 { color: #1e293b; font-family: 'Sans-serif'; }
    </style>
""", unsafe_allow_html=True)

# 4. เมนูควบคุมหลักบริเวณแถบด้านข้าง (Sidebar)
st.sidebar.markdown("# 💵 ChequeOut Pro")
st.sidebar.markdown("ระบบบริหารจัดการเช็คและเอกสารเบิกจ่าย")
st.sidebar.markdown("---")
menu = st.sidebar.radio("เลือกรายการเมนู", [
    "📊 หน้าหลัก & ตรวจสอบเช็ค", 
    "➕ เพิ่มรายการเช็คใหม่", 
    "⚙️ จัดการข้อมูล (แก้ไข/ลบ)",
    "📥 นำเข้า / 📤 ส่งออก Excel"
])

# --- โหมดที่ 1: หน้าหลัก ค้นหา และแสดงรูปภาพทันทีเมื่อเปิดดู ---
if menu == "📊 หน้าหลัก & ตรวจสอบเช็ค":
    st.title("📊 รายการเช็คและหลักฐานเอกสารเบิกจ่าย")
    
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM cheques ORDER BY date DESC", conn)
    conn.close()
    
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
        search_query = st.text_input("🔍 ค้นหาด่วน (พิมพ์ชื่อผู้รับเงิน หรือ เลขที่เช็ค)", placeholder="พิมพ์ข้อความที่ต้องการค้นหา...")
        
        st.sidebar.header("🎯 ตัวกรองข้อมูล")
        selected_status = st.sidebar.selectbox("สถานะเช็ค", ["ทั้งหมด"] + list(df['status'].unique()))
        
        filtered_df = df.copy()
        if selected_status != "ทั้งหมด":
            filtered_df = filtered_df[filtered_df['status'] == selected_status]
        if search_query:
            filtered_df = filtered_df[
                filtered_df['payee'].str.contains(search_query, case=False, na=False) |
                filtered_df['cheque_no'].str.contains(search_query, case=False, na=False)
            ]
            
        # การแสดงผลการ์ดสรุปตัวเลข
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("ยอดจ่ายสุทธิรวมทั้งหมด", f"{filtered_df['amount'].sum():,.2f} บาท")
        with col2: st.metric("ยอดรวมภาษีหัก ณ ที่จ่าย", f"{filtered_df['tax'].sum():,.2f} บาท")
        with col3: st.metric("จำนวนเอกสารในระบบ", f"{filtered_df.shape[0]} ฉบับ")
            
        st.markdown("---")
        
        # แสดงรายการแบบเปิดการ์ดดูรูปภาพทันที
        for idx
