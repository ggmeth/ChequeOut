import streamlit as st
import datetime

# ตั้งค่าหน้าจอโปรแกรม
st.set_page_config(page_title="KTB Cheque Printer", layout="centered")

# สมมติข้อมูลภาษาไทยที่ระบบ AI OCR สแกนและดึงได้จากเอกสาร
mock_ocr_payee = "บริษัท สมาร์ท ดีเวลลอปเม้นท์ จำกัด"
mock_ocr_amount = 45000.00

st.title("ระบบพิมพ์เช็คธนาคารกรุงไทย")
st.write("---")

# ==========================================
# 1. ส่วนฟอร์มจัดการข้อมูล (แสดงบนหน้าเว็บ)
# ==========================================
st.subheader("🤖 ข้อมูลที่ระบบดึงให้อัตโนมัติ (แก้ไขได้)")

# ช่องกรอกข้อมูลที่ดึงมาอัตโนมัติ แต่ยอมให้ผู้ใช้พิมพ์แก้ไขเองได้
payee_name = st.text_input("สั่งจ่าย (ชื่อร้าน/บริษัท)", value=mock_ocr_payee)
amount = st.number_input("จำนวนเงิน (ตัวเลข)", value=mock_ocr_amount, min_value=0.0, step=100.0, format="%.2f")

st.write("---")
st.subheader("✍️ รายละเอียดที่ต้องระบุเพิ่ม")

# ส่วนที่คุณเลือกเอง
cheque_date = st.date_input("วันที่บนหน้าเช็ค", datetime.date.today())
is_crossed = st.checkbox("ขีดคร่อมเช็ค (A/C Payee Only)", value=True)
is_delete_bearer = st.checkbox("ขีดฆ่า 'หรือผู้ถือ'", value=True)

# ฟังก์ชันแปลงตัวเลขเป็นตัวอักษรไทยแบบง่าย (สามารถหา library มาใส่เพิ่มได้)
def format_thai_baht_text(num):
    # ตัวอย่างผลลัพธ์ (ในโปรเจกต์จริงสามารถเชื่อมฟังก์ชันแปลงบาทเท็กซ์ได้)
    if num == 45000.00:
        return "สี่หมื่นห้าพันบาทถ้วน"
    return "ระบุจำนวนเงินตัวอักษรที่นี่"

amount_text = format_thai_baht_text(amount)
date_str = cheque_date.strftime("%d%m%Y") # แปลงวันที่เป็น 13072026

# ==========================================
# 2. ส่วนคำสั่ง CSS สำหรับจัดพิกัดพิมพ์ลงใบเช็คจริง
# ==========================================
# ใช้ st.markdown ร่วมกับ unsafe_allow_html เพื่อให้สไตล์งานพิมพ์ทำงานเมื่อกดพิมพ์หน้าเว็บ
st.markdown(f"""
    <style>
    /* ตั้งค่าพิกัดเช็คกรุงไทย (กว้าง 17.8 ซม. สูง 8.9 ซม.) */
    .print-area {{
        width: 17.8cm;
        height: 8.9cm;
        position: relative;
        background-color: #f9f9f9;
        border: 1px dashed #ccc;
        margin-top: 20px;
        font-family: monospace;
    }}
    .target-date {{ position: absolute; top: 0.8cm; right: 0.5cm; font-size: 18px; font-weight: bold; letter-spacing: 12px; }}
    .target-payee {{ position: absolute; top: 2.3cm; left: 2.5cm; font-size: 16px; font-weight: bold; }}
    .target-amount-text {{ position: absolute; top: 3.4cm; left: 3.5cm; font-size: 14px; font-weight: bold; }}
    .target-amount-num {{ position: absolute; top: 4.5cm; right: 1.0cm; font-size: 16px; font-weight: bold; }}
    
    .target-crossed {{ 
        position: absolute; top: 0.5cm; left: 1.5cm; width: 2.5cm; 
        border-top: 1px solid black; border-bottom: 1px solid black; 
        font-size: 9px; font-weight: bold; text-align: center; transform: rotate(-15deg); 
    }}
    .target-bearer-line {{ 
        position: absolute; top: 2.4cm; right: 2.2cm; width: 1.8cm; 
        border-top: 2px solid black; 
    }}

    /* ซ่อนเมนูและปุ่มของ Streamlit ทั้งหมดตอนสั่งพิมพ์ออกเครื่องพิมพ์ */
    @media print {{
        div[data-testid="stSidebar"], 
        header, 
        footer, 
        div.stButton, 
        div[data-testid="stBlock"] > div:not(.print-area) {{
            display: none !important;
        }}
        .print-area {{
            border: none !important;
            background: transparent !important;
        }}
    }}
    </style>

    <div class="print-area">
        <div class="target-date">{date_str}</div>
        <div class="target-payee">{payee_name}</div>
        <div class="target-amount-text">=== {amount_text} ===</div>
        <div class="target-amount-num">*{amount:,.2f}*</div>
        {"<div class='target-crossed'>A/C PAYEE ONLY</div>" if is_crossed else ""}
        {"<div class='target-bearer-line'></div>" if is_delete_bearer else ""}
    </div>
""", unsafe_allow_html=True)

st.write("---")

# ปุ่มกดสั่งพิมพ์ในหน้าจอ
if st.button("Print Cheque (สั่งพิมพ์เช็ค)"):
    # ใช้ JavaScript สั่งเบราว์เซอร์ให้เปิดหน้าต่างพิมพ์
    st.components.v1.html("<script>window.print();</script>", height=0)
