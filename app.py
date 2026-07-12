import streamlit as st
import pandas as pd
import sqlite3
import datetime
import io
import json

# 1. ตั้งค่าหน้าจอธีมสว่าง Modern Pro
st.set_page_config(
    page_title="ChequeOut Modern Pro",
    page_icon="💵",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DB_NAME = "cheque_data_v3.db"

# 2. เริ่มต้นฐานข้อมูล
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

# ฟังก์ชันนำเข้าไฟล์ Excel
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

# 3. โหลด CSS ตกแต่ง
st.markdown("<style>@import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;600;700&display=swap'); html, body, [class*='css'] { font-family: 'Sarabun', sans-serif !important; } .metric-box { background: white; padding: 15px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; border-top: 4px solid #007bff; } .card-item { background: white; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 5px; }</style>", unsafe_allow_html=True)

st.title("💵 ChequeOut Modern Pro")
st.markdown("ระบบบริหารจัดการเช็คและคลังรูปภาพหลักฐานเอกสารจ่ายเงิน")

tab1, tab2, tab3 = st.tabs(["📋 รายการเช็ค & จัดการข้อมูล", "➕ เพิ่มรายการใหม่", "📥 นำเข้า / 📤 ส่งออก Excel"])

# --- 📋 TAB 1: รายการเช็ค & จัดการข้อมูล ---
with tab1:
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM cheques ORDER BY date DESC", conn)
    conn.close()

    sc1, sc2 = st.columns([2, 1])
    with sc1:
        q = st.text_input("🔍 ค้นหาด่วน", placeholder="พิมพ์ชื่อผู้รับ หรือ เลขที่เช็ค...")
    with sc2:
        st_filter = st.selectbox("สถานะ", ["ทั้งหมด", "จ่ายแล้ว", "รอดำเนินการ", "ยกเลิก", "ยังไม่จ่าย"])

    filtered_df = df.copy()
    if q:
        filtered_df = filtered_df[filtered_df['payee'].str.contains(q, na=False) | filtered_df['cheque_no'].str.contains(q, na=False)]
    if st_filter != "ทั้งหมด":
        filtered_df = filtered_df[filtered_df['status'] == st_filter]

    v1, v2, v3 = st.columns(3)
    with v1: st.markdown(f"<div class='metric-box'><div>ยอดรวมสุทธิ</div><div style='font-size:22px; font-weight:bold;'>{filtered_df['amount'].sum():,.2f} ฿</div></div>", unsafe_allow_html=True)
    with v2: st.markdown(f"<div class='metric-box'><div>ยอดภาษีรวม</div><div style='font-size:22px; font-weight:bold;'>{filtered_df['tax'].sum():,.2f} ฿</div></div>", unsafe_allow_html=True)
    with v3: st.markdown(f"<div class='metric-box'><div>รวมทั้งหมด</div><div style='font-size:22px; font-weight:bold;'>{len(filtered_df)} ฉบับ</div></div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    if not filtered_df.empty:
        for idx, row in filtered_df.iterrows():
            st_text = row['status']
            if st_text == "จ่ายแล้ว":
                bg_color, text_color = "#d1e7dd", "#0f5132"
            elif "รอ" in st_text:
                bg_color, text_color = "#fff3cd", "#664d03"
            else:
                bg_color, text_color = "#f8d7da", "#842029"

            col_main, col_action = st.columns([4, 1])
            
            with col_main:
                st.markdown(f"""
                <div class='card-item'>
                    <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;'>
                        <span style='font-size:18px; font-weight:bold;'>📄 เลขที่เช็ค: {row['cheque_no']}</span>
                        <span style='background-color:{bg_color}; color:{text_color}; padding:3px 12px; border-radius:20px; font-size:13px; font-weight:bold;'>{st_text}</span>
                    </div>
                    <div style='font-size:15px; line-height:1.6;'>
                        <b>ผู้รับเงิน:</b> {row['payee']} | <span style='color:#007bff; font-weight:bold;'>ยอดสุทธิ: {row['amount']:,.2f} บาท</span><br>
                        <b>ประเภท:</b> {row['cheque_type']} | <b>วันที่:</b> {row['date']} | <b>ภาษีหัก ณ ที่จ่าย:</b> {row['tax']:,.2f} บาท
                    </div>
                    <div style='color:#6c757d; font-size:13px; margin-top:5px; font-style:italic;'><b>หมายเหตุ:</b> {row['note'] or '-'}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # 🖼️ ระบบซ่อนรูปภาพ
                try: imgs = json.loads(row['images_json']) if row['images_json'] else []
                except: imgs = []
                
                if imgs:
                    with st.expander("📂 คลิกเพื่อเปิดดูรูปภาพหลักฐาน"):
                        img_cols = st.columns(4)
                        for i, img_hex in enumerate(imgs):
                            with img_cols[i % 4]:
                                st.image(io.BytesIO(bytes.fromhex(img_hex)), use_container_width=True, caption=f"รูปที่ {i+1}")
                else:
                    st.caption("ℹ️ ไม่มีรูปภาพหลักฐาน")

            with col_action:
                st.markdown("<div style='text-align:right;'>", unsafe_allow_html=True)
                btn_edit = st.checkbox("✏️ แก้ไข", key=f"ed_chk_{row['id']}")
                btn_delete = st.button("❌ ลบ", key=f"del_btn_{row['id']}", use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
                if btn_delete:
                    conn = sqlite3.connect(DB_NAME)
                    conn.cursor().execute("DELETE FROM cheques WHERE id=?", (row['id'],))
                    conn.commit()
                    conn.close()
                    st.rerun()

            # ฟอร์มแก้ไข (แทนที่รายการเดิมและเคลียร์รูปภาพได้เด็ดขาด)
            if btn_edit:
                with st.form(f"form_edit_{row['id']}"):
                    st.markdown("##### ⚙️ แก้ไขข้อมูลรายการ")
                    el1, el2 = st.columns(2)
                    with el1:
                        e_no = st.text_input("เลขที่เช็ค", value=row['cheque_no'])
                        e_pay = st.text_input("ชื่อผู้รับเงิน", value=row['payee'])
                        e_type = st.selectbox("ประเภทเช็ค", ["เช็ครายได้", "เช็คเงินอุดหนุน", "อื่น ๆ"], index=["เช็ครายได้", "เช็คเงินอุดหนุน", "อื่น ๆ"].index(row['cheque_type']) if row['cheque_type'] in ["เช็ครายได้", "เช็คเงินอุดหนุน", "อื่น ๆ"] else 0)
                    with el2:
                        e_amt = st.number_input("ยอดเงิน (บาท)", value=float(row['amount']))
                        e_tax = st.number_input("ภาษี (บาท)", value=float(row['tax'] or 0.0))
                        try: current_d = datetime.datetime.strptime(row['date'], '%Y-%m-%d').date()
                        except: current_d = datetime.date.today()
                        e_date = st.date_input("วันที่", current_d)
                        e_stat = st.selectbox("สถานะ", ["จ่ายแล้ว", "รอดำเนินการ", "ยังไม่จ่าย", "ยกเลิก"], index=["จ่ายแล้ว", "รอดำเนินการ", "ยังไม่จ่าย", "ยกเลิก"].index(row['status']) if row['status'] in ["จ่ายแล้ว", "รอดำเนินการ", "ยังไม่จ่าย", "ยกเลิก"] else 0)
                    
                    e_note = st.text_area("หมายเหตุ", value=row['note'])
                    
                    st.markdown("---")
                    e_del_imgs = st.checkbox("🗑️ ลบรูปภาพหลักฐานทั้งหมดของรายการนี้ทิ้ง", key=f"del_img_chk_{row['id']}")
                    e_files = st.file_uploader("📸 อัปโหลดรูปภาพใหม่เข้าไปแทนที่", accept_multiple_files=True, key=f"file_ed_{row['id']}")
                    
                    if st.form_submit_button("💾 บันทึกการแก้ไข"):
                        conn = sqlite3.connect(DB_NAME)
                        cursor = conn.cursor()
                        
                        if e_files:
                            new_imgs = json.dumps([f.read().hex() for f in e_files])
                            cursor.execute("UPDATE cheques SET cheque_no=?, payee=?, amount=?, date=?, status=?, tax=?, cheque_type=?, note=?, images_json=? WHERE id=?", 
                                         (e_no, e_pay, e_amt, e_date.strftime('%Y-%m-%d'), e_stat, e_tax, e_type, e_note, new_imgs, row['id']))
                        elif e_del_imgs:
                            cursor.execute("UPDATE cheques SET cheque_no=?, payee=?, amount=?, date=?, status=?, tax=?, cheque_type=?, note=?, images_json=? WHERE id=?", 
                                         (e_no, e_pay, e_amt, e_date.strftime('%Y-%m-%d'), e_stat, e_tax, e_type, e_note, "[]", row['id']))
                        else:
                            cursor.execute("UPDATE cheques SET cheque_no=?, payee=?, amount=?, date=?, status=?, tax=?, cheque_type=?, note=? WHERE id=?", 
                                         (e_no, e_pay, e_amt, e_date.strftime('%Y-%m-%d'), e_stat, e_tax, e_type, e_note, row['id']))
                        
                        conn.commit()
                        conn.close()
                        st.success("แก้ไขข้อมูลสำเร็จ!")
                        st.rerun()
            st.markdown("---")
    else:
        st.info("ไม่มีรายการบันทึก")

# --- ➕ TAB 2: เพิ่มรายการใหม่ ---
with tab2:
    st.subheader("📝 กรอกรายละเอียดเช็คใบใหม่")
    with st.form("add_new_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            in_no = st.text_input("เลขที่เช็ค")
            in_pay = st.text_input("ชื่อผู้รับเงิน")
            in_type = st.selectbox("ประเภทเช็ค", ["เช็ครายได้", "เช็คเงินอุดหนุน", "อื่น ๆ"])
        with c2:
            in_amt = st.number_input("ยอดเงินสุทธิ (บาท)", min_value=0.0)
            in_tax = st.number_input("ภาษีหัก ณ ที่จ่าย (บาท)", min_value=0.0)
            in_date = st.date_input("วันที่", datetime.date.today())
        in_stat = st.selectbox("สถานะเช็ค", ["จ่ายแล้ว", "รอดำเนินการ", "ยังไม่จ่าย", "ยกเลิก"])
        in_note = st.text_area("หมายเหตุ")
        in_files = st.file_uploader("📸 แนบรูปหลักฐาน (ได้หลายรูปพร้อมกัน)", accept_multiple_files=True)
        
        if st.form_submit_button("✅ บันทึกข้อมูล"):
            if in_no and in_pay:
                img_list = json.dumps([f.read().hex() for f in in_files]) if in_files else "[]"
                conn = sqlite3.connect(DB_NAME)
                conn.cursor().execute('''
                    INSERT INTO cheques (cheque_no, payee, amount, date, status, tax, cheque_type, images_json, note)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (in_no, in_pay, in_amt, in_date.strftime('%Y-%m-%d'), in_stat, in_tax, in_type, img_list, in_note))
                conn.commit()
                conn.close()
                st.success("บันทึกสำเร็จ!")
                st.rerun()

# --- 📥 TAB 3: นำเข้า / ส่งออก Excel & ล้างระบบ ---
with tab3:
    st.subheader("📥 อัปโหลดนำเข้าไฟล์ Excel")
    up_file = st.file_uploader("เลือกไฟล์ Excel (.xlsx)", type=["xlsx"])
    if up_file is not None:
        try:
            df_up = pd.read_excel(up_file)
            st.dataframe(df_up.head(2))
            if st.button("🚀 ยืนยันการนำเข้าข้อมูล"):
                import_dataframe_to_db(df_up)
                st.success("นำเข้าข้อมูลเสร็จสมบูรณ์เรียบร้อย!")
                st.rerun()
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")
            
    st.markdown("---")
    st.subheader("📤 ส่งออกรายงาน Excel")
    conn = sqlite3.connect(DB_NAME)
    ex_df = pd.read_sql_query("SELECT cheque_no, payee, amount, date, status, tax, cheque_type, note FROM cheques", conn)
    conn.close()
    if not ex_df.empty:
        ex_df.columns = ['เลขที่เช็ค', 'ชื่อผู้รับเงิน', 'ยอดสุทธิในเช็ค (บาท)', 'วันที่ออกเช็ค', 'สถานะ', 'ยอดภาษีที่หัก', 'ประเภทเช็ค', 'หมายเหตุ']
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as w:
            ex_df.to_excel(w, index=False)
        st.download_button("📥 ดาวน์โหลด Excel", data=buf.getvalue(), file_name="รายงานเช็ค.xlsx")
        
    st.markdown("---")
    # 🚨 โซนอันตรายเพิ่มปุ่มล้างระบบข้อมูลซ้ำ
    st.subheader("🚨 การจัดการระบบข้อมูลหลังบ้าน")
    st.error("คำเตือน: ปุ่มด้านล่างนี้จะทำการลบข้อมูลเช็คและรูปภาพหลักฐานทั้งหมดออกจากฐานข้อมูลเว็บอย่างถาวร ไม่สามารถกู้คืนได้")
    
    confirm_clear = st.checkbox("ฉันยืนยันว่าต้องการลบข้อมูลทั้งหมดในระบบออกให้หมดเพื่อเริ่มนำเข้าใหม่")
    if st.button("🗑️ ล้างฐานข้อมูลทั้งหมดให้เป็นศูนย์", disabled=not confirm_clear):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cheques")
        conn.commit()
        conn.close()
        st.success("💥 ล้างฐานข้อมูลสำเร็จ! ตอนนี้ระบบว่างเปล่าพร้อมสำหรับการนำข้อมูลเข้าใหม่แล้วครับ")
        st.rerun()
