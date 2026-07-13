import streamlit as st
import datetime

# ตั้งค่าหน้าจอโปรแกรมของระบบเดิม
st.set_page_config(page_title="Cheque Out", layout="centered")

st.title("ระบบแสกนเอกสารตั้งเบิก")
st.write("---")

# ส่วนอัปโหลดและแสดงผลรูปภาพเอกสารเดิม
st.subheader("📷 แสกนเอกสารตั้งเบิก")
uploaded_file = st.file_uploader("เลือกภาพถ่ายหรือแสกนหน้าเอกสาร", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    # แสดงรูปภาพเอกสารที่ผู้ใช้อัปโหลด
    st.image(uploaded_file, caption="เอกสารตั้งเบิกที่อัปโหลด", use_container_width=True)
    st.success("อัปโหลดเอกสารเรียบร้อยแล้ว")
else:
    st.info("กรุณาอัปโหลดไฟล์ภาพเอกสารตั้งเบิกเพื่อเริ่มใช้งาน")
