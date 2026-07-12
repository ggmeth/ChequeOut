import streamlit as st
import pandas as pd
import sqlite3
import datetime
from PIL import Image
import io
import json

# 1. ตั้งค่าหน้าจอธีมสว่าง คลีน หน้าหลักกว้างขวางรองรับมือถือ
st.set_page_config(
    page_title="ChequeOut Modern All-in-One",
    page_icon="💵",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DB_NAME = "cheque_modern.db"

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

init_db()

# 3. ปรับแต่งดีไซน์ให้สว่าง ทันสมัย ตัวหนังสือใหญ่ อ่านง่าย สะอาดตา
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&display=swap');
    * { font-family: 'Sarabun', sans-serif !important; }
    .main { background-color: #f8fafc; }
    
    /* สไตล์การ์ดสรุปยอดเงิน */
    .metric-box {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 14px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        border: 1px
