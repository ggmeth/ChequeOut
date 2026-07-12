import streamlit as st
import pandas as pd
import sqlite3
import datetime
from PIL import Image
import io
import json

# 1. ตั้งค่าหน้าจอธีมสว่าง คลีน และรองรับมือถือ
st.set_page_config(
    page_title="ChequeOut Modern Pro",
    page_icon="💵",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DB_NAME = "cheque_modern.db"

# 2. ฟังก์ชันจัดการฐานข้อมูลแบบรองรับหลายรูป (เก็บเป็น JSON String ของ list รูปภาพ)
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
    
    # นำเข้าข้อมูลเริ่มต้นจาก Excel (ถ้าฐานข้อมูลยังว่างเปล่า)
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
                if isinstance(dt, pd.Timestamp) or isinstance(dt, datetime.date):
                    date_str = dt.strftime('%Y-%m-%d')
                else:
                    date_str = str(dt)
                    
                status = str(row.get('สถานะ', 'จ่ายแล้ว')).strip()
                c_type = str(row.get('ประเภทเช็ค', 'เช็ครายได้')).strip()
                
                tax = 0
                for col in df.columns:
                    if 'ภาษี' in str(col):
                        tax = pd.to_numeric(row.get(col, 0), errors='coerce')
                        break
                
                c.execute('''
                    INSERT INTO cheques (cheque_no, payee, amount, date, status, tax, cheque_type, images_json, note)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (cheque_no, payee, float(amount) if not pd.isna(amount) else 0.0, date_str, status, float(tax) if not pd.isna(tax) else 0.0, c_type, "[]", 'นำเข้าเริ่มต้น'))
            conn.commit()
        except Exception:
            pass
    conn.close()

init_db()

# 3. ปรับแต่งหน้าตาแอปด้วย CSS ให้ดูหรูหรา สว่าง ทันสมัย และตัวหนังสือใหญ่温馨
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&display=swap');
    
    * { font-family: 'Sarabun', sans-serif !important; }
    .main { background-color: #f6f8fa; }
    
    /* สไตล์การ์ดสรุปยอดเงิน */
    .metric-card {
        background-color: #ffffff;
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        border: 1px solid #eef2f6;
        text-align: center;
    }
    .metric-title { color: #6c757d; font-size: 14px; font-weight: 600; margin-bottom: 8px; }
    .metric-value { color: #1f2937; font-size: 24px; font-weight: 700; }
    
    /* สไตล์การ์ดรายการเช็ค */
    .cheque-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 14px;
        border: 1px solid #eef2f6;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
        margin-bottom: 16px;
    }
    .status-badge {
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        display: inline-block;
    }
    .type-badge {
        background-color: #e8f4fd;
        color: #0d6efd;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        display: inline-block;
        margin-right: 5px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("💵 ChequeOut Modern Pro")
st.markdown("ระบบบริหารจัดการข้อมูลเช็คและหลักฐานเอกสารเบิกจ่ายความปลอดภัยสูง")

# เปลี่ยนมาใช้ระบบ Tab ด้านบนแทนเมนูด้านข้าง เพื่อลดความกระจัดกระจายบนมือถือ
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 รายการเช็คทั้งหมด", 
    "➕ เพิ่มรายการใหม่", 
    "⚙️ แก้ไข/ลบรายการ", 
    "📥 นำเข้า/ส่งออก Excel"
])

# --- 📊 TAB 1: หน้าหลัก & ค้นหาเช็ค ---
with tab1:
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM cheques ORDER BY date DESC", conn)
    conn.close()
    
    # ส่วนตัวค้นหาและการ์ดสรุปยอด
    search_q = st.text_input("🔍 ค้นหาด่วน...", placeholder="พิมพ์เลขที่เช็ค หรือชื่อผู้รับเงินเพื่อค้นหาทันที...")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        f_type = st.selectbox("กรองตามประเภทเช็ค", ["ทั้งหมด", "เช็ครายได้", "เช็คเงินอุดหนุน"])
    with col_f2:
        f_status = st.selectbox("กรองตามสถานะ", ["ทั้งหมด", "จ่ายแล้ว", "รอดำเนินการ", "ยกเลิก"])
        
    filtered_df = df.copy()
    if f_type != "ทั้งหมด":
        filtered_df = filtered_df[filtered_df['cheque_type'] == f_type]
    if f_status != "ทั้งหมด":
        filtered_df = filtered_df[filtered_df['status'] == f_status]
    if search_q:
        filtered_df = filtered_df[
            filtered_df['payee'].str.contains(search_q, case=False, na=False) |
            filtered_df['cheque_no'].str.contains(search_q, case=False, na=False)
        ]
        
    # แสดงการ์ดสรุปผล
    st.markdown("<br>", unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f'<div class="metric-card"><div class="metric-title">ยอดจ่ายสุทธิรวม</div><div class="metric-value">{filtered_df["amount"].sum():,.2f} ฿</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-card"><div class="metric-title">ภาษีหัก ณ ที่จ่ายรวม</div><div class="metric-value">{filtered_df["tax"].sum():,.2f} ฿</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="metric-card"><div class="metric-title">จำนวนรายการเช็ค</div><div class="metric-value">{filtered_df.shape[0]} ฉบับ</div></div>', unsafe_allow_html=True)
        
    st.markdown("---")
    
    if not filtered_df.empty:
        for idx, row in filtered_df.iterrows():
            # กำหนดสีของ Status Badge
            st_color = "#d1e7dd" if row['status'] == "จ่ายแล้ว" else "#fff3cd" if row['status'] == "รอดำเนินการ" else "#f8d7da"
            st_tx_color = "#0f5132" if row['status'] == "จ่ายแล้ว" else "#664d03" if row['status'] == "รอดำเนินการ" else "#842029"
            
            st.markdown(f"""
            <div class="cheque-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <span style="font-size: 18px; font-weight: bold; color:#1e2937;">📄 เลขที่เช็ค: {row['cheque_no']}</span>
                    <span class="status-badge" style="background-color: {st_color}; color: {st_tx_color};">{row['status']}</span>
                </div>
                <div style="font-size: 15px; color: #4b5563; margin-bottom: 8px;">
                    👤 <b>ผู้รับเงิน:</b> {row['payee']} &nbsp;|&nbsp; 💰 <b>ยอดเงินสุทธิ:</b> <span style="color:#0d6efd; font-weight:bold;">{row['amount']:,.2f} บาท</span>
                </div>
                <div style="font-size: 14px; color: #6b7280; margin-bottom: 12px;">
                    <span class="type-badge">📌 {row['cheque_type']}</span>
                    📅 <b>วันที่ออกเช็ค:</b> {row['date']} &nbsp;|&nbsp; 💡 <b>ภาษีหัก ณ ที่จ่าย:</b> {row['tax']:,.2f} บาท
                </div>
                <div style="font-size: 14px; color: #6b7280; font-style: italic; margin-bottom: 15px;">
                    📝 <b>หมายเหตุ:</b> {row['note'] if row['note'] else '-'}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # แสดงรูปภาพหลักฐานเบิกจ่าย (รองรับหลายรูป)
            try:
                img_list = json.loads(row['images_json']) if row['images_json'] else []
            except:
                img_list = []
                
            if img_list:
                st.markdown("🖼️ **หลักฐานเอกสารเบิกจ่ายที่แนบไว้:**")
                img_cols = st.columns(min(len(img_list), 4))
                for i, img_hex in enumerate(img_list):
                    with img_cols[i % 4]:
                        try:
                            img_data = bytes.fromhex(img_hex)
                            image = Image.open(io.BytesIO(img_data))
                            st.image(image, use_container_width=True, caption=f"รูปภาพที่ {i+1}")
                        except:
                            st.caption("⚠️ รูปภาพไม่สมบูรณ์")
            else:
                st.caption("❌ ยังไม่มีการแนบรูปภาพหลักฐานเบิกจ่ายในรายการนี้")
            st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
    else:
        st.info("ไม่พบข้อมูลรายการเช็คตามเงื่อนไขที่ค้นหา")

# --- ➕ TAB 2: เพิ่มรายการเช็คใหม่ ---
with tab2:
    st.subheader("📝 ฟอร์มบันทึกรายการเช็คและหลักฐาน")
    with st.form("modern_add_form", clear_on_submit=True):
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            c_no = st.text_input("เลขที่เช็ค")
            payee = st.text_input("ชื่อผู้รับเงิน / บริษัท")
            c_type = st.selectbox("ประเภทเช็ค", ["เช็ครายได้", "เช็คเงินอุดหนุน", "อื่น ๆ"])
        with col_a2:
            amount = st.number_input("ยอดเงินสุทธิในเช็ค (บาท)", min_value=0.0, step=100.0)
            tax = st.number_input("ภาษีที่หัก ณ ที่จ่าย (บาท)", min_value=0.0, step=10.0)
            date = st.date_input("วันที่ออกเช็ค", datetime.date.today())
            
        status = st.selectbox("สถานะเช็ค", ["จ่ายแล้ว", "รอดำเนินการ", "ยกเลิก"])
        note = st.text_area("หมายเหตุเพิ่มเติม")
        
        st.markdown("### 🖼️ อัปเดตแนบภาพหลักฐานเอกสารเบิกจ่าย (เลือกได้หลายรูปพร้อมกัน)")
        uploaded_files = st.file_uploader("ถ่ายรูปภาพเช็ค / ใบเสร็จ / รูปสลิปโอนเงิน", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
        
        submit_btn = st.form_submit_button("💾 บันทึกข้อมูลเข้าสู่ระบบ")
        
        if submit_btn:
            if not c_no or not payee:
                st.error("❌ กรุณากรอกเลขที่เช็คและชื่อผู้รับเงินให้เรียบร้อยก่อนบันทึก")
            else:
                hex_images = []
                if uploaded_files:
                    for f in uploaded_files:
                        hex_images.append(f.read().hex())
                        
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute('''
                    INSERT INTO cheques (cheque_no, payee, amount, date, status, tax, cheque_type, images_json, note)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (c_no, payee, amount, date.strftime('%Y-%m-%d'), status, tax, c_type, json.dumps(hex_images), note))
                conn.commit()
                conn.close()
                st.success("🎉 บันทึกข้อมูลและจัดเก็บรูปภาพหลักฐานเรียบร้อยแล้ว!")
                st.rerun()

# --- ⚙️ TAB 3: แก้ไขและลบรายการ ---
with tab3:
    st.subheader("⚙️ แก้ไขข้อมูลและหลักฐานเอกสารเบิกจ่าย")
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM cheques ORDER BY date DESC", conn)
    conn.close()
    
    if not df.empty:
        list_options = {f"เลขที่: {row['cheque_no']} | {row['payee']} ({row['amount']:,.2f} บ.)": row['id'] for _, row in df.iterrows()}
        selected_item = st.selectbox("🔍 เลือกรายการที่ต้องการปรับปรุงข้อมูล", list(list_options.keys()))
        item_id = list_options[selected_item]
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT * FROM cheques WHERE id = ?", (item_id,))
        item_data = c.fetchone()
        conn.close()
        
        with st.form("modern_edit_form"):
            col_e1, col_e2 = st.columns(2)
            with col_e1:
                edit_c_no = st.text_input("เลขที่เช็ค", value=item_data[1])
                edit_payee = st.text_input("ชื่อผู้รับเงิน / บริษัท", value=item_data[2])
                edit_type = st.selectbox("ประเภทเช็ค", ["เช็ครายได้", "เช็คเงินอุดหนุน", "อื่น ๆ"], index=["เช็ครายได้", "เช็คเงินอุดหนุน", "อื่น ๆ"].index(item_data[7]) if item_data[7] in ["เช็ครายได้", "เช็คเงินอุดหนุน", "อื่น ๆ"] else 0)
            with col_e2:
                edit_amount = st.number_input("ยอดเงินสุทธิในเช็ค (บาท)", value=float(item_data[3]))
                edit_tax = st.number_input("ภาษีที่หัก ณ ที่จ่าย (บาท)", value=float(item_data[6]) if item_data[6] else 0.0)
                try: edit_date = datetime.datetime.strptime(item_data[4], '%Y-%m-%d').date()
                except: edit_date = datetime.date.today()
                edit_date = st.date_input("วันที่ออกเช็ค", edit_date)
                
            edit_status = st.selectbox("สถานะเช็ค", ["จ่ายแล้ว", "รอดำเนินการ", "ยกเลิก"], index=["จ่ายแล้ว", "รอดำเนินการ", "ยกเลิก"].index(item_data[5]) if item_data[5] in ["จ่ายแล้ว", "รอดำเนินการ", "ยกเลิก"] else 0)
            edit_note = st.text_area("หมายเหตุเพิ่มเติม", value=item_data[9] if item_data[9] else "")
            
            st.markdown("🖼️ **อัปเดตชุดรูปภาพหลักฐานใหม่** (หากอัปโหลดใหม่จะแทนที่รูปภาพชุดเดิมทั้งหมด)")
            edit_uploaded_files = st.file_uploader("อัปโหลดกลุ่มรูปภาพใหม่", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
            
            save_btn = st.form_submit_button("💾 บันทึกการเปลี่ยนแปลงข้อมูล")
            
            if save_btn:
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                if edit_uploaded_files:
                    new_hex_images = [f.read().hex() for f in edit_uploaded_files]
                    c.execute('''
                        UPDATE cheques SET cheque_no=?, payee=?, amount=?, date=?, status=?, tax=?, cheque_type=?, images_json=?, note=? WHERE id=?
                    ''', (edit_c_no, edit_payee, edit_amount, edit_date.strftime('%Y-%m-%d'), edit_status, edit_tax, edit_type, json.dumps(new_hex_images), edit_note, item_id))
                else:
                    c.execute('''
                        UPDATE cheques SET cheque_no=?, payee=?, amount=?, date=?, status=?, tax=?, cheque_type=?, note=? WHERE id=?
                    ''', (edit_c_no, edit_payee, edit_amount, edit_date.strftime('%Y-%m-%d'), edit_status, edit_tax, edit_type, edit_note, item_id))
                conn.commit()
                conn.close()
                st.success("แก้ไขข้อมูลในระบบเรียบร้อยแล้ว!")
                st.rerun()
                
        st.markdown("---")
        if st.button("🚨 ยืนยันลบรายการนี้ถาวร"):
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("DELETE FROM cheques WHERE id = ?", (item_id,))
            conn.commit()
            conn.close()
            st.success("ลบข้อมูลออกจากระบบสำเร็จ!")
            st.rerun()
    else:
        st.info("ยังไม่มีข้อมูลในระบบ")

# --- 📥 TAB 4: นำเข้าและส่งออก Excel ---
with tab4:
    st.subheader("📤 ส่งออกข้อมูลเป็นไฟล์ Excel")
    conn = sqlite3.connect(DB_NAME)
    export_df = pd.read_sql_query("SELECT cheque_no, payee, amount, date, status, tax, cheque_type, note FROM cheques", conn)
    conn.close()
    
    if not export_df.empty:
        export_df.columns = ['เลขที่เช็ค', 'ชื่อผู้รับเงิน', 'ยอดสุทธิในเช็ค (บาท)', 'วันที่ออกเช็ค', 'สถานะ', 'ยอดภาษีที่หัก', 'ประเภทเช็ค', 'หมายเหตุ']
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            export_df.to_excel(writer, index=False, sheet_name='ChequeReport')
        buffer.seek(0)
        st.download_button(
            label="📤 ดาวน์โหลดไฟล์ Excel (.xlsx)",
            data=buffer,
            file_name=f"รายงานเช็คระบบใหม่_{datetime.date.today().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("ระบบยังไม่มีข้อมูลให้ส่งออก")
