import streamlit as st
import pandas as pd
import sqlite3
import datetime
from PIL import Image
import io

# 1. ตั้งค่าหน้าจอธีมสว่าง คลีน และรองรับมือถือ
st.set_page_config(
    page_title="ChequeOut Pro Max",
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
    
    # นำเข้าข้อมูลเริ่มต้นจาก Excel (ถ้าฐานข้อมูลยังว่างเปล่า)
    c.execute("SELECT COUNT(*) FROM cheques")
    if c.fetchone()[0] == 0:
        try:
            df = pd.read_excel("ออกเช็ค 2.xlsx")
            import_dataframe_to_db(df)
        except Exception:
            pass
    conn.close()

# ฟังก์ชันสำหรับบันทึกข้อมูลแบบกลุ่ม (Bulk Import) จาก Dataframe เข้าสู่ Database
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
        ''', (cheque_no, payee, float(amount) if not pd.isna(amount) else 0.0, date_str, status, float(tax) if not pd.isna(tax) else 0.0, 'นำเข้าไฟล์ระบบ'))
    conn.commit()
    conn.close()

init_db()

# 3. ตกแต่งหน้าตาแอปพลิเคชัน (Custom UI CSS) ให้ดูสว่าง มินิมอล และสบายตา
st.markdown("""
    <style>
    .main { background-color: #fcfdfe; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.03); border-top: 4px solid #0d6efd; }
    div[data-testid="stExpander"] { background-color: #ffffff; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); border: 1px solid #e9ecef; margin-bottom: 12px; }
    .stButton>button { border-radius: 8px; font-weight: bold; }
    h1, h2, h3 { color: #212529; font-family: 'Inter', sans-serif; }
    </style>
""", unsafe_allow_html=True)

# 4. เมนูควบคุมด้านข้าง (Sidebar Navigation)
st.sidebar.markdown("## 💵 ChequeOut Pro Max")
menu = st.sidebar.radio("เมนูการใช้งาน", [
    "📊 หน้าหลัก & ตรวจสอบเช็ค", 
    "➕ เพิ่มรายการเช็คใหม่", 
    "⚙️ จัดการข้อมูล (แก้ไข/ลบ)",
    "📥 นำเข้า / 📤 ส่งออก Excel"
])

# --- 📁 โหมดที่ 1: หน้าหลัก ค้นหา และแสดงรูปภาพหลักฐานทันที ---
if menu == "📊 หน้าหลัก & ตรวจสอบเช็ค":
    st.title("📊 รายการเช็คและเอกสารเบิกจ่าย")
    
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM cheques ORDER BY date DESC", conn)
    conn.close()
    
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
        search_query = st.text_input("🔍 พิมพ์ค้นหาด่วน (ชื่อผู้รับเงิน / เลขที่เช็ค)", placeholder="พิมพ์สิ่งที่ต้องการค้นหาที่นี่...")
        
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
            
        # สรุปยอดเงินในสไตล์การ์ดสว่าง
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("ยอดรวมจ่ายสุทธิทั้งหมด", f"{filtered_df['amount'].sum():,.2f} บาท")
        with col2: st.metric("ยอดรวมภาษีหัก ณ ที่จ่าย", f"{filtered_df['tax'].sum():,.2f} บาท")
        with col3: st.metric("จำนวนเอกสารในระบบ", f"{filtered_df.shape[0]} ฉบับ")
            
        st.markdown("---")
        st.subheader("📋 รายการข้อมูลและหลักฐานภาพถ่าย")
        
        # แสดงรายการแบบเปิดการ์ดออก พร้อมโชว์รูปภาพในตัวทันที
        for idx, row in filtered_df.iterrows():
            with st.expander(f"📄 เลขที่เช็ค: {row['cheque_no']} | ผู้รับเงิน: {row['payee']} | ยอดสุทธิ: {row['amount']:,.2f} บาท"):
                col_info, col_img = st.columns([3, 2])
                with col_info:
                    st.markdown(f"📅 **วันที่ออกเช็ค:** {row['date']}")
                    st.markdown(f"📌 **สถานะรายการ:** `{row['status']}`")
                    st.markdown(f"💡 **ภาษีหัก ณ ที่จ่าย:** {row['tax']:,.2f} บาท")
                    st.markdown(f"📝 **หมายเหตุ:** {row['note'] if row['note'] else '-'}")
                
                with col_img:
                    st.markdown("**🖼️ รูปภาพหลักฐานเอกสารเบิกจ่าย**")
                    if row['image_bytes']:
                        try:
                            image = Image.open(io.BytesIO(row['image_bytes']))
                            st.image(image, use_container_width=True)
                        except:
                            st.caption("⚠️ ไฟล์รูปภาพมีข้อผิดพลาด")
                    else:
                        st.caption("❌ ยังไม่มีการแนบรูปถ่ายหลักฐาน")
    else:
        st.info("ยังไม่มีข้อมูลจัดเก็บอยู่ในระบบ สามารถไปป้อนข้อมูลหรือนำเข้าไฟล์ได้ที่เมนูด้านซ้าย")

# --- ➕ โหมดที่ 2: ฟอร์มเพิ่มข้อมูลและภาพถ่ายหลักฐาน ---
elif menu == "➕ เพิ่มรายการเช็คใหม่":
    st.title("➕ เพิ่มรายการเช็คและหลักฐานใหม่")
    
    with st.form("add_form", clear_on_submit=True):
        c_no = st.text_input("เลขที่เช็ค")
        payee = st.text_input("ชื่อผู้รับเงิน / บริษัท / หน่วยงาน")
        amount = st.number_input("ยอดเงินสุทธิในเช็ค (บาท)", min_value=0.0, step=100.0)
        tax = st.number_input("ภาษีที่หัก ณ ที่จ่าย (บาท)", min_value=0.0, step=10.0)
        date = st.date_input("วันที่ออกเช็ค", datetime.date.today())
        status = st.selectbox("สถานะเช็ค", ["จ่ายแล้ว", "รอดำเนินการ", "ยกเลิก"])
        note = st.text_area("หมายเหตุเพิ่มเติม")
        
        st.markdown("### 🖼️ แนบรูปภาพหลักฐานเอกสารเบิกจ่าย")
        uploaded_file = st.file_uploader("ถ่ายรูปภาพเช็ค / แนบใบเสร็จ / รูปสลิปโอนเงิน", type=["png", "jpg", "jpeg"])
        
        submit_btn = st.form_submit_button("💾 บันทึกข้อมูลลงระบบ")
        
        if submit_btn:
            if not c_no or not payee:
                st.error("❌ กรุณากรอกเลขที่เช็คและชื่อผู้รับเงินก่อนทำการบันทึก")
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
                st.success("🎉 บันทึกข้อมูลและจัดเก็บรูปภาพหลักฐานสำเร็จ!")

# --- ⚙️ โหมดที่ 3: ระบบแก้ไขข้อมูลและลบรายการ ---
elif menu == "⚙️ จัดการข้อมูล (แก้ไข/ลบ)":
    st.title("⚙️ แก้ไขและลบรายการเช็ค")
    
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM cheques ORDER BY date DESC", conn)
    conn.close()
    
    if not df.empty:
        list_options = {f"เลขที่: {row['cheque_no']} | ผู้รับ: {row['payee']} ({row['amount']:,.2f} บ.)": row['id'] for _, row in df.iterrows()}
        selected_item = st.selectbox("🔍 เลือกรายการเช็คที่ต้องการดำเนินการ", list(list_options.keys()))
        item_id = list_options[selected_item]
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT * FROM cheques WHERE id = ?", (item_id,))
        item_data = c.fetchone()
        conn.close()
        
        st.markdown("---")
        st.subheader("✏️ ฟอร์มแก้ไขข้อมูล")
        
        with st.form("edit_form"):
            edit_c_no = st.text_input("เลขที่เช็ค", value=item_data[1])
            edit_payee = st.text_input("ชื่อผู้รับเงิน / บริษัท", value=item_data[2])
            edit_amount = st.number_input("ยอดเงินสุทธิในเช็ค (บาท)", value=float(item_data[3]))
            
            try:
                current_date = datetime.datetime.strptime(item_data[4], '%Y-%m-%d').date()
            except:
                current_date = datetime.date.today()
                
            edit_date = st.date_input("วันที่ออกเช็ค", current_date)
            edit_status = st.selectbox("สถานะเช็ค", ["จ่ายแล้ว", "รอดำเนินการ", "ยกเลิก"], index=["จ่ายแล้ว", "รอดำเนินการ", "ยกเลิก"].index(item_data[5]) if item_data[5] in ["จ่ายแล้ว", "รอดำเนินการ", "ยกเลิก"] else 0)
            edit_tax = st.number_input("<b>ภาษีที่หัก ณ ที่จ่าย (บาท)</b>", value=float(item_data[6]) if item_data[6] else 0.0)
            edit_note = st.text_area("หมายเหตุเพิ่มเติม", value=item_data[8] if item_data[8] else "")
            
            st.markdown("🖼️ **อัปเดตเปลี่ยนภาพหลักฐานเอกสารเบิกจ่าย** (เว้นว่างไว้หากต้องการใช้รูปเดิม)")
            edit_uploaded_file = st.file_uploader("อัปโหลดรูปภาพหลักฐานใหม่เพื่อทดแทนรูปเก่า", type=["png", "jpg", "jpeg"])
            
            save_btn = st.form_submit_button("💾 บันทึกการแก้ไขข้อมูล")
            
            if save_btn:
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                if edit_uploaded_file is not None:
                    new_img_bytes = edit_uploaded_file.read()
                    c.execute('''
                        UPDATE cheques SET cheque_no=?, payee=?, amount=?, date=?, status=?, tax=?, image_bytes=?, note=? WHERE id=?
                    ''', (edit_c_no, edit_payee, edit_amount, edit_date.strftime('%Y-%m-%d'), edit_status, edit_tax, new_img_bytes, edit_note, item_id))
                else:
                    c.execute('''
                        UPDATE cheques SET cheque_no=?, payee=?, amount=?, date=?, status=?, tax=?, note=? WHERE id=?
                    ''', (edit_c_no, edit_payee, edit_amount, edit_date.strftime('%Y-%m-%d'), edit_status, edit_tax, edit_note, item_id))
                conn.commit()
                conn.close()
                st.success("แก้ไขข้อมูลในระบบเรียบร้อยแล้ว!")
                st.rerun()
                
        st.markdown("---")
        st.subheader("❌ ลบรายการออกจากฐานข้อมูล")
        st.error("⚠️ คำเตือน: ข้อมูลและรูปภาพหลักฐานเบิกจ่ายจะหายไปอย่างถาวรเมื่อกดยืนยันลบ")
        
        if st.button("🚨 ยืนยันลบรายการนี้ถาวร"):
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("DELETE FROM cheques WHERE id = ?", (item_id,))
            conn.commit()
            conn.close()
            st.success("ลบรายการเช็คออกจากระบบสำเร็จ!")
            st.rerun()
    else:
        st.info("ยังไม่มีข้อมูลให้จัดการ")

# --- 📥 โหมดที่ 4: ระบบนำเข้า (Import) และ ส่งออก (Export) Excel ---
elif menu == "📥 นำเข้า / 📤 ส่งออก Excel":
    st.title("📥 นำเข้า / 📤 ส่งออกไฟล์ Excel (.xlsx)")
    
    # 1. การส่งออกไฟล์ (Export)
    st.subheader("📤 ส่งออกข้อมูลจากระบบ")
    st.markdown("ดาวน์โหลดรายการเช็คทั้งหมดที่มีในฐานข้อมูลเว็บแอปออกมาเป็นไฟล์ Excel เพื่อเอาไปพิมพ์รายงานหรือเก็บสำรองไว้")
    
    conn = sqlite3.connect(DB_NAME)
    export_df = pd.read_sql_query("SELECT cheque_no, payee, amount, date, status, tax, note FROM cheques", conn)
    conn.close()
    
    if not export_df.empty:
        export_df.columns = ['เลขที่เช็ค', 'ชื่อผู้รับเงิน', 'ยอดสุทธิในเช็ค (บาท)', 'วันที่ออกเช็ค', 'สถานะ', 'ยอดภาษีที่หัก', 'หมายเหตุ']
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            export_df.to_excel(writer, index=False, sheet_name='ChequeData')
        buffer.seek(0)
        
        st.download_button(
            label="📤 ดาวน์โหลดไฟล์รายงาน Excel",
            data=buffer,
            file_name=f"รายงานเช็คและเอกสาร_{datetime.date.today().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("ไม่มีข้อมูลในระบบสำหรับการส่งออก")
        
    st.markdown("---")
    
    # 2. การนำเข้าไฟล์ (Import)
    st.subheader("📥 นำเข้าข้อมูลจำนวนมากจาก Excel")
    st.markdown("อัปโหลดไฟล์ Excel เพื่อเพิ่มรายการเช็คคราวละหลาย ๆ แถวพร้อมกันอย่างรวดเร็ว (ชื่อคอลัมน์ในไฟล์ต้องตรงกับระบบเริ่มต้น)")
    
    excel_file = st.file_uploader("เลือกอัปโหลดไฟล์ Excel (.xlsx) เพื่อนำเข้าข้อมูล", type=["xlsx"])
    if excel_file is not None:
        try:
            uploaded_df = pd.read_excel(excel_file)
            st.markdown("**🔍 ตัวอย่างแถวข้อมูลที่พบบนไฟล์:**")
            st.dataframe(uploaded_df.head(3))
            
            if st.button("🚀 เริ่มต้นนำเข้าชุดข้อมูลเข้าฐานข้อมูลบนเว็บ"):
                import_dataframe_to_db(uploaded_df)
                st.success(f"🎉 นำเข้าข้อมูลชุดใหม่รวมจำนวน {len(uploaded_df)} รายการ เรียบร้อยแล้ว! สามารถเช็คได้ที่หน้าหลักครับ")
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการโหลดไฟล์ Excel: {e}")
