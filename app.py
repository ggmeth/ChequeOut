import streamlit as st
import pandas as pd
import sqlite3
import datetime
from PIL import Image
import io
import json

# 1. ตั้งค่าหน้าจอธีมสว่าง Modern & Clean
st.set_page_config(
    page_title="ChequeOut Modern Pro",
    page_icon="💵",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DB_NAME = "cheque_data_v3.db"

# 2. ฟังก์ชันจัดการฐานข้อมูล (รองรับการเก็บรูปหลายรูปในรูปแบบ JSON)
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

# 3. ปรับแต่งดีไซน์ด้วย CSS (แก้ไขจุดที่ทำให้เกิด Syntax Error แล้ว)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&display=swap');
    html, body, [class*="css"]  { font-family: 'Sarabun', sans-serif; }
    .main { background-color: #f0f2f6; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border-radius: 10px 10px 0px 0px;
        padding: 10px 20px;
        border: 1px solid #e6e9ef;
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
st.markdown("ระบบจัดการเช็คและหลักฐานเอกสารเบิกจ่าย (เวอร์ชันอัปเกรด All-in-One)")

tab1, tab2, tab3 = st.tabs(["📋 รายการเช็ค & จัดการ", "➕ เพิ่มรายการใหม่", "📤 ส่งออกรายงาน Excel"])

# --- 📋 TAB 1: แสดงรายการ / แก้ไข / ลบ (ในหน้าเดียว) ---
with tab1:
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM cheques ORDER BY date DESC", conn)
    conn.close()

    # ส่วนค้นหา
    search_col1, search_col2 = st.columns([2, 1])
    with search_col1:
        q = st.text_input("🔍 ค้นหา (ชื่อผู้รับ / เลขที่เช็ค)", placeholder="พิมพ์เพื่อค้นหา...")
    with search_col2:
        st_filter = st.selectbox("สถานะ", ["ทั้งหมด", "จ่ายแล้ว", "รอดำเนินการ", "ยกเลิก"])

    filtered_df = df.copy()
    if q:
        filtered_df = filtered_df[filtered_df['payee'].str.contains(q, na=False) | filtered_df['cheque_no'].str.contains(q, na=False)]
    if st_filter != "ทั้งหมด":
        filtered_df = filtered_df[filtered_df['status'] == st_filter]

    # สรุปยอด
    m1, m2, m3 = st.columns(3)
    with m1: st.markdown(f'<div class="metric-card"><div>ยอดจ่ายรวม</div><div style="font-size:24px; font-weight:bold;">{filtered_df["amount"].sum():,.2f} ฿</div></div>', unsafe_allow_html=True)
    with m2: st.markdown(f'<div class="metric-card"><div>ภาษีรวม</div><div style="font-size:24px; font-weight:bold;">{filtered_df["tax"].sum():,.2f} ฿</div></div>', unsafe_allow_html=True)
    with m3: st.markdown(f'<div class="metric-card"><div>จำนวนเช็ค</div><div style="font-size:24px; font-weight:bold;">{len(filtered_df)} ฉบับ</div></div>', unsafe_allow_html=True)

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
                        <b>ประเภท:</b> {row['cheque_type']} | <b>วันที่:</b> {row['date']} | <b>ภาษี:</b> {row['tax']:,.2f} บ.
                    </p>
                    <p style="color:#6c757d; font-style:italic;"><b>หมายเหตุ:</b> {row['note'] or '-'}</p>
                </div>
                """, unsafe_allow_html=True)

                # แสดงรูปภาพ (ถ้ามี)
                imgs = json.loads(row['images_json']) if row['images_json'] else []
                if imgs:
                    st.write("🖼️ **หลักฐานที่แนบไว้:**")
                    cols = st.columns(4)
                    for i, img_hex in enumerate(imgs):
                        with cols[i % 4]:
                            st.image(io.BytesIO(bytes.fromhex(img_hex)), use_container_width=True)
                
                # ปุ่มแก้ไขและลบ (Inline)
                c_edit, c_del, _ = st.columns([1, 1, 4])
                with c_edit:
                    exp = st.expander("✏️ แก้ไข")
                    if exp:
                        with st.form(f"edit_{row['id']}"):
                            e_no = st.text_input("เลขที่เช็ค", value=row['cheque_no'])
                            e_pay = st.text_input("ชื่อผู้รับ", value=row['payee'])
                            e_type = st.selectbox("ประเภทเช็ค", ["เช็ครายได้", "เช็คเงินอุดหนุน", "อื่น ๆ"], index=0)
                            e_amt = st.number_input("ยอดเงิน", value=float(row['amount']))
                            e_tax = st.number_input("ภาษี", value=float(row['tax']))
                            e_stat = st.selectbox("สถานะ", ["จ่ายแล้ว", "รอดำเนินการ", "ยกเลิก"], index=0)
                            e_note = st.text_area("หมายเหตุ", value=row['note'])
                            e_files = st.file_uploader("แนบรูปภาพใหม่ (จะทับของเดิม)", accept_multiple_files=True, key=f"f_{row['id']}")
                            if st.form_submit_button("💾 บันทึก"):
                                conn = sqlite3.connect(DB_NAME)
                                cursor = conn.cursor()
                                if e_files:
                                    new_imgs = json.dumps([f.read().hex() for f in e_files])
                                    cursor.execute("UPDATE cheques SET cheque_no=?, payee=?, amount=?, status=?, tax=?, cheque_type=?, note=?, images_json=? WHERE id=?", 
                                                 (e_no, e_pay, e_amt, e_stat, e_tax, e_type, e_note, new_imgs, row['id']))
                                else:
                                    cursor.execute("UPDATE cheques SET cheque_no=?, payee=?, amount=?, status=?, tax=?, cheque_type=?, note=? WHERE id=?", 
                                                 (e_no, e_pay, e_amt, e_stat, e_tax, e_type, e_note, row['id']))
                                conn.commit()
                                conn.close()
                                st.rerun()

                with c_del:
                    if st.button("❌ ลบ", key=f"del_{row['id']}"):
                        conn = sqlite3.connect(DB_NAME)
                        conn.cursor().execute("DELETE FROM cheques WHERE id=?", (row['id'],))
                        conn.commit()
                        conn.close()
                        st.rerun()
                st.markdown("---")
    else:
        st.info("ไม่พบรายการข้อมูล")

# --- ➕ TAB 2: เพิ่มรายการใหม่ ---
with tab2:
    st.subheader("📝 กรอกข้อมูลเช็คใบใหม่")
    with st.form("add_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            in_no = st.text_input("เลขที่เช็ค")
            in_pay = st.text_input("ชื่อผู้รับเงิน")
            in_type = st.selectbox("ประเภทเช็ค", ["เช็ครายได้", "เช็คเงินอุดหนุน", "อื่น ๆ"])
        with col2:
            in_amt = st.number_input("ยอดเงินสุทธิ", min_value=0.0)
            in_tax = st.number_input("ภาษีหัก ณ ที่จ่าย", min_value=0.0)
            in_date = st.date_input("วันที่", datetime.date.today())
        
        in_stat = st.selectbox("สถานะ", ["จ่ายแล้ว", "รอดำเนินการ", "ยกเลิก"])
        in_note = st.text_area("หมายเหตุ")
        in_files = st.file_uploader("📸 ถ่ายรูป/แนบรูปหลักฐาน (เลือกได้หลายรูป)", accept_multiple_files=True)
        
        if st.form_submit_button("✅ บันทึกข้อมูล"):
            if in_no and in_pay:
                img_hex_list = json.dumps([f.read().hex() for f in in_files]) if in_files else "[]"
                conn = sqlite3.connect(DB_NAME)
                conn.cursor().execute('''
                    INSERT INTO cheques (cheque_no, payee, amount, date, status, tax, cheque_type, images_json, note)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (in_no, in_pay, in_amt, in_date.strftime('%Y-%m-%d'), in_stat, in_tax, in_type, img_hex_list, in_note))
                conn.commit()
                conn.close()
                st.success("บันทึกสำเร็จ!")
                st.rerun()
            else:
                st.error("กรุณากรอกเลขที่เช็คและผู้รับเงิน")

# --- 📤 TAB 3: ส่งออกรายงาน ---
with tab3:
    st.subheader("📊 ส่งออกรายงานเป็น Excel")
    conn = sqlite3.connect(DB_NAME)
    ex_df = pd.read_sql_query("SELECT cheque_no, payee, amount, date, status, tax, cheque_type, note FROM cheques", conn)
    conn.close()
    if not ex_df.empty:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            ex_df.to_excel(writer, index=False)
        st.download_button("📥 ดาวน์โหลดไฟล์ Excel", data=buffer.getvalue(), file_name="report_cheque.xlsx")
