import streamlit as st
import pandas as pd
import sqlite3
import datetime
from PIL import Image
import io

# ตั้งค่าหน้าจอแบบสว่าง ทันสมัย และรองรับทุกหน้าจอ
st.set_page_config(
    page_title="ChequeOut Pro",
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
    
    # ย้ายข้อมูลจาก Excel เข้าฐานข้อมูล (เฉพาะครั้งแรกที่ระบบยังว่างอยู่)
    c.execute("SELECT COUNT(*) FROM cheques")
    if c.fetchone()[0] == 0:
        try:
            df = pd.read_excel("ออกเช็ค 2.xlsx")
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
                ''', (cheque_no, payee, float(amount) if not pd.isna(amount) else 0.0, date_str, status, float(tax) if not pd.isna(tax) else 0.0, 'นำเข้าเริ่มต้น'))
            conn.commit()
        except Exception:
            pass
    conn.close()

init_db()

# ปรับสไตล์สีสันให้สว่าง มินิมอล และทันสมัยดูง่าย
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-left: 5px solid #0d6efd; }
    div[data-testid="stExpander"] { background-color: #ffffff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 10px; }
    .stButton>button { border-radius: 6px; }
    </style>
""", unsafe_allow_html=True)

# ส่วนเมนูควบคุมหลักด้านข้าง
st.sidebar.markdown("## 💵 ChequeOut Pro")
menu = st.sidebar.radio("เมนูการใช้งาน", ["📊 หน้าหลัก & ตรวจสอบเช็ค", "➕ เพิ่มรายการเช็คใหม่", "⚙️ จัดการข้อมูล (แก้ไข/ลบ)"])

# --- โหมดที่ 1: หน้าหลัก ค้นหา และแสดงรูปภาพทันที ---
if menu == "📊 หน้าหลัก & ตรวจสอบเช็ค":
    st.title("📊 ระบบตรวจสอบเช็คและเอกสารเบิกจ่าย")
    
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM cheques ORDER BY date DESC", conn)
    conn.close()
    
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
        
        # ค้นหาข้อมูลแบบด่วนด้านบน
        search_query = st.text_input("🔍 พิมพ์ค้นหาด่วน (ชื่อผู้รับเงิน / เลขที่เช็ค)", placeholder="พิมพ์เพื่อค้นหา...")
        
        # ตัวกรองใน Sidebar
        st.sidebar.header("🎯 ตัวกรองเชิงลึก")
        selected_status = st.sidebar.selectbox("สถานะเช็ค", ["ทั้งหมด"] + list(df['status'].unique()))
        
        filtered_df = df.copy()
        if selected_status != "ทั้งหมด":
            filtered_df = filtered_df[filtered_df['status'] == selected_status]
        if search_query:
            filtered_df = filtered_df[
                filtered_df['payee'].str.contains(search_query, case=False, na=False) |
                filtered_df['cheque_no'].str.contains(search_query, case=False, na=False)
            ]
            
        # สรุปภาพรวมการเงิน
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("ยอดจ่ายสุทธิรวม", f"{filtered_df['amount'].sum():,.2f} บาท")
        with col2: st.metric("ยอดรวมภาษีหัก ณ ที่จ่าย", f"{filtered_df['tax'].sum():,.2f} บาท")
        with col3: st.metric("จำนวนรายการทั้งหมด", f"{filtered_df.shape[0]} ฉบับ")
            
        st.markdown("---")
        st.subheader("📋 รายการเช็คและหลักฐานเอกสารเบิกจ่าย")
        
        # ลูปแสดงรายการทั้งหมดพร้อมภาพหลักฐานทันทีเมื่อเปิดดู
        for idx, row in filtered_df.iterrows():
            with st.expander(f"📄 เลขที่เช็ค: {row['cheque_no']} | ผู้รับเงิน: {row['payee']} | ยอดเงิน: {row['amount']:,.2f} บาท"):
                col_info, col_img = st.columns([2, 1])
                with col_info:
                    st.write(f"📅 **วันที่ออกเช็ค:** {row['date']}")
                    st.write(f"📌 **สถานะ:** `{row['status']}`")
                    st.write(f"💡 **ภาษีที่หัก:** {row['tax']:,.2f} บาท")
                    st.write(f"📝 **หมายเหตุ:** {row['note'] if row['note'] else '-'}")
                
                with col_img:
                    st.markdown("**🖼️ หลักฐานเอกสารเบิกจ่าย**")
                    if row['image_bytes']:
                        try:
                            image = Image.open(io.BytesIO(row['image_bytes']))
                            st.image(image, use_container_width=True)
                        except:
                            st.caption("⚠️ ไฟล์รูปภาพชำรุด")
                    else:
                        st.caption("❌ ยังไม่มีการแนบรูปภาพหลักฐาน")
    else:
        st.info("ยังไม่มีข้อมูลจัดเก็บอยู่ในระบบ")

# --- โหมดที่ 2: ฟอร์มเพิ่มข้อมูลพร้อมปุ่มถ่ายรูป/แนบรูปหลักฐาน ---
elif menu == "➕ เพิ่มรายการเช็คใหม่":
    st.title("➕ เพิ่มรายการเช็คและหลักฐานใหม่")
    
    with st.form("add_form", clear_on_submit=True):
        c_no = st.text_input("เลขที่เช็ค")
        payee = st.text_input("ชื่อผู้รับเงิน / บริษัท")
        amount = st.number_input("ยอดเงินสุทธิในเช็ค (บาท)", min_value=0.0, step=100.0)
        tax = st.number_input("ภาษีที่หัก ณ ที่จ่าย (บาท)", min_value=0.0, step=10.0)
        date = st.date_input("วันที่ออกเช็ค", datetime.date.today())
        status = st.selectbox("สถานะเช็ค", ["จ่ายแล้ว", "รอดำเนินการ", "ยกเลิก"])
        note = st.text_area("หมายเหตุเพิ่มเติม")
        
        st.markdown("### 🖼️ หลักฐานเอกสารเบิกจ่าย")
        uploaded_file = st.file_uploader("ถ่ายภาพตัวเช็ค / ใบเสร็จ / แนบสลิปโอนเงิน", type=["png", "jpg", "jpeg"])
        
        submit_btn = st.form_submit_button("💾 บันทึกข้อมูลเข้าเว็บ")
        
        if submit_btn:
            if not c_no or not payee:
                st.error("❌ กรุณากรอกข้อมูลเลขที่เช็คและชื่อผู้รับเงินให้ครบถ้วน")
            else:
                img_bytes = uploaded_file.read() if uploaded_file is not None else None
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute('''
                    INSERT INTO cheques (cheque_no, payee, amount, date, status, tax, image_bytes, note)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (c_no, payee, amount, date.strftime('%Y-%m-%d'), status, tax, img_bytes, note))
                conn.commit()
                conn.close()
                st.success("🎉 บันทึกข้อมูลและแนบรูปภาพเรียบร้อยแล้ว!")

# --- โหมดที่ 3: ระบบแก้ไข (Edit) และ ลบ (Delete) ข้อมูลเช็ค ---
elif menu == "⚙️ จัดการข้อมูล (แก้ไข/ลบ)":
    st.title("⚙️ จัดการข้อมูล ลบ และแก้ไขรายการ")
    
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM cheques ORDER BY date DESC", conn)
    conn.close()
    
    if not df.empty:
        # เลือกรายการที่จะจัดการ
        list_options = {f"เลขที่: {row['cheque_no']} | ผู้รับ: {row['payee']} ({row['amount']:,.2f} บ.)": row['id'] for _, row in df.iterrows()}
        selected_item = st.selectbox("🔍 เลือกรายการเช็คที่ต้องการแก้ไขหรือลบ", list(list_options.keys()))
        
        item_id = list_options[selected_item]
        
        # ดึงข้อมูลตัวเลือกปัจจุบันขึ้นมาแสดงบนฟอร์ม
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT * FROM cheques WHERE id = ?", (item_id,))
        item_data = c.fetchone()
        conn.close()
        
        st.markdown("---")
        st.subheader("✏️ แก้ไขข้อมูล")
        
        # สร้างฟอร์มสำหรับแก้ข้อมูลเก่า
        with st.form("edit_form"):
            edit_c_no = st.text_input("เลขที่เช็ค", value=item_data[1])
            edit_payee = st.text_input("ชื่อผู้รับเงิน / บริษัท", value=item_data[2])
            edit_amount = st.number_input("ยอดเงินสุทธิในเช็ค (บาท)", value=float(item_data[3]))
            edit_date = st.date_input("วันที่ออกเช็ค", datetime.datetime.strptime(item_data[4], '%Y-%m-%d').date() if '-' in str(item_data[4]) else datetime.date.today())
            edit_status = st.selectbox("สถานะเช็ค", ["จ่ายแล้ว", "รอดำเนินการ", "ยกเลิก"], index=["จ่ายแล้ว", "รอดำเนินการ", "ยกเลิก"].index(item_data[5]) if item_data[5] in ["จ่ายแล้ว", "รอดำเนินการ", "ยกเลิก"] else 0)
            edit_tax = st.number_input("ภาษีที่หัก ณ ที่จ่าย (บาท)", value=float(item_data[6]) if item_data[6] else 0.0)
            edit_note = st.text_area("หมายเหตุเพิ่มเติม", value=item_data[8] if item_data[8] else "")
            
            st.markdown("🖼️ **อัปเดตภาพหลักฐานเอกสารเบิกจ่าย** (ปล่อยว่างไว้หากต้องการใช้รูปเดิม)")
            edit_uploaded_file = st.file_uploader("อัปโหลดรูปภาพใหม่เพื่อเปลี่ยนแทนรูปเดิม", type=["png", "jpg", "jpeg"])
            
            col_save, _ = st.columns([1, 4])
            with col_save:
                save_btn = st.form_submit_button("💾 บันทึกการแก้ไข")
            
            if save_btn:
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                if edit_uploaded_file is not None:
                    # ถ้ามีการแนบภาพใหม่มาให้บันทึกภาพทับด้วย
                    new_img_bytes = edit_uploaded_file.read()
                    c.execute('''
                        UPDATE cheques SET cheque_no=?, payee=?, amount=?, date=?, status=?, tax=?, image_bytes=?, note=? WHERE id=?
                    ''', (edit_c_no, edit_payee, edit_amount, edit_date.strftime('%Y-%m-%d'), edit_status, edit_tax, new_img_bytes, edit_note, item_id))
                else:
                    # หากไม่มีภาพใหม่ให้ใช้ภาพเดิมคงไว้
                    c.execute('''
                        UPDATE cheques SET cheque_no=?, payee=?, amount=?, date=?, status=?, tax=?, note=? WHERE id=?
                    ''', (edit_c_no, edit_payee, edit_amount, edit_date.strftime('%Y-%m-%d'), edit_status, edit_tax, edit_note, item_id))
                conn.commit()
                conn.close()
                st.success("บันทึกการปรับปรุงข้อมูลเรียบร้อยแล้ว!")
                st.rerun()
                
        # ส่วนงานลบข้อมูลออกจากฐานข้อมูล
        st.markdown("---")
        st.subheader("❌ ลบข้อมูลถาวร")
        st.warning("คำเตือน: หากกดปุ่มลบแล้วข้อมูลรวมถึงรูปภาพหลักฐานจะหายไปจากระบบทันทีและไม่สามารถกู้คืนได้")
        
        if st.button("🚨 ยืนยันการลบรายการนี้"):
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("DELETE FROM cheques WHERE id = ?", (item_id,))
            conn.commit()
            conn.close()
            st.success("ลบข้อมูลเช็ครายการดังกล่าวสำเร็จแล้ว!")
            st.rerun()
    else:
        st.info("ไม่มีรายการให้เข้าไปจัดการ")
