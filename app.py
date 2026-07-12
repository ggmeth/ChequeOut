import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ตั้งค่าหน้าเว็บให้รองรับการแสดงผลบนมือถือ
st.set_page_config(
    page_title="ChequeOut Dashboard",
    page_icon="💵",
    layout="wide"
)

# ฟังก์ชันโหลดข้อมูลจากไฟล์ Excel ในระบบโดยตรง
@st.cache_data
def load_data():
    df = pd.read_excel("ออกเช็ค 2.xlsx")
    df.columns = df.columns.str.strip()
    
    # ล้างและจับคู่ชื่อคอลัมน์ภาษี
    for col in df.columns:
        if 'ภาษีที่หัก' in str(col):
            df = df.rename(columns={col: 'ยอดภาษีที่หัก'})
            break
            
    if 'ยอดภาษีที่หัก' not in df.columns:
        df['ยอดภาษีที่หัก'] = 0
        
    for txt_col in ['ประเภทเช็ค', 'สถานะ', 'ชื่อผู้รับเงิน']:
        if txt_col in df.columns:
            df[txt_col] = df[txt_col].astype(str).str.strip()
    
    if 'วันที่ออกเช็ค' in df.columns:
        df['วันที่ออกเช็ค'] = pd.to_datetime(df['วันที่ออกเช็ค'], errors='coerce').dt.date
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"ไม่สามารถอ่านไฟล์ข้อมูล 'ออกเช็ค 2.xlsx' ได้\nError: {e}")
    st.stop()

# --- เมนูและส่วนแสดงผลบนเว็บ ---
st.title("💵 ChequeOut ส่วนตัว")
st.markdown("ระบบรายงานข้อมูลภาพรวม ค้นหา และตรวจสอบสถานะความถูกต้องของการจ่ายเช็ค")

st.sidebar.header("🔍 ตัวกรองข้อมูล (Filters)")
valid_dates = df['วันที่ออกเช็ค'].dropna()
min_date = valid_dates.min() if not valid_dates.empty else datetime.now().date()
max_date = valid_dates.max() if not valid_dates.empty else datetime.now().date()
start_date, end_date = st.sidebar.date_input("เลือกช่วงวันที่ออกเช็ค", [min_date, max_date])

all_types = ["ทั้งหมด"] + list(df['ประเภทเช็ค'].unique()) if 'ประเภทเช็ค' in df.columns else ["ทั้งหมด"]
selected_type = st.sidebar.selectbox("ประเภทเช็ค", all_types)

all_statuses = ["ทั้งหมด"] + [s for s in df['สถานะ'].unique() if s != 'nan'] if 'สถานะ' in df.columns else ["ทั้งหมด"]
selected_status = st.sidebar.selectbox("สถานะเช็ค", all_statuses)

search_name = st.sidebar.text_input("ค้นหาชื่อผู้รับเงิน / เลขที่เช็ค")

filtered_df = df.copy()
if 'วันที่ออกเช็ค' in filtered_df.columns:
    filtered_df = filtered_df[(filtered_df['วันที่ออกเช็ค'] >= start_date) & (filtered_df['วันที่ออกเช็ค'] <= end_date)]
if selected_type != "ทั้งหมด" and 'ประเภทเช็ค' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['ประเภทเช็ค'] == selected_type]
if selected_status != "ทั้งหมด" and 'สถานะ' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['สถานะ'] == selected_status]
if search_name:
    name_cond = filtered_df['ชื่อผู้รับเงิน'].str.contains(search_name, case=False, na=False) if 'ชื่อผู้รับเงิน' in filtered_df.columns else False
    code_cond = filtered_df['เลขที่เช็ค'].str.contains(search_name, case=False, na=False) if 'เลขที่เช็ค' in filtered_df.columns else False
    filtered_df = filtered_df[name_cond | code_cond]

# สรุปตัวเลขยอดเงินสุทธิ
st.subheader("📊 สรุปข้อมูลภาพรวม")
col1, col2, col3, col4 = st.columns(4)
total_amount = pd.to_numeric(filtered_df['ยอดสุทธิในเช็ค (บาท)'], errors='coerce').sum() if 'ยอดสุทธิในเช็ค (บาท)' in filtered_df.columns else 0
total_tax = pd.to_numeric(filtered_df['ยอดภาษีที่หัก'], errors='coerce').sum()
active_cheques = filtered_df[filtered_df['สถานะ'].str.contains('จ่ายแล้ว', na=False)].shape[0] if 'สถานะ' in filtered_df.columns else 0
cancelled_cheques = filtered_df[filtered_df['สถานะ'].str.contains('ยกเลิก', na=False)].shape[0] if 'สถานะ' in filtered_df.columns else 0

with col1: st.metric("ยอดรวมจ่ายสุทธิทั้งหมด", f"{total_amount:,.2f} บาท")
with col2: st.metric("ยอดรวมภาษีที่หัก", f"{total_tax:,.2f} บาท")
with col3: st.metric("จำนวนเช็คที่จ่ายแล้ว", f"{active_cheques} ฉบับ")
with col4: st.metric("จำนวนเช็คที่ยกเลิก", f"{cancelled_cheques} ฉบับ")

st.markdown("---")
st.subheader("📋 รายการข้อมูลเช็คทั้งหมด")
st.dataframe(filtered_df, use_container_width=True)
