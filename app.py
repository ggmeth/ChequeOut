import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import pytesseract
from PIL import Image
import io

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="ระบบบันทึกการออกเช็คส่วนตัว", layout="wide")

# --- 1. การจัดการฐานข้อมูล SQLite (ใช้งานส่วนตัว ปลอดภัยในเครื่อง) ---
DB_NAME = "cheque_private.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS cheques (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            type TEXT,
            cheque_no TEXT,
            payee TEXT,
            amount REAL,
            status TEXT,
            tax REAL,
            evidence BLOB,
            note TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_data():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM cheques", conn)
    conn.close()
    return df

# --- 2. ฟังก์ชัน AI OCR แสกนข้อความจากรูปภาพ ---
def scan_image_text(image_bytes):
    try:
        image = Image.open(io.BytesIO(image_bytes))
        # ใช้ Tesseract ในการอ่านภาษาไทยและอังกฤษ
        text = pytesseract.image_to_string(image, lang='tha+eng')
        return text
    except Exception as e:
        return f"ไม่สามารถแสกนข้อความได้: {str(e)} (ตรวจสอบการติดตั้ง Tesseract OCR)"

# --- 3. ฟังก์ชันจัดระเบียบข้อมูลนำเข้า (Flexible Mapping) ---
def clean_column_name(col):
    col = str(col).strip()
    # รายการอิโมจิและสัญลักษณ์ที่พบบ่อยในไฟล์ของคุณ
    emojis = ["💡", "📝", "💰", "📅", "📌", "✨", "❌", "✔️"]
    for emoji in emojis:
        col = col.replace(emoji, "")
    return col.strip()

def map_flexible_df(uploaded_df):
    # Map คำพ้องความหมายตามโครงสร้างไฟล์ของคุณ
    mapping_rules = {
        'date': ['วันที่ออกเช็ค', 'วันที่', 'date', 'วันออกเช็ค'],
        'type': ['ประเภทเช็ค', 'ประเภท', 'type'],
        'cheque_no': ['เลขที่เช็ค', 'เลขเช็ค', 'cheque_no', 'เลขที่'],
        'payee': ['ชื่อผู้รับเงิน', 'ผู้รับเงิน', 'ชื่อผู้รับ', 'payee'],
        'amount': ['ยอดสุทธิในเช็ค (บาท)', 'ยอดสุทธิ', 'จำนวนเงิน', 'ยอดเงิน', 'amount', 'ยอดสุทธิในเช็ค'],
        'status': ['สถานะ', 'status'],
        'tax': ['ยอดภาษีที่หัก', 'ภาษี', 'tax', 'ภาษีหัก ณ ที่จ่าย', 'ยอดภาษีที่หัก '],
        'note': ['หมายเหตุ', 'note', 'ข้อความเพิ่มเติม']
    }
    
    cleaned_cols = {clean_column_name(col): col for col in uploaded_df.columns}
    final_df = pd.DataFrame()
    
    for target_col, synonyms in mapping_rules.items():
        found = False
        for syn in synonyms:
            for clean_col, original_col in cleaned_cols.items():
                if syn in clean_col or clean_col in syn:
                    final_df[target_col] = uploaded_df[original_col]
                    found = True
                    break
            if found: break
        if not found:
            final_df[target_col] = None
            
    return final_df

# --- 4. ส่วนหน้าตาเว็บแอป (UI) ---
st.title("🔒 ระบบบันทึกข้อมูลการออกเช็ค (ส่วนตัว)")
st.caption("ระบบทำงานบนเครื่องโลคอล ข้อมูลปลอดภัย 100% ไม่ถูกส่งขึ้นคลาวด์สาธารณะ")

tab1, tab2, tab3 = st.tabs(["📝 บันทึก/ดูข้อมูล", "📥 นำเข้าข้อมูล (Flexible Import)", "📊 ส่งออก & พิมพ์"])

# ---- TAB 1: บันทึกข้อมูลใหม่ & รายการทั้งหมด ----
with tab1:
    st.subheader("➕ เพิ่มรายการออกเช็คใหม่")
    
    ocr_file = st.file_uploader("📷 แสกนข้อความจากหลักฐานการตั้งเบิก (Auto-Fill)", type=["jpg", "png", "jpeg"], key="ocr_uploader")
    ocr_text = ""
    if ocr_file:
        img_bytes = ocr_file.read()
        ocr_text = scan_image_text(img_bytes)
        st.info(f"🔎 ข้อความที่ตรวจพบจากรูปภาพ: {ocr_text[:200]}...")

    with st.form("cheque_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            date_val = st.date_input("วันที่ออกเช็ค", datetime.now())
            cheque_type = st.selectbox("ประเภทเช็ค", ["รายได้", "อุดหนุน", "อื่นๆ"])
            cheque_no = st.text_input("เลขที่เช็ค")
        with col2:
            payee = st.text_input("ชื่อผู้รับเงิน")
            amount = st.number_input("ยอดสุทธิในเช็ค (บาท)", min_value=0.0, step=0.01)
            tax = st.number_input("ยอดภาษีที่หัก (ถ้ามี)", min_value=0.0, step=0.01)
        with col3:
            status = st.selectbox("สถานะ", ["จ่ายแล้ว", "ยังไม่ได้จ่าย", "ยกเลิก"])
            note = st.text_area("หมายเหตุ", value=ocr_text if ocr_text else "")
            evidence_file = st.file_uploader("📎 อัปโหลดรูปหลักฐานเอกสารตั้งเบิก", type=["jpg", "png", "jpeg"], key="evidence_uploader")

        submit_btn = st.form_submit_button("บันทึกข้อมูล")
        
        if submit_btn:
            binary_img = evidence_file.read() if evidence_file else None
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute('''
                INSERT INTO cheques (date, type, cheque_no, payee, amount, status, tax, evidence, note)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (date_val.strftime('%Y-%m-%d'), cheque_type, cheque_no, payee, amount, status, tax, binary_img, note))
            conn.commit()
            conn.close()
            st.success("บันทึกข้อมูลสำเร็จแล้ว!")
            st.slots = [] # Force clean UI
            st.rerun()

    st.write("---")
    st.subheader("📂 รายการเช็คทั้งหมดในระบบ")
    df_display = get_data()
    
    if not df_display.empty:
        st.write("🗑️ **เลือกรายการเพื่อลบ**")
        select_to_delete = st.multiselect("เลือกรหัส (ID) ที่ต้องการลบออกจากระบบ:", df_display['id'].tolist())
        if st.button("🔴 ลบรายการที่เลือก", key="delete_btn"):
            if select_to_delete:
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute(f"DELETE FROM cheques WHERE id IN ({','.join(map(str, select_to_delete))})")
                conn.commit()
                conn.close()
                st.success(f"ลบข้อมูลรหัส {select_to_delete} เรียบร้อยแล้ว")
                st.rerun()
            else:
                st.warning("กรุณาเลือกรายการที่ต้องการลบ")

        st.dataframe(df_display.drop(columns=['evidence']), use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูลในระบบ")

# ---- TAB 2: นำเข้าข้อมูลยืดหยุ่น ----
with tab2:
    st.subheader("📥 นำเข้าข้อมูลจากไฟล์เก่า (รองรับชื่อหัวคอลัมน์หลากหลาย & อิโมจิ)")
    st.write("ระบบจะแมตช์คำให้อัตโนมัติ เช่น '💡 ยอดภาษีที่หัก', 'ภาษี', 'tax' -> จะถูกรวมเป็นช่องเดียวกัน")
    
    uploaded_file = st.file_uploader("เลือกไฟล์ CSV หรือ Excel สำหรับนำเข้า", type=["csv", "xlsx"])
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'):
                raw_df = pd.read_csv(uploaded_file)
            else:
                raw_df = pd.read_excel(uploaded_file)
                
            st.write("📊 ข้อมูลดิบที่อัปโหลด:")
            st.dataframe(raw_df.head(3))
            
            mapped_df = map_flexible_df(raw_df)
            
            st.write("✅ ข้อมูลหลังผ่านการจัดกลุ่มและทำความสะอาดคำพ้องความหมายเรียบร้อย:")
            st.dataframe(mapped_df)
            
            if st.button("🚀 ยืนยันบันทึกข้อมูลนำเข้าทั้งหมดลงฐานข้อมูล", key="import_btn"):
                conn = sqlite3.connect(DB_NAME)
                mapped_df.to_sql('cheques', conn, if_exists='append', index=False)
                conn.commit()
                conn.close()
                st.success(f"นำเข้าข้อมูลสำเร็จจำนวน {len(mapped_df)} รายการ!")
                st.rerun()
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการอ่านไฟล์: {e}")

# ---- TAB 3: ส่งออกข้อมูล & สั่งพิมพ์ ----
with tab3:
    st.subheader("🖨️ เลือกรายการเพื่อสั่งพิมพ์ หรือ ส่งออก Excel")
    df_export = get_data()
    
    if not df_export.empty:
        selected_ids = st.multiselect("เลือกรายการเช็คที่ต้องการดำเนินการ (พิมพ์/ส่งออกเฉพาะรายการ):", df_export['id'].tolist(), default=df_export['id'].tolist())
        filtered_df = df_export[df_export['id'].isin(selected_ids)]
        
        st.dataframe(filtered_df.drop(columns=['evidence']), use_container_width=True)
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            filtered_df.drop(columns=['evidence']).to_excel(writer, index=False, sheet_name='Cheque_Records')
        
        st.download_button(
            label="📥 ดาวน์โหลดไฟล์ Excel (.xlsx)",
            data=buffer.getvalue(),
            file_name=f"รายงานการออกเช็ค_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_excel_btn"
        )
        
        if st.button("🖨️ เตรียมสั่งพิมพ์รายการที่เลือก", key="print_btn"):
            st.write("### 🖨️ เอกสารสำหรับสั่งพิมพ์")
            print_html = filtered_df.drop(columns=['evidence']).to_html(class_style="table table-striped")
            st.markdown(print_html, unsafe_allow_html=True)
            st.info("💡 แนะนำ: กดปุ่ม Ctrl + P (หรือ Cmd + P บน Mac) เพื่อสั่งพิมพ์หน้านี้ออกทางเครื่องพิมพ์ได้ทันที")
    else:
        st.info("ไม่มีข้อมูลที่จะส่งออก")
