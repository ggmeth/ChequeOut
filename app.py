import streamlit as st
import pandas as pd
import sqlite3
import datetime
from PIL import Image
import io

# ตั้งค่าหน้าจอ
st.set_page_config(
    page_title="ChequeOut Pro",
    page_icon="💵",
    layout="wide"
)

DB_NAME = "cheque_private.db"

# ฟังก์ชันสร้างฐานข้อมูล SQLite
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
    
    # ดึงข้อมูลจาก Excel มาใส่ในฐานข้อมูลครั้งแรก (ถ้าฐานข้อมูลยังว่างอยู่)
    c.execute("SELECT COUNT(*) FROM cheques")
    if c.fetchone()[0] == 0:
        try:
            df = pd.read_excel("ออกเช็ค 2.xlsx")
            df.columns = df.columns.str.strip()
            for _, row in df.iterrows():
                cheque_no = str(row.get('เลขที่เช็ค', '')).strip()
                payee = str(row.get('ชื่อผู้รับเงิน', '')).strip()
                amount = pd.to_numeric(row.get('ยอดสุทธิในเช็ค (บาท)', 0), errors='coerce')
                
                # จัดการวันที่
                dt = row.get('วันที่ออกเช็ค', datetime.date.today())
                if isinstance(dt, pd.Timestamp):
                    date_str = dt.strftime('%Y-%m-%d')
                elif isinstance(dt, datetime.date):
                    date_str = dt.strftime('%Y-%m-%d')
                else:
                    date_str = str(dt)
                    
                status = str(row.get('สถานะ', 'จ่ายแล้ว')).strip()
                
                # หาคอลัมน์ภาษี
                tax = 0
                for col in df.columns:
                    if 'ภาษี' in str(col):
                        tax = pd.to_numeric(row.get(col, 0), errors='coerce')
                        break
                
                c.execute('''
                    INSERT INTO cheques (cheque_no, payee, amount, date, status, tax, note)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (cheque_no, payee, float(amount) if not pd.isna(amount) else 0.0, date_str, status, float(tax) if not pd.isna(tax) else 0.0, 'นำเข้าจาก Excel'))
            conn.commit()
        except Exception as e:
            pass
    conn.close()

init_db()

# ส่วนเมนูควบคุมหลัก
st.title("💵 ChequeOut Pro (จัดการข้อมูลและหลักฐาน)")
menu = st.sidebar.selectbox("เลือกโหมดการใช้งาน", ["📊 Dashboard & ค้นหาเช็ค", "➕ เพิ่มรายการเช็คใหม่"])

# --- โหมดที่ 1: แดชบอร์ดและค้นหาข้อมูล ---
if menu == "📊 Dashboard & ค้นหาเช็ค":
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM cheques", conn)
    conn.close()
    
    if not df.empty:
        # แปลงวันที่เพื่อใช้กรอง
        df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
        
        st.sidebar.header("🔍 ตัวกรองข้อมูล")
        search_query = st.sidebar.text_input("ค้นหาชื่อผู้รับเงิน / เลขที่เช็ค")
        selected_status = st.sidebar.selectbox("สถานะเช็ค", ["ทั้งหมด"] + list(df['status'].unique()))
        
        # กรองข้อมูล
        filtered_df = df.copy()
        if selected_status != "ทั้งหมด":
            filtered_df = filtered_df[filtered_df['status'] == selected_status]
        if search_query:
            filtered_df = filtered_df[
                filtered_df['payee'].str.contains(search_query, case=False, na=False) |
                filtered_df['cheque_no'].str.contains(search_query, case=False, na=False)
            ]
            
        # ตัวเลขสำคัญ
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("ยอดรวมจ่ายสุทธิ", f"{filtered_df['amount'].sum():,.2f} บาท")
        with col2:
            st.metric("ยอดรวมภาษีหัก ณ ที่จ่าย", f"{filtered_df['tax'].sum():,.2f} บาท")
        with col3:
            st.metric("จำนวนเช็คในระบบ", f"{filtered_df.shape[0]} ฉบับ")
            
        st.markdown("---")
        
        # แสดงรายการข้อมูล
        st.subheader("📋 รายการเช็คทั้งหมด")
        for idx, row in filtered_df.iterrows():
            with st.expander(f"📄 เลขที่เช็ค: {row['cheque_no']} | ผู้รับเงิน: {row['payee']} | ยอดเงิน: {row['amount']:,.2f} บาท"):
                st.write(f"**วันที่ออกเช็ค:** {row['date']}")
                st.write(f"**สถานะ:** {row['status']}")
                st.write(f"**ภาษีที่หัก:** {row['tax']:,.2f} บาท")
                st.write(f"**หมายเหตุ:** {row['note'] if row['note'] else '-'}")
                
                # แสดงรูปหลักฐานถ้ามีคีย์ข้อมูลไว้
                if row['image_bytes']:
                    try:
                        image = Image.open(io.BytesIO(row['image_bytes']))
                        st.image(image, caption="รูปภาพหลักฐานเช็ค/สลิป", use_container_width=True)
                    except:
                        st.warning("ไม่สามารถแสดงรูปภาพหลักฐานได้")
    else:
        st.info("ยังไม่มีข้อมูลในระบบ")

# --- โหมดที่ 2: ฟอร์มเพิ่มข้อมูลและรูปภาพหลักฐาน ---
elif menu == "➕ เพิ่มรายการเช็คใหม่":
    st.subheader("📝 ฟอร์มกรอกข้อมูลเช็คและอัปโหลดหลักฐาน")
    
    with st.form("add_cheque_form", clear_on_submit=True):
        c_no = st.text_input("เลขที่เช็ค")
        payee = st.text_input("ชื่อผู้รับเงิน / บริษัท")
        amount = st.number_input("ยอดเงินสุทธิในเช็ค (บาท)", min_value=0.0, step=100.0)
        tax = st.number_input("ภาษีที่หัก ณ ที่จ่าย (บาท)", min_value=0.0, step=10.0)
        date = st.date_input("วันที่ออกเช็ค", datetime.date.today())
        status = st.selectbox("สถานะเช็ค", ["จ่ายแล้ว", "รอดำเนินการ", "ยกเลิก"])
        note = st.text_area("หมายเหตุเพิ่มเติม")
        
        # ช่องอัปโหลดรูปภาพหลักฐาน
        uploaded_file = st.file_uploader("📷 ถ่ายภาพหรือแนบรูปภาพเช็ค / สลิปเงินโอน", type=["png", "jpg", "jpeg"])
        
        submit_btn = st.form_submit_button("💾 บันทึกข้อมูลเข้าเว็บ")
        
        if submit_btn:
            if not c_no or not payee:
                st.error("❌ กรุณากรอกเลขที่เช็คและชื่อผู้รับเงินก่อนบันทึก")
            else:
                img_bytes = None
                if uploaded_file is not None:
                    img_bytes = uploaded_file.read()
                    
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute('''
                    INSERT INTO cheques (cheque_no, payee, amount, date, status, tax, image_bytes, note)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (c_no, payee, amount, date.strftime('%Y-%m-%d'), status, tax, img_bytes, note))
                conn.commit()
                conn.close()
                st.success("🎉 บันทึกข้อมูลและภาพหลักฐานเรียบร้อยแล้ว! ไปดูที่แท็บ Dashboard ได้เลยครับ")
