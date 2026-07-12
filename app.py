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

# ฟังก์ชันบันทึกกลุ่มข้อมูลจาก Excel เข้า Database ขาเข้า (Import)
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
        note_val = str(row.get('หมายเหตุ', '')).strip() if pd.notna(row.get('หมายเหตุ')) else 'นำเข้าผ่าน Excel'
        
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

# 3. ตกแต่งหน้าตาแอปด้วย CSS ให้ดูสว่าง ทันสมัย ตัวหนังสือใหญ่ชัดเจน
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
        margin-bottom: 20px;
    }
    .label-blue { color: #007bff; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("💵 ChequeOut Modern Pro")
st.markdown("ระบบจัดการเช็คและหลักฐานเอกสารเบิกจ่าย รูปแบบ All-in-One ครบครันในหน้าเดียว")

tab1, tab2, tab3 = st.tabs(["📋 รายการเช็ค & จัดการข้อมูล", "➕ เพิ่มรายการใหม่", "📥 นำเข้า / 📤 ส่งออก Excel"])

# --- 📋 TAB 1: รายการเช็ค ค้นหา แก้ไข และลบในที่เดียว ---
with tab1:
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM cheques ORDER BY date DESC", conn)
    conn.close()

    # ระบบค้นหาข้อมูลด่วน
    search_col1, search_col2 = st.columns([2, 1])
    with search_col1:
        q = st.text_input("🔍 ค้นหาแบบรวดเร็ว (ชื่อผู้รับ / เลขที่เช็ค)", placeholder="พิมพ์สิ่งที่ต้องการค้นหา...")
    with search_col2:
        st_filter = st.selectbox("กรองตามสถานะเช็ค", ["ทั้งหมด", "จ่ายแล้ว", "รอดำเนินการ", "ยกเลิก"])

    filtered_df = df.copy()
    if q:
        filtered_df = filtered_df[filtered_df['payee'].str.contains(q, na=False) | filtered_df['cheque_no'].str.contains(q, na=False)]
    if st_filter != "ทั้งหมด":
        filtered_df = filtered_df[filtered_df['status'] == st_filter]

    # การ์ดสรุปยอดเงินภาพรวม
    m1, m2, m3 = st.columns(3)
    with m1: st.markdown(f'<div class="metric-card"><div>ยอดจ่ายสุทธิรวม</div><div style="font-size:24px; font-weight:bold;">{filtered_df["amount"].sum():,.2f} ฿</div></div>', unsafe_allow_html=True)
    with m2: st.markdown(f'<div class="metric-card"><div>ภาษีหัก ณ ที่จ่ายรวม</div><div style="font-size:24px; font-weight:bold;">{filtered_df["tax"].sum():,.2f} ฿</div></div>', unsafe_allow_html=True)
    with m3: st.markdown(f'<div class="metric-card"><div>จำนวนเช็คทั้งหมด</div><div style="font-size:24px; font-weight:bold;">{len(filtered_df)} ฉบับ</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if not filtered_df.empty:
        for _, row in filtered_df.iterrows():
            with st.container():
                st.markdown(f"""
                <div class="cheque-box">
                    <div style="display:flex; justify-content:space-between;">
                        <span style="font-size:20px; font-weight:bold;">📄 เลขที่: {row['cheque_no']}</span>
                        <span style="background:#e7f3ff; color:#007bff; padding:2px 10px; border-radius:10px; font-size:14px; font-weight:bold;">{row['status']}</span>
                    </div>
                    <p style="margin:10px 0; font-size:16px;">
                        <b>ผู้รับเงิน:</b> {row['payee']} | <span class="label-blue">ยอดสุทธิ: {row['amount']:,.2f} บาท</span><br>
                        <b>ประเภทเช็ค:</b> {row['cheque_type']} | <b>วันที่ออกเช็ค:</b> {row['date']} | <b>ภาษี:</b> {row['tax']:,.2f} บ.
                    </p>
                    <p style="color:#6c757d; font-style:italic;"><b>หมายเหตุ:</b> {row['note'] or '-'}</p>
                </div>
                """, unsafe_allow_html=True)

                # ดึงรูปภาพหลายรูปมาแสดงผลเรียงกัน
                try: imgs = json.loads(row['images_json']) if row['images_json'] else []
                except: imgs = []
                
                if imgs:
                    st.write("🖼️ **หลักฐานรูปภาพที่แนบไว้:**")
                    cols = st.columns(4)
                    for i, img_hex in enumerate(imgs):
                        with cols[i % 4]:
                            try: st.image(io.BytesIO(bytes.fromhex(img_hex)), use_container_width=True, caption=f"รูปที่ {i+1}")
                            except: st.caption("⚠️ โหลดภาพล้มเหลว")
                else:
                    st.caption("❌ รายการนี้ยังไม่มีการแนบภาพหลักฐาน")

                # แถวปุ่มแก้ไข และปุ่มลบ (Inline ในหน้าแรก)
                c_edit, c_del, _ = st.columns([1, 1, 4])
                with c_edit:
                    show_form = st.checkbox("✏️ แก้ไขข้อมูล", key=f"form_key_{row['id']}")
                with c_del:
                    if st.button("❌ ลบรายการ", key=f"del_{row['id']}"):
                        conn = sqlite3.connect(DB_NAME)
                        conn.cursor().execute("DELETE FROM cheques WHERE id=?", (row['id'],))
                        conn.commit()
                        conn.close()
                        st.success("ลบรายการเรียบร้อย!")
                        st.rerun()

                # ฟอร์มแก้ไขขยายตัวออกมาใต้การ์ดเมื่อกดติ๊กถูก
                if show_form:
                    with st.form(f"edit_f_{row['id']}"):
                        st.markdown("##### ✏️ แก้ไขข้อมูลรายละเอียดรายการ")
                        col_e1, col_e2 = st.columns(2)
                        with col_e1:
                            e_no = st.text_input("เลขที่เช็ค", value=row['cheque_no'])
                            e_pay = st.text_input("ชื่อผู้รับเงิน", value=row['payee'])
                            e_type = st.selectbox("ประเภทเช็ค", ["เช็ครายได้", "เช็คเงินอุดหนุน", "อื่น ๆ"], index=["เช็ครายได้", "เช็คเงินอุดหนุน", "อื่น ๆ"].index(row['cheque_type']) if row['cheque_type'] in ["เช็ครายได้", "เช็คเงินอุดหนุน", "อื่น ๆ"] else 0)
                        with col_e2:
                            e_amt = st.number_input("ยอดเงินสุทธิ (บาท)", value=float(row['amount']))
                            e_tax = st.number_input("ภาษีหัก ณ ที่จ่าย (บาท)", value=float(row['tax']) if row['tax'] else 0.0)
                            try: current_d = datetime.datetime.strptime(row['date'], '%Y-%m-%d').date()
                            except: current_d = datetime.date.today()
                            e_date = st.date_input("วันที่", current_d)
                            
                        e_stat = st.selectbox("สถานะ", ["จ่ายแล้ว", "รอดำเนินการ", "ยกเลิก"], index=["จ่ายแล้ว", "รอดำเนินการ", "ยกเลิก"].index(row['status']) if row['status'] in ["จ่ายแล้ว", "รอดำเนินการ", "ยกเลิก"] else 0)
                        e_note = st.text_area("หมายเหตุ", value=row['note'])
                        e_files = st.file_uploader("แนบกลุ่มรูปภาพใหม่ (จะทับรูปชุดเดิมทั้งหมด)", accept_multiple_files=True, key=f"files_{row['id']}")
                        
                        if st.form_submit_button("💾 บันทึกการเปลี่ยนแปลง"):
                            conn = sqlite3.connect(DB_NAME)
                            cursor = conn.cursor()
                            if e_files:
                                new_imgs = json.dumps([f.read().hex() for f in e_files])
                                cursor.execute("UPDATE cheques SET cheque_no=?, payee=?, amount=?, date=?, status=?, tax=?, cheque_type=?, note=?, images_json=? WHERE id=?", 
                                             (e_no, e_pay, e_amt, e_date.strftime('%Y-%m-%d'), e_stat, e_tax, e_type, e_note, new_imgs, row['id']))
                            else:
                                cursor.execute("UPDATE cheques SET cheque_no=?, payee=?, amount=?, date=?, status=?, tax=?, cheque_type=?, note=? WHERE id=?", 
                                             (e_no, e_pay, e_amt, e_date.strftime('%Y-%m-%d'), e_stat, e_tax, e_type, e_note, row['id']))
                            conn.commit()
                            conn.close()
                            st.success("บันทึกข้อมูลเรียบร้อยแล้ว!")
                            st.rerun()
                st.markdown("<hr style='border-top:1px dashed #ccc;'>", unsafe_allow_html=True)
    else:
        st.info("ไม่มีข้อมูลในระบบ หรือไม่มีรายการตามที่ระบุ")

# --- ➕ TAB 2: ฟอร์มเพิ่มเช็คใบใหม่ (รองรับหลายรูปภาพ) ---
with tab2:
    st.subheader("📝 บันทึกข้อมูลเช็คใบใหม่เข้าสู่ระบบ")
    with st.form("add_form_new", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            in_no = st.text_input("เลขที่เช็ค")
            in_pay = st.text_input("ชื่อผู้รับเงิน / บริษัท")
            in_type = st.selectbox("ประเภทเช็ค", ["เช็ครายได้", "เช็คเงินอุดหนุน", "อื่น ๆ"])
        with col2:
            in_amt = st.number_input("ยอดเงินสุทธิในเช็ค (บาท)", min_value=0.0)
            in_tax = st.number_input("ภาษีหัก ณ ที่จ่าย (บาท)", min_value=0.0)
            in_date = st.date_input("วันที่ออกเช็ค", datetime.date.today())
        
        in_stat = st.selectbox("สถานะเช็ค", ["จ่ายแล้ว", "รอดำเนินการ", "ยกเลิก"])
        in_note = st.text_area("หมายเหตุเพิ่มเติม")
        in_files = st.file_uploader("📸 เลือกรูปถ่ายเช็ค / ใบเสร็จ / สลิป (เลือกได้หลายรูปพร้อมกัน)", accept_multiple_files=True)
        
        if st.form_submit_button("✅ บันทึกข้อมูลลงฐานข้อมูล"):
            if in_no and in_pay:
                img_hex_list = json.dumps([f.read().hex() for f in in_files]) if in_files else "[]"
                conn = sqlite3.connect(DB_NAME)
                conn.cursor().execute('''
                    INSERT INTO cheques (cheque_no, payee, amount, date, status, tax, cheque_type, images_json, note)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (in_no, in_pay, in_amt, in_date.strftime('%Y-%m-%d'), in_stat, in_tax, in_type, img_hex_list, in_note))
                conn.commit()
                conn.close()
                st.success("🎉 บันทึกข้อมูลและบันทึกรูปภาพเรียบร้อย!")
                st.rerun()
            else:
                st.error("❌ ข้อผิดพลาด: กรุณากรอกข้อมูลเลขที่เช็คและชื่อผู้รับเงินก่อนกดบันทึก")

# --- 📥 TAB 3: ระบบนำเข้า (Import) และส่งออก (Export) Excel ---
with tab3:
    st.subheader("📥 นำเข้าข้อมูลจำนวนมากจากไฟล์ Excel")
    st.markdown("คุณสามารถอัปโหลดไฟล์ Excel (`.xlsx`) เพื่อเพิ่มรายการข้อมูลเช็คหลายรายการเข้าระบบพร้อมกันได้อย่างรวดเร็ว")
    
    upload_excel = st.file_uploader("เลือกไฟล์ Excel ที่ต้องการอัปโหลดเข้าระบบ", type=["xlsx"])
    if upload_excel is not None:
        try:
            df_uploaded = pd.read_excel(upload_excel)
            st.markdown("**🔍 ตรวจพบตัวอย่างแถวข้อมูลบนไฟล์:**")
            st.dataframe(df_uploaded.head(3))
            
            if st.button("🚀 ยืนยันคำสั่งนำเข้าข้อมูลทั้งหมดเข้าสู่เว็บ"):
                import_dataframe_to_db(df_uploaded)
                st.success(f"🎉 นำเข้าชุดข้อมูลชุดใหม่รวม {len(df_uploaded)} รายการสำเร็จ! ตรวจสอบได้ที่หน้าแรก")
                st.rerun()
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการอ่านโครงสร้างไฟล์ Excel: {e}")
            
    st.markdown("---")
    
    st.subheader("📤 ส่งออกข้อมูลเป็นรายงาน Excel")
    st.markdown("ดาวน์โหลดข้อมูลเช็คทั้งหมดที่บันทึกอยู่ในฐานข้อมูลเว็บไซต์ออกมาในรูปแบบไฟล์ Excel ไปใช้งานต่อ")
    
    conn = sqlite3.connect(DB_NAME)
    ex_df = pd.read_sql_query("SELECT cheque_no, payee, amount, date, status, tax, cheque_type, note FROM cheques", conn)
    conn.close()
    
    if not ex_df.empty:
        ex_df.columns = ['เลขที่เช็ค', 'ชื่อผู้รับเงิน', 'ยอดสุทธิในเช็ค (บาท)', 'วันที่ออกเช็ค', 'สถานะ', 'ยอดภาษีที่หัก', 'ประเภทเช็ค', 'หมายเหตุ']
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            ex_df.to_excel(writer, index=False, sheet_name='ChequeReport')
        st.download_button("📥 ดาวน์โหลดไฟล์รายงาน Excel (.xlsx)", data=buffer.getvalue(), file_name=f"รายงานเช็คทั้งหมด_{datetime.date.today().strftime('%Y%m%d')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("ไม่มีข้อมูลในระบบสำหรับการส่งออก")
