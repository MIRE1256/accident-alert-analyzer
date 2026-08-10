import streamlit as st
import pandas as pd
import re
from pythainlp.tokenize import word_tokenize
from pythainlp.tag import pos_tag
from pythainlp.corpus import thai_stopwords

# ---------------------------------------------------------
# ตั้งค่าหน้าเว็บ และ CSS Custom ธีมสีฟ้าเทอร์ควอยซ์ & ขาวไข่มุก
# ---------------------------------------------------------
st.set_page_config(
    page_title="ระบบวิเคราะห์โพสต์เตือนภัย/ข่าวอุบัติเหตุ",
    page_icon="🚨",
    layout="wide"
)

st.markdown("""
    <style>
    /* พื้นหลังหลัก โทนขาวไข่มุก (Pearl White) */
    .stApp {
        background-color: #f8fafb;
    }
    
    /* หัวข้อหลัก โทนฟ้าเทอร์ควอยซ์เข้ม (Dark Turquoise) */
    h1, h2, h3 {
        color: #006978 !important;
        font-family: 'Sarabun', sans-serif;
    }
    
    /* ปรับแต่งปุ่มกด โทนสีฟ้าเทอร์ควอยซ์สดใส (Turquoise Blue) */
    .stButton>button {
        background-color: #00acc1 !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        border: none !important;
        font-size: 16px !important;
        font-weight: bold !important;
        padding: 0.6rem 1.2rem !important;
        box-shadow: 0 2px 5px rgba(0, 172, 193, 0.3);
    }
    .stButton>button:hover {
        background-color: #00838f !important;
        color: #ffffff !important;
    }
    
    /* การ์ดแสดงผล ขาวไข่มุกตัดขอบฟ้าเทอร์ควอยซ์ */
    .result-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        border-left: 6px solid #26c6da;
        box-shadow: 0 4px 12px rgba(0,0,0,0.04);
        margin-bottom: 18px;
    }
    
    /* ปรับแต่ง Sidebar */
    [data-testid="stSidebar"] {
        background-color: #f0f7f8;
    }
    </style>
""", unsafe_allow_html=True)

stopwords = set(thai_stopwords()) - {'หน้า', 'หลัง', 'ใน', 'นอก', 'บน', 'ใต้'}

# ---------------------------------------------------------
# 1. Cleansing (ทำความสะอาดข้อความ)
# ---------------------------------------------------------
def clean_text(text):
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\S+@\S+', '', text)
    text = re.sub(r'\d{3}[-\s]?\d{3}[-\s]?\d{4}', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# ---------------------------------------------------------
# 2. Tokenization
# ---------------------------------------------------------
def process_tokens(text):
    tokens = word_tokenize(text, engine="newmm")
    return [w for w in tokens if w not in stopwords and w.strip() != '']

# ---------------------------------------------------------
# 3. Topic Identification (จำแนกหมวดหมู่)
# ---------------------------------------------------------
def identify_topic(text):
    t = text.lower()
    if any(k in t for k in ['ชน', 'พลิกคว่ำ', 'ตกถนน', 'รถ', 'จราจร', 'ทางหลวง', 'สี่แยก', 'เฉี่ยว']):
        return "🚗 อุบัติเหตุทางถนน / จราจร"
    elif any(k in t for k in ['น้ำท่วม', 'ฝนตกหนัก', 'ดินถล่ม', 'พายุ', 'น้ำป่า', 'ลมกระโชก']):
        return "🌊 ภัยธรรมชาติ / น้ำท่วม"
    elif any(k in t for k in ['ไฟไหม้', 'เพลิงไหม้', 'กลุ่มควัน', 'ไหม้บ้าน', 'ไฟฟ้าลัดวงจร']):
        return "🔥 เพลิงไหม้"
    elif any(k in t for k in ['สารเคมี', 'แก๊ส', 'รั่วไหล', 'แอมโมเนีย', 'ระเบิด']):
        return "☣️ ภัยสารเคมี / วัตถุอันตราย"
    else:
        return "⚠️ แจ้งเตือนภัยทั่วไป"

# ---------------------------------------------------------
# 4. Enhanced Extraction (การสกัดข้อมูล)
# ---------------------------------------------------------
def extract_entities(text):
    locations = []
    times = []
    casualties = []
    organizations = []

    # --- A. สกัดสถานที่ ---
    loc_patterns = [
        r'(?:บริเวณ|หน้า|หลัง|ตรงข้าม|ใกล้|ทางเข้า|สี่แยก|สามแยก|แยก|ซอย|ถนน|หมู่บ้าน|แขวง|เขต|ตำบล|อำเภอ|จังหวัด|โค้ง|หน้าโรงเรียน|หน้าวัด|สะพานพุทธ|สะพาน)\s*([ก-๙0-9A-Za-z\s]+?)(?=\s|เมื่อ|เวลา|ส่งผล|ทำให้|เจ้าหน้าที่|มูลนิธิ|$)',
        r'(?:ถนน|ซอย|แยก|ต\.|อ\.|จ\.)\s*[ก-๙0-9]+'
    ]
    for pattern in loc_patterns:
        matches = re.findall(pattern, text)
        for m in matches:
            val = m.strip() if isinstance(m, str) else m[0].strip()
            if len(val) > 2 and val not in ['เกิดเหตุ', 'มีผู้']:
                locations.append(val)

    # --- B. สกัดเวลา ---
    time_patterns = [
        r'\d{1,2}[:.]\d{2}\s*(?:น\.|นาฬิกา)?',
        r'เวลา\s*\d{1,2}[:.]\d{2}',
        r'(?:เมื่อกลางดึก|เมื่อเช้า|ช่วงเช้า|ช่วงบ่าย|ช่วงค่ำ|ดึกดื่น|เมื่อวานนี้|วันนี้|ขณะนี้)'
    ]
    for pattern in time_patterns:
        matches = re.findall(pattern, text)
        times.extend(matches)

    # --- C. สกัดผู้บาดเจ็บ / ผู้เสียชีวิต ---
    cas_patterns = [
        r'(?:เสียชีวิต|ผู้เสียชีวิต|ดับ|ดับคาที่)\s*\d*\s*(?:ราย|คน)?',
        r'(?:บาดเจ็บ|ผู้บาดเจ็บ|สาหัส|สำลักควัน)\s*\d*\s*(?:ราย|คน)?'
    ]
    for pattern in cas_patterns:
        matches = re.findall(pattern, text)
        casualties.extend(matches)

    # --- D. สกัดหน่วยงานช่วยเหลือ ---
    org_patterns = [
        r'(?:มูลนิธิ|กู้ภัย|สว่าง|ป่อเต็กตึ๊ง|ร่วมกตัญญู|ศูนย์วิทยุ|เจ้าหน้าที่|ตำรวจ|สภ\.|ปภ\.|รพ\.|โรงพยาบาล|เทศกิจ|ทหาร)[ก-๙A-Za-z0-9\.\s]*'
    ]
    for pattern in org_patterns:
        matches = re.findall(pattern, text)
        for m in matches:
            cleaned_org = m.strip()
            if len(cleaned_org) > 3:
                organizations.append(cleaned_org)

    return {
        "locations": list(dict.fromkeys(locations)) if locations else ["ไม่พบข้อมูลสถานที่ชัดเจน"],
        "times": list(dict.fromkeys(times)) if times else ["ไม่พบข้อมูลเวลาชัดเจน"],
        "casualties": list(dict.fromkeys(casualties)) if casualties else ["ไม่พบรายงานผู้บาดเจ็บ/เสียชีวิต"],
        "organizations": list(dict.fromkeys(organizations)) if organizations else ["ไม่พบข้อมูลหน่วยงาน"]
    }

# ---------------------------------------------------------
# GUI Section (ส่วนแสดงผลสีฟ้าเทอร์ควอยซ์ & ขาวไข่มุก)
# ---------------------------------------------------------
st.title("🚨 ระบบวิเคราะห์โพสต์เตือนภัยและข่าวอุบัติเหตุ")
st.caption("💎 ระบบ NLP ภาษาไทยประมวลผลการสกัดข้อมูลสถานที่ วันเวลา ผู้บาดเจ็บ และหน่วยงานช่วยเหลือ")

st.sidebar.header("📂 ตัวเลือกข้อมูล")
uploaded_file = st.sidebar.file_uploader("อัปโหลดไฟล์ CSV (คอลัมน์ 'text')", type=["csv"])

input_text = ""
if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        if 'text' in df.columns:
            input_text = st.sidebar.selectbox("เลือกข้อความตัวอย่างจากไฟล์ CSV:", df['text'].tolist())
        else:
            st.sidebar.error("ไฟล์ CSV ต้องมีคอลัมน์ชื่อ 'text'")
    except Exception as e:
        st.sidebar.error("เกิดข้อผิดพลาดในการอ่านไฟล์ CSV")

user_input = st.text_area("หรือพิมพ์/วางข้อความแจ้งเหตุเพื่อทดสอบ:", value=input_text, height=140)

if st.button("🔍 วิเคราะห์ข้อความ", type="primary"):
    if not user_input.strip():
        st.warning("กรุณากรอกข้อความก่อนทำการวิเคราะห์")
    else:
        cleaned = clean_text(user_input)
        tokens = process_tokens(cleaned)
        topic = identify_topic(cleaned)
        entities = extract_entities(cleaned)

        st.markdown("---")
        st.subheader("📊 ผลการวิเคราะห์ข้อมูล")
        
        st.info(f"**ประเภทเหตุการณ์ (Topic):** {topic}")

        # การแสดงผลแบบการ์ดสีขาวไข่มุก ตัดขอบฟ้าเทอร์ควอยซ์
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown("### 📍 สถานที่เกิดเหตุ")
            for loc in entities["locations"]:
                st.write(f"- {loc}")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown("### ⏰ วัน/เวลา เกิดเหตุ")
            for t in entities["times"]:
                st.write(f"- {t}")
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown("### 🚑 ผู้บาดเจ็บ / เสียชีวิต")
            for c in entities["casualties"]:
                st.write(f"- {c}")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown("### 🏢 หน่วยงานช่วยเหลือ")
            for org in entities["organizations"]:
                st.write(f"- {org}")
            st.markdown('</div>', unsafe_allow_html=True)

        with st.expander("🛠️ ดูรายละเอียดการประมวลผล NLP (Tokens & Cleansing)"):
            st.write("**ข้อความหลังทำ Cleansing:**", cleaned)
            st.write("**ผลการตัดคำ (Tokens):**", tokens)
