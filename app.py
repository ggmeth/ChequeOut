import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ตั้งค่าหน้าเว็บให้ดูเก๋และรองรับมือถือได้ดี
st.set_page_config(
    page_title="ChequeOut Dashboard",
    page_icon="💵",
    layout="wide"
)

# ฟังก์ชันโหลดข้อมูลจากไฟล์ CSV ใน GitHub ของคุณ
@st.cache_data
def load_data():
    # โหลดไฟล์ .csv ที่มีอยู่ในคลังข้อมูล GitHub
    df = pd.read_csv("ออกเช็ค 2.xlsx - Sheet1.csv")
    
    # แก้ปัญหาชื่อคอลัมน์ภาษีเพี้ยน: ค้นหาคอลัมน์ที่มีคำว่า 'ภาษีที่หัก' แล้วเปลี่ยนชื่อให้เป็นมาตรฐาน
    for col in df.columns:
        if 'ภาษีที่หัก' in str(col):
            df = df.rename(columns={col: 'ยอดภาษีที่หัก'})
            break
            
    # ตรวจสอบว่าถ้ายังไม่มีคอลัมน์นี้ ให้สร้างขึ้นมาเป็นค่าว่างเพื่อไม่ให้โค้ดพัง
    if 'ยอดภาษีที่หัก' not in df.columns:
        df['ยอดภาษีที่หัก'] = 0
        
    # คลีนช่องว่างในข้อความของแต่ละคอลัมน์ ป้องกันการค้นหาไม่เจอ
    df['ประเภทเช็ค'] = df['ประเภทเช็ค'].astype(str).str.strip()
    df['สถานะ'] = df['สถานะ'].astype(str).str.strip()
    df['ชื่อผู้รับเงิน'] = df['ชื่อผู้รับเงิน'].astype(str).str.strip()
    
    # แปลงคอลัมน์วันที่ให้เป็นรูปแบบวันที่ที่ถูกต้อง
    df['วันที่ออกเช็ค'] = pd.to_datetime(df['วันที่ออกเช็ค']).dt.date
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"ไม่สามารถโหลดไฟล์ข้อมูลได้ กรุณาตรวจสอบไฟล์บน GitHub\nError: {e}")
    st.stop()

# --- ส่วนหัวของเว็บแอปพลิเคชัน ---
st.title("💵 ChequeOut ส่วนตัว")
st.markdown("ระบบรายงานข้อมูลภาพรวม ค้นหา และตรวจสอบสถานะความถูกต้องของการจ่ายเช็ค")
st.sidebar.header("🔍 ตัวกรองข้อมูล (Filters)")

# --- ตัวกรองข้อมูลใน Sidebar ---
min_date = df['วันที่ออกเช็ค'].min()
max_date = df['วันที่ออกเช็ค'].max()
start_date, end_date = st.sidebar.date_input("เลือกช่วงวันที่ออกเช็ค", [min_date, max_date])

all_types = ["ทั้งหมด"] + list(df['ประเภทเช็ค'].unique())
selected_type = st.sidebar.selectbox("ประเภทเช็ค", all_types)

all_statuses = ["ทั้งหมด"] + [s for s in df['สถานะ'].unique() if s != 'nan']
selected_status = st.sidebar.selectbox("สถานะเช็ค", all_statuses)

search_name = st.sidebar.text_input("ค้นหาชื่อผู้รับเงิน / เลขที่เช็ค")

# คำนวณการกรองข้อมูลตามปุ่มที่เลือก
filtered_df = df[
    (df['วันที่ออกเช็ค'] >= start_date) & 
    (df['วันที่ออกเช็ค'] <= end_date)
]

if selected_type != "ทั้งหมด":
    filtered_df = filtered_df[filtered_df['ประเภทเช็ค'] == selected_type]

if selected_status != "ทั้งหมด":
    filtered_df = filtered_df[filtered_df['สถานะ'] == selected_status]

if search_name:
    filtered_df = filtered_df[
        filtered_df['ชื่อผู้รับเงิน'].str.contains(search_name, case=False, na=False) |
        filtered_df['เลขที่เช็ค'].str.contains(search_name, case=False, na=False)
    ]

# --- ส่วนที่ 1: สรุปตัวเลขสำคัญ (Key Metrics) ---
st.subheader("📊 สรุปข้อมูลภาพรวม")
col1, col2, col3, col4 = st.columns(4)

total_amount = filtered_df['ยอดสุทธิในเช็ค (บาท)'].sum()
total_tax = pd.to_numeric(filtered_df['ยอดภาษีที่หัก'], errors='coerce').sum()
active_cheques = filtered_df[filtered_df['สถานะ'].str.contains('จ่ายแล้ว', na=False)].shape[0]
cancelled_cheques = filtered_df[filtered_df['สถานะ'].str.contains('ยกเลิก', na=False)].shape[0]

with col1:
    st.metric("ยอดรวมจ่ายสุทธิทั้งหมด", f"{total_amount:,.2f} บาท")
with col2:
    st.metric("ยอดรวมภาษีที่หัก", f"{total_tax:,.2f} บาท")
with col3:
    st.metric("จำนวนเช็คที่จ่ายแล้ว", f"{active_cheques} ฉบับ")
with col4:
    st.metric("จำนวนเช็คที่ยกเลิก", f"{cancelled_cheques} ฉบับ")

st.markdown("---")

# --- ส่วนที่ 2: กราฟสถิติ (Charts) ---
st.subheader("📈 แผนภูมิวิเคราะห์ข้อมูล")
chart_col1, chart_col2 = st.columns(2)

with chart_col
