import streamlit as st
import pandas as pd
import re
from pythainlp.tokenize import word_tokenize
from pythainlp.corpus import thai_stopwords

# ---------------------------------------------------------
# ตั้งค่าหน้าเว็บ และ CSS Custom (โทนสีฟ้าเทอร์ควอยซ์)
# ---------------------------------------------------------
st.set_page_config(
    page_title="ระบบวิเคราะห์โพสต์เตือนภัย/ข่าวอุบัติเหตุ",
    page_icon="🚨",
    layout="wide"
)

st.markdown("""
    <style>
    header[data-testid="stHeader"] {
        background-color: #00acc1 !important;
    }
    header[data-testid="stHeader"] * {
        color: #ffffff !important;
    }
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
        padding: 12px !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03) !important;
    }
    [data-testid="stSidebar"] {
        background-color: #e0f7fa !important;
    }

    /* กล่องสรุปประเด็นสำคัญ */
    .summary-box {
        background-color: #fff9e6;
        border-left: 6px solid #d9381e;
        border-radius: 6px;
        padding: 16px 20px;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .summary-title {
        background-color: #d9381e;
        color: #ffffff !important;
        display: inline-block;
        padding: 4px 10px;
        font-size: 14px;
        font-weight: bold;
        border-radius: 4px;
        margin-bottom: 10px;
    }
    .summary-text {
        font-size: 16px;
        font-weight: 600;
        color: #222222 !important;
        line-height: 1.6;
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

def generate_summary(text):
    sentences = [s.strip() for s in text.split(' ') if len(s.strip()) > 10]
    if not sentences:
        return text
    key_sentences = []
    for s in sentences:
        if any(k in s for k in ['ดำเนินคดี', 'บาดเจ็บ', 'เสียชีวิต', 'พุ่งชน', 'ชน', 'เกิดเหตุ', 'พบสารเสพติด']):
            key_sentences.append(s)
    if key_sentences:
        return ' '.join(key_sentences[:2])
    return ' '.join(sentences[:2])

def extract_action_details(text):
    actions = []
    if re.search(r'ขับรถ|พุ่งชน|ชน|พลิกคว่ำ|เสียหลัก|ชนกำแพง|ตกข้างทาง', text):
        m = re.search(r'(?:ขับรถ|พุ่งชน|ชน|พลิกคว่ำ|เสียหลัก|ตกข้างทาง)[^,.\n]+', text)
        if m:
            actions.append(f"📌 การกระทำ/เหตุการณ์: {m.group(0).strip()}")
            
    if re.search(r'สารเสพติด|เมา|ดื่ม|มึนเมา|หลับใน|เบรกแตก|ความเร็วสูง', text):
        m = re.search(r'พบ[^,.\n]*(?:สารเสพติด|แอลกอฮอล์)|(?:เมา|หลับใน|เบรกแตก|สารเสพติด)[^,.\n]*', text)
        if m:
            actions.append(f"⚠️ ปัจจัยเสี่ยง/สาเหตุ: {m.group(0).strip()}")
            
    if re.search(r'ดำเนินคดี|แจ้งข้อหา|จับกุม|คุมตัว|ตั้งข้อหา', text):
        m = re.search(r'(?:ดำเนินคดี|แจ้งข้อหา|จับกุม|คุมตัว|ตั้งข้อหา)[^,.\n]+', text)
        if m:
            actions.append(f"⚖️ การดำเนินคดี: {m.group(0).strip()}")

    return actions if actions else ["ไม่พบรายละเอียดพฤติกรรมชัดเจน"]

def calculate_severity(casualties_list, text):
    has_death = any('เสียชีวิต' in c or 'ดับ' in c for c in casualties_list)
    num_injured = 0
    for c in casualties_list:
        nums = re.findall(r'\d+', c)
        if nums:
            num_injured += int(nums[0])
            
    if has_death or num_injured >= 10 or 'สารเสพติด' in text or 'ร้ายแรง' in text:
        return "🔴 ความรุนแรงระดับสูงมาก (Extreme)"
    elif num_injured >= 3:
        return "🟠 ความรุนแรงระดับสูง (High)"
    else:
        return "🟡 ความรุนแรงระดับปานกลาง (Medium)"

def extract_structured_location(text):
    loc_info = []

    site = re.search(r'(?:ศูนย์เด็กเล็ก[ก-๙]*|โรงเรียน[ก-๙]*|วัด[ก-๙]*|ตลาด[ก-๙]*|โรงงาน[ก-๙]*|สี่แยก[ก-๙]*|สามแยก[ก-๙]*|สะพาน[ก-๙]*)', text)
    if site:
        loc_info.append(f"🏫 **ชื่อสถานที่:** {site.group(0).strip()}")

    village = re.search(r'(?:หมู่บ้าน[ก-๙0-9]+|ม\.\d+|หมู่ที่\s*\d+)', text)
    if village:
        loc_info.append(f"🏡 **หมู่บ้าน/หมู่ที่:** {village.group(0).strip()}")

    subdistrict = re.search(r'(?:ตำบล|ต\.|แขวง)\s*([ก-๙]+)', text)
    if subdistrict:
        loc_info.append(f"📍 **ตำบล/แขวง:** ต.{subdistrict.group(1).strip()}")
    elif "แก่งเสี้ยน" in text:
        loc_info.append("📍 **ตำบล/แขวง:** ต.แก่งเสี้ยน")

    district = re.search(r'(?:อำเภอ|อ\.|เขต)\s*([ก-๙]+)', text)
    if district:
        loc_info.append(f"🏙️ **อำเภอ/เขต:** อ.{district.group(1).strip()}")
    elif "เมืองกาญจนบุรี" in text:
        loc_info.append("🏙️ **อำเภอ/เขต:** อ.เมืองกาญจนบุรี")

    province = re.search(r'(?:จังหวัด|จ\.)\s*([ก-๙]+)', text)
    if province:
        loc_info.append(f"🗺️ **จังหวัด:** จ.{province.group(1).strip()}")
    elif "กาญจนบุรี" in text:
        loc_info.append("🗺️ **จังหวัด:** จ.กาญจนบุรี")

    return loc_info if loc_info else ["ไม่พบข้อมูลสถานที่ชัดเจน"]

def extract_organizations_detailed(text):
    org_list = []

    if re.search(r'ตำรวจ|สภ\.|เจ้าหน้าที่ตำรวจ|พนักงานสอบสวน', text):
        police_name = re.search(r'(?:สภ\.|สถานีตำรวจภูธร)\s*([ก-๙]+)', text)
        station = f" ({police_name.group(0)})" if police_name else ""
        
        actions = []
        if 'ดำเนินคดี' in text or 'แจ้งข้อหา' in text: actions.append("ดำเนินคดีทางกฎหมาย")
        if 'ตรวจ' in text or 'สารเสพติด' in text: actions.append("ตรวจวัดสารเสพติด/คุมประพฤติ")
        if 'คุมตัว' in text or 'จับกุม' in text: actions.append("ควบคุมตัวผู้ก่อเหตุ")
        
        act_str = ", ".join(actions) if actions else "ตรวจสอบที่เกิดเหตุและสอบสวน"
        org_list.append(f"👮 **เจ้าหน้าที่ตำรวจ{station}**\n  - **บทบาท:** {act_str}")

    if re.search(r'โรงพยาบาล|รพ\.|แพทย์|พยาบาล|ปฐมพยาบาล', text):
        hosp_name = re.search(r'(?:รพ\.|โรงพยาบาล)\s*([ก-๙]+)', text)
        hosp = f" ({hosp_name.group(0)})" if hosp_name else ""
        
        actions = []
        if 'รักษา' in text or 'รับตัว' in text: actions.append("รับตัวผู้บาดเจ็บเข้ารักษา")
        if 'ตรวจ' in text or 'ตรวจร่างกาย' in text: actions.append("ตรวจชันสูตร/ตรวจร่างกายผู้ต้องหา")
        if 'ปฐมพยาบาล' in text: actions.append("ปฐมพยาบาลเบื้องต้น")
        
        act_str = ", ".join(actions) if actions else "ให้การรักษาทางการแพทย์"
        org_list.append(f"🏥 **ทีมแพทย์ / โรงพยาบาล{hosp}**\n  - **บทบาท:** {act_str}")

    if re.search(r'กู้ภัย|มูลนิธิ|สว่าง|ป่อเต็กตึ๊ง|ร่วมกตัญญู|อาสาสมัคร|บรรเทาสาธารณภัย', text):
        rescue_name = re.search(r'(?:มูลนิธิ|กู้ภัย)\s*([ก-๙]+)', text)
        resc = f" ({rescue_name.group(0)})" if rescue_name else ""
        org_list.append(f"🚑 **หน่วยกู้ภัย / มูลนิธิ{resc}**\n  - **บทบาท:** ลำเลียงผู้บาดเจ็บ และอำนวยความสะดวกในพื้นที่")

    if re.search(r'อบต\.|เทศบาล|ศูนย์เด็กเล็ก|ฝ่ายปกครอง|กทม\.|สำนักงานเขต', text):
        org_list.append("🏢 **หน่วยงานปกครองท้องถิ่น / อบต. / เทศบาล**\n  - **บทบาท:** ประสานงานพื้นที่ และดูแลเยียวยาเบื้องต้น")

    return org_list if org_list else ["ไม่พบข้อมูลหน่วยงานช่วยเหลือชัดเจน"]

def extract_entities(text):
    times, casualties = [], []

    # --- สกัดวัน/เวลา ---
    time_patterns = [
        r'(?:วันที่\s*)?\d{1,2}\s*(?:ม\.ค\.|ก\.พ\.|มี\.ค\.|เม\.ย\.|พ\.ค\.|มิ\.ย\.|ก\.ค\.|ส\.ค\.|ก\.ย\.|ต\.ค\.|พ\.ย\.|ธ\.ค\.|มกราคม|กุมภาพันธ์|มีนาคม|เมษายน|พฤษภาคม|มิถุนายน|กรกฎาคม|สิงหาคม|กันยายน|ตุลาคม|พฤศจิกายน|ธันวาคม)(?:\s*(?:พ\.ศ\.|ศ\.)?\s*\d{2,4})?',
        r'\d{1,2}[:.]\d{2}\s*(?:น\.|นาฬิกา)',
        r'เวลา\s*\d{1,2}[:.]\d{2}\s*(?:น\.)?',
        r'(?:เมื่อกลางดึก|เมื่อเช้า|ช่วงเช้า|ช่วงบ่าย|ช่วงค่ำ|เมื่อวานนี้|วันนี้|ขณะนี้)'
    ]
    for pattern in time_patterns:
        times.extend(re.findall(pattern, text))

    # --- สกัดจำนวนคนบาดเจ็บ/เสียชีวิต (สกัดเน้นระบุตัวเลขแม่นยำ) ---
    # 1. ค้นหาผู้บาดเจ็บ
    inj_match = re.search(r'(?:บาดเจ็บ|สำลักควัน)[^0-9\n]{0,20}(\d+)\s*(คน|ราย)', text)
    if not inj_match:
        inj_match = re.search(r'(\d+)\s*(คน|ราย)[^0-9\n]{0,10}(?:บาดเจ็บ)', text)
        
    if inj_match:
        casualties.append(f"บาดเจ็บ {inj_match.group(1)} {inj_match.group(2)}")

    # 2. ค้นหาผู้เสียชีวิต
    death_match = re.search(r'(?:เสียชีวิต|ดับ)[^0-9\n]{0,20}(\d+)\s*(คน|ราย)', text)
    if not death_match:
        death_match = re.search(r'(\d+)\s*(คน|ราย)[^0-9\n]{0,10}(?:เสียชีวิต|ดับ)', text)

    if death_match:
        casualties.append(f"เสียชีวิต {death_match.group(1)} {death_match.group(2)}")

    return {
        "locations": extract_structured_location(text),
        "times": list(dict.fromkeys(times)) if times else ["ไม่พบข้อมูลวัน/เวลาชัดเจน"],
        "casualties": list(dict.fromkeys(casualties)) if casualties else ["ไม่พบรายงานผู้บาดเจ็บ/เสียชีวิต"],
        "organizations": extract_organizations_detailed(text)
    }

# ---------------------------------------------------------
# GUI Section
# ---------------------------------------------------------
st.title("🚨 ระบบวิเคราะห์โพสต์เตือนภัยและข่าวอุบัติเหตุ")
st.caption("💎 สกัดข้อมูลเชิงลึก: สรุปประเด็น สถานที่ วัน/เวลา พฤติกรรมเหตุการณ์ ผู้บาดเจ็บ และหน่วยงานช่วยเหลือ")

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

user_input = st.text_area("วางข้อความแจ้งเหตุเพื่อทดสอบวิเคราะห์:", value=input_text, height=130)

if st.button("🔍 วิเคราะห์ข้อความ", type="primary"):
    if not user_input.strip():
        st.warning("กรุณากรอกข้อความก่อนทำการวิเคราะห์")
    else:
        cleaned = clean_text(user_input)
        tokens = process_tokens(cleaned)
        topic = identify_topic(cleaned)
        entities = extract_entities(cleaned)
        action_details = extract_action_details(cleaned)
        severity = calculate_severity(entities["casualties"], cleaned)
        summary = generate_summary(cleaned)

        st.markdown("---")
        
        st.markdown(f"""
            <div class="summary-box">
                <div class="summary-title">สรุปประเด็นสำคัญ</div>
                <div class="summary-text">{summary}</div>
            </div>
        """, unsafe_allow_html=True)

        st.subheader("📊 ผลการวิเคราะห์ข้อมูลเชิงลึก")
        
        col_top1, col_top2 = st.columns(2)
        with col_top1:
            st.info(f"**ประเภทเหตุการณ์:** {topic}")
        with col_top2:
            st.error(f"**ระดับประเมินสถานการณ์:** {severity}")

        col1, col2 = st.columns(2)
        
        with col1:
            with st.container(border=True):
                st.markdown("### 📍 สถานที่เกิดเหตุ (Where)")
                for loc in entities["locations"]:
                    st.markdown(f"• {loc}")

            with st.container(border=True):
                st.markdown("### ⏰ วัน/เวลา เกิดเหตุ (When)")
                for t in entities["times"]:
                    st.write(f"• {t}")

        with col2:
            with st.container(border=True):
                st.markdown("### 🚑 ผู้บาดเจ็บ / เสียชีวิต (Casualties)")
                for c in entities["casualties"]:
                    st.write(f"• {c}")

            with st.container(border=True):
                st.markdown("### 🏢 หน่วยงานช่วยเหลือ (Who Helped)")
                for org in entities["organizations"]:
                    st.markdown(f"{org}")

        with st.container(border=True):
            st.markdown("### 🎬 รายละเอียดพฤติกรรมและการกระทำ (What & How)")
            for act in action_details:
                st.write(f"{act}")

        with st.expander("🛠️ ดูรายละเอียดการประมวลผล NLP (Tokens & Cleansing)"):
            st.write("**ข้อความหลังทำ Cleansing:**", cleaned)
            st.write("**ผลการตัดคำ (Tokens):**")
            st.info(", ".join([f"'{w}'" for w in tokens]))
