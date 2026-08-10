import streamlit as st
import pandas as pd
import re
from pythainlp.tokenize import word_tokenize
from pythainlp.tag import pos_tag
from pythainlp.corpus import thai_stopwords

# ตั้งค่าหน้าเว็บ
st.set_page_config(
    page_title="ระบบวิเคราะห์โพสต์เตือนภัย/ข่าวอุบัติเหตุ",
    page_icon="🚨",
    layout="wide"
)

stopwords = set(thai_stopwords())

# 1. Regex & Cleansing
def clean_text(text):
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\S+@\S+', '', text)
    text = re.sub(r'\d{3}[-\s]?\d{3}[-\s]?\d{4}', '', text)
    text = re.sub(r'[^\w\s\nก-๙]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# 2. Tokenization & Normalization
def process_tokens(text):
    tokens = word_tokenize(text, engine="newmm")
    return [w for w in tokens if w not in stopwords and w.strip() != '']

# 3. Topic Identification
def identify_topic(text):
    t = text.lower()
    if any(k in t for k in ['ชน', 'พลิกคว่ำ', 'ตกถนน', 'รถ', 'จราจร', 'ทางหลวง']):
        return "🚗 อุบัติเหตุทางถนน"
    elif any(k in t for k in ['น้ำท่วม', 'ฝนตกหนัก', 'ดินถล่ม', 'พายุ', 'น้ำป่า']):
        return "🌊 ภัยธรรมชาติ / น้ำท่วม"
    elif any(k in t for k in ['ไฟไหม้', 'เพลิงไหม้', 'กลุ่มควัน']):
        return "🔥 เพลิงไหม้"
    elif any(k in t for k in ['สารเคมี', 'แก๊ส', 'รั่วไหล', 'แอมโมเนีย']):
        return "☣️ ภัยสารเคมี / วัตถุอันตราย"
    else:
        return "⚠️ แจ้งเตือนภัยทั่วไป"

# 4. POS & NER / Extraction
def extract_entities(text):
    tokens = word_tokenize(text, engine="newmm")
    pos_tagged = pos_tag(tokens, engine="perceptron")
    
    locations, times, organizations = [], [], []
    
    # สกัดคำที่เป็นชื่อเฉพาะ/องค์กร/สถานที่ จาก POS tagging และ Keyword matching
    for word, pos in pos_tagged:
        if pos in ['PROPN', 'NPRU']:
            if any(k in word for k in ['ถนน', 'ซอย', 'แยก', 'แขวง', 'เขต', 'จังหวัด', 'อำเภอ', 'ตำบล', 'หมู่บ้าน', 'โค้ง']):
                locations.append(word)
            elif any(k in word for k in ['มูลนิธิ', 'กู้ภัย', 'ตำรวจ', 'สภ', 'ปภ', 'ศูนย์', 'รพ', 'โรงพยาบาล', 'กรม', 'ทหาร']):
                organizations.append(word)

    # Regex เสริมการจับสถานที่
    loc_regex = re.findall(r'(?:บริเวณ|หน้า|ซอย|ถนน|แยก|ตำบล|อำเภอ|จังหวัด|เขต|แขวง)\s*[ก-๙0-9]+', text)
    locations.extend(loc_regex)
            
    # Regex สกัดวันเวลา
    time_regex = re.findall(r'(\d{1,2}[:.]\d{2}\s*น\.|เวลา\s*\d{1,2}[:.]\d{2}|เช้า|ดึก|บ่าย|เมื่อวาน|วันนี้|เมื่อกลางดึก)', text)
    times.extend(time_regex)
    
    # Rule-based สกัดผู้บาดเจ็บ/เสียชีวิต
    casualties = re.findall(r'((?:บาดเจ็บ|เสียชีวิต|ผู้บาดเจ็บ|ผู้เสียชีวิต|สำลักควัน)\s*\d*\s*(?:ราย|คน)?)', text)
    
    # Rule-based สกัดหน่วยงานช่วยเหลือเพิ่มเติม
    rescue_terms = re.findall(r'(มูลนิธิ[ก-๙]+|กู้ภัย[ก-๙]+|เจ้าหน้าที่[ก-๙]+|เทศกิจ|ตำรวจ|โรงพยาบาล[ก-๙]+|ศูนย์วิทยุ[ก-๙]+|สภ\.[ก-๙]+|ปภ\.[ก-๙]+|กรม[ก-๙]+|ทหาร[ก-๙]+)', text)
    organizations.extend(rescue_terms)

    return {
        "locations": list(set(locations)) if locations else ["ไม่พบข้อมูลสถานที่ชัดเจน"],
        "times": list(set(times)) if times else ["ไม่พบข้อมูลเวลาชัดเจน"],
        "casualties": list(set(casualties)) if casualties else ["ไม่พบรายงานผู้บาดเจ็บ/เสียชีวิต"],
        "organizations": list(set(organizations)) if organizations else ["ไม่พบข้อมูลหน่วยงาน"]
    }

# --- GUI Section ---
st.title("🚨 ระบบวิเคราะห์โพสต์เตือนภัยและข่าวอุบัติเหตุ")
st.markdown("ระบบ NLP สกัดข้อมูลสถานที่ วันเวลา ผู้บาดเจ็บ และหน่วยงานช่วยเหลือจากข้อความภาษาไทย")

st.sidebar.header("📂 ข้อมูลทดสอบ")
uploaded_file = st.sidebar.file_uploader("อัปโหลดไฟล์ CSV (คอลัมน์ 'text')", type=["csv"])

input_text = ""
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    if 'text' in df.columns:
        input_text = st.sidebar.selectbox("เลือกข้อความตัวอย่างจากไฟล์:", df['text'].tolist())
    else:
        st.sidebar.error("ไฟล์ CSV ต้องมีคอลัมน์ชื่อ 'text'")

user_input = st.text_area("หรือพิมพ์/วางข้อความแจ้งเหตุที่นี่:", value=input_text, height=150)

if st.button("🔍 วิเคราะห์ข้อความ", type="primary"):
    if not user_input.strip():
        st.warning("กรุณากรอกข้อความก่อนทำการวิเคราะห์")
    else:
        cleaned = clean_text(user_input)
        tokens = process_tokens(cleaned)
        topic = identify_topic(cleaned)
        entities = extract_entities(cleaned)

        st.subheader("📊 ผลการวิเคราะห์")
        st.info(f"**ประเภทเหตุการณ์ (Topic):** {topic}")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📍 สถานที่เกิดเหตุ")
            for loc in entities["locations"]:
                st.write(f"- {loc}")
            st.markdown("### ⏰ วัน/เวลา เกิดเหตุ")
            for t in entities["times"]:
                st.write(f"- {t}")

        with col2:
            st.markdown("### 🚑 ผู้บาดเจ็บ/เสียชีวิต")
            for c in entities["casualties"]:
                st.write(f"- {c}")
            st.markdown("### 🏢 หน่วยงานช่วยเหลือ")
            for org in entities["organizations"]:
                st.write(f"- {org}")

        st.divider()
        with st.expander("🛠️ ดูรายละเอียด NLP (Cleansing & Tokenization & POS Tagging)"):
            st.write("**ข้อความหลังทำ Cleansing:**", cleaned)
            st.write("**ผลการตัดคำ (Tokens):**", tokens)
