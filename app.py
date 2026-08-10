import streamlit as st
import pandas as pd
import re
from pythainlp.tokenize import word_tokenize
from pythainlp.corpus import thai_stopwords

# ---------------------------------------------------------
# ตั้งค่าหน้าเว็บ และ CSS Custom
# ---------------------------------------------------------
st.set_page_config(
    page_title="ระบบวิเคราะห์โพสต์เตือนภัย/ข่าวอุบัติเหตุ",
    page_icon="🚨",
    layout="wide"
)

st.markdown("""
    <style>
    .stApp {
        background-color: #f4fbfb;
        color: #111111 !important;
    }
    p, span, label, li, div {
        color: #111111 !important;
        font-family: 'Sarabun', sans-serif;
    }
    h1, h2, h3, h4 {
        color: #005b66 !important;
        font-weight: bold !important;
    }
    textarea, input {
        background-color: #ffffff !important;
        color: #111111 !important;
        border: 1px solid #b2ebf2 !important;
        border-radius: 8px !important;
    }
    .stButton>button {
        background-color: #00acc1 !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        border: none !important;
        font-size: 16px !important;
        font-weight: bold !important;
        padding: 0.5rem 1.5rem !important;
    }
    .stButton>button:hover {
        background-color: #00838f !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #ffffff !important;
        border: 2px solid #80deea !important;
        border-radius: 12px !important;
        padding: 10px !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03) !important;
    }
    [data-testid="stSidebar"] {
        background-color: #e0f7fa !important;
    }
    </style>
""", unsafe_allow_html=True)

stopwords = set(thai_stopwords()) - {'หน้า', 'หลัง', 'ใน', 'นอก', 'บน', 'ใต้'}

# ---------------------------------------------------------
# Functions
# ---------------------------------------------------------
def clean_text(text):
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\S+@\S+', '', text)
    text = re.sub(r'\d{3}[-\s]?\d{3}[-\s]?\d{4}', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def process_tokens(text):
    tokens = word_tokenize(text, engine="newmm")
    return [w for w in tokens if w not in stopwords and w.strip() != '']

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

def extract_entities(text):
    locations, times, casualties, organizations = [], [], [], []

    # --- 1. สกัดสถานที่ ---
    loc_patterns = [
        r'(?:บริเวณ|หน้า|หลัง|ตรงข้าม|ใกล้|ทางเข้า|สี่แยก|สามแยก|แยก|ซอย|ถนน|หมู่บ้าน|แขวง|เขต|ตำบล|อำเภอ|จังหวัด|โค้ง|สะพาน)\s*([ก-๙0-9A-Za-z\s]+?)(?=\s|เมื่อ|เวลา|ส่งผล|ทำให้|เจ้าหน้าที่|มูลนิธิ|$)',
        r'(?:ถนน|ซอย|แยก|ต\.|อ\.|จ\.)\s*[ก-๙0-9]+'
    ]
    for pattern in loc_patterns:
        matches = re.findall(pattern, text)
        for m in matches:
            val = m.strip() if isinstance(m, str) else m[0].strip()
            if len(val) > 2 and val not in ['เกิดเหตุ', 'มีผู้', 'ได้รับบาดเจ็บ']:
                locations.append(val)

    # --- 2. สกัดวัน/เวลา ---
    time_patterns = [
        r'(?:วันที่\s*)?\d{1,2}\s*(?:ม\.ค\.|ก\.พ\.|มี\.ค\.|เม\.ย\.|พ\.ค\.|มิ\.ย\.|ก\.ค\.|ส\.ค\.|ก\.ย\.|ต\.ค\.|พ\.ย\.|ธ\.ค\.|มกราคม|กุมภาพันธ์|มีนาคม|เมษายน|พฤษภาคม|มิถุนายน|กรกฎาคม|สิงหาคม|กันยายน|ตุลาคม|พฤศจิกายน|ธันวาคม)(?:\s*(?:พ\.ศ\.|ศ\.)?\s*\d{2,4})?',
        r'\d{1,2}[:.]\d{2}\s*(?:น\.|นาฬิกา)',
        r'เวลา\s*\d{1,2}[:.]\d{2}\s*(?:น\.)?',
        r'(?:เมื่อกลางดึก|เมื่อเช้า|ช่วงเช้า|ช่วงบ่าย|ช่วงค่ำ|เมื่อวานนี้|วันนี้|ขณะนี้)'
    ]
    for pattern in time_patterns:
        times.extend(re.findall(pattern, text))

    # --- 3. สกัดจำนวนคนบาดเจ็บ/เสียชีวิต ---
    cas_patterns = [
        r'(?:บาดเจ็บ|ผู้บาดเจ็บ|สำลักควัน)\s*\d+\s*(?:ราย|คน)?',
        r'(?:เสียชีวิต|ผู้เสียชีวิต|ดับ|ดับคาที่)\s*\d+\s*(?:ราย|คน)?',
        r'\d+\s*(?:ราย|คน)\s*(?:บาดเจ็บ|เสียชีวิต)'
    ]
    for pattern in cas_patterns:
        casualties.extend(re.findall(pattern, text))

    # --- 4. สกัดหน่วยงานช่วยเหลือ และบทบาทการปฏิบัติงาน (รายละเอียดเพิ่มเติม) ---
    org_details = []
    
    # เช็คตำรวจและการดำเนินคดี
    if re.search(r'ตำรวจ|สภ\.|เจ้าหน้าที่ตำรวจ', text):
        action = ""
        if any(k in text for k in ['ดำเนินคดี', 'สอบสวน', 'ตรวจหาสาร', 'คุมตัว', 'แจ้งข้อหา']):
            action = " (หน้าที่: ตรวจสอบ/ดำเนินคดีทางกฎหมาย)"
        elif any(k in text for k in ['อำนวยความสะดวก', 'การจราจร']):
            action = " (หน้าที่: อำนวยความสะดวกการจราจร)"
        org_details.append(f"เจ้าหน้าที่ตำรวจ{action}")

    # เช็คทีมแพทย์และโรงพยาบาล
    if re.search(r'โรงพยาบาล|รพ\.|แพทย์|ปฐมพยาบาล', text):
        action = ""
        if any(k in text for k in ['นำส่ง', 'รักษา', 'บาดเจ็บ', 'ปฐมพยาบาล', 'ส่งตัว']):
            action = " (หน้าที่: ปฐมพยาบาล / รับตัวผู้บาดเจ็บเข้ารักษา)"
        org_details.append(f"โรงพยาบาล / ทีมแพทย์{action}")

    # เช็คกู้ภัย/มูลนิธิ
    if re.search(r'กู้ภัย|มูลนิธิ|สว่าง|ป่อเต็กตึ๊ง|ร่วมกตัญญู|อาสาสมัคร', text):
        action = ""
        if any(k in text for k in ['ช่วยเหลือ', 'ค้นหา', 'ตัดถ่าง', 'ลำเลียง']):
            action = " (หน้าที่: กู้ภัยและช่วยเหลือผู้ประสบเหตุ)"
        org_details.append(f"หน่วยกู้ภัย / มูลนิธิ{action}")

    # เช็คดับเพลิง/ปภ.
    if re.search(r'ดับเพลิง|บรรเทาสาธารณภัย|ปภ\.|นักผจญเพลิง', text):
        action = " (หน้าที่: ควบคุมเพลิง / ดับไฟ)"
        org_details.append(f"เจ้าหน้าที่ดับเพลิง / ปภ.{action}")

    organizations = list(dict.fromkeys(org_details))

    return {
        "locations": list(dict.fromkeys(locations)) if locations else ["ไม่พบข้อมูลสถานที่ชัดเจน"],
        "times": list(dict.fromkeys(times)) if times else ["ไม่พบข้อมูลวัน/เวลาชัดเจน"],
        "casualties": list(dict.fromkeys(casualties)) if casualties else ["ไม่พบรายงานผู้บาดเจ็บ/เสียชีวิต"],
        "organizations": organizations if organizations else ["ไม่พบข้อมูลหน่วยงานช่วยเหลือ"]
    }

# ---------------------------------------------------------
# GUI Section
# ---------------------------------------------------------
st.title("🚨 ระบบวิเคราะห์โพสต์เตือนภัยและข่าวอุบัติเหตุ")
st.caption("💎 ประมวลผลสกัดข้อมูลสถานที่ วัน/เวลา ตัวเลขผู้บาดเจ็บ และรายละเอียดหน่วยงานช่วยเหลือ")

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
    except Exception:
        st.sidebar.error("เกิดข้อผิดพลาดในการอ่านไฟล์ CSV")

user_input = st.text_area("วางข้อความแจ้งเหตุเพื่อทดสอบวิเคราะห์:", value=input_text, height=140)

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

        col1, col2 = st.columns(2)
        
        with col1:
            with st.container(border=True):
                st.markdown("### 📍 สถานที่เกิดเหตุ")
                for loc in entities["locations"]:
                    st.write(f"• {loc}")

            with st.container(border=True):
                st.markdown("### ⏰ วัน/เวลา เกิดเหตุ")
                for t in entities["times"]:
                    st.write(f"• {t}")

        with col2:
            with st.container(border=True):
                st.markdown("### 🚑 ผู้บาดเจ็บ / เสียชีวิต")
                for c in entities["casualties"]:
                    st.write(f"• {c}")

            with st.container(border=True):
                st.markdown("### 🏢 หน่วยงานช่วยเหลือ")
                for org in entities["organizations"]:
                    st.write(f"• {org}")

        with st.expander("🛠️ ดูรายละเอียดการประมวลผล NLP (Tokens & Cleansing)"):
            st.write("**ข้อความหลังทำ Cleansing:**", cleaned)
            st.write("**ผลการตัดคำ (Tokens):**", tokens)
