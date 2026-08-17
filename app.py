import os
import re
from pathlib import Path

import faiss
import numpy as np
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
from sentence_transformers import SentenceTransformer

# ============================================================
# Nature Noob: Doi Khuntan
# Beginner Hiking Chatbot - DOI KHUN TAN ONLY
# ============================================================

# ------------------------------------------------------------
# 0. Path, Environment และชื่อแอป
# ------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
KB_PATH = BASE_DIR / "trekking_gear_kb.md"

load_dotenv(BASE_DIR / ".env", override=True)

APP_NAME = "Nature Noob: Doi Khuntan"
APP_TAGLINE = "เพื่อนพาเนเจอร์นู้บไปดอยขุนตาล — คู่มือเฉพาะทางสำหรับมือใหม่"


# ------------------------------------------------------------
# 1. ตั้งค่าหน้าเว็บ
# ------------------------------------------------------------

st.set_page_config(
    page_title=f"{APP_NAME}",
    page_icon="⛺",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ------------------------------------------------------------
# 1.1 ธีม "Nature Noob" — CSS
# ------------------------------------------------------------

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Kanit:wght@400;500;600;700&family=Sarabun:wght@300;400;500;600&display=swap');

:root {
    --primary-green: #344c33;
    --primary-light: #466045;
    --bg-main: #f5f1e7;
    --card-yellow: #deb865;
    --alert-yellow: #eaddb6;
    --text-dark: #2c2c2c;
    --text-light: #ffffff;
}

html, body, [class*="css"] {
    font-family: 'Sarabun', sans-serif;
}

/* ---------- พื้นหลังหลัก (Topographic Map pattern) ---------- */
.stApp {
    background-color: var(--bg-main);
    background-image: url("data:image/svg+xml,%3Csvg width='100' height='100' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M11 18c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm48 25c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm-43-7c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm63 31c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM34 90c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm56-76c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM12 86c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm28-65c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm23-11c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-6 60c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm29 22c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zM32 63c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm57-13c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-9-21c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM60 91c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM35 41c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM12 60c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2z' fill='%23344c33' fill-opacity='0.05' fill-rule='evenodd'/%3E%3C/svg%3E");
    background-attachment: fixed;
}

/* ---------- Header / Hero ---------- */
.hero-container {
    text-align: center;
    padding: 2rem 1rem 1rem 1rem;
    color: var(--text-dark);
}
.hero-container h1 {
    font-family: 'Kanit', sans-serif;
    font-weight: 700;
    font-size: 2.8rem;
    color: var(--text-dark);
    margin-bottom: 0.5rem;
}
.hero-container p {
    font-family: 'Sarabun', sans-serif;
    font-size: 1.1rem;
    color: #555;
    margin-top: 0;
}

/* ---------- การ์ดต้อนรับ (Welcome Card) ---------- */
.welcome-card {
    background-color: var(--card-yellow);
    border-radius: 12px;
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
}
.welcome-header {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
}
.welcome-header img {
    width: 60px;
    height: auto;
}
.welcome-text h3 {
    font-family: 'Kanit', sans-serif;
    margin: 0 0 0.2rem 0;
    font-size: 1.2rem;
    color: var(--text-dark);
}
.welcome-text p {
    margin: 0;
    color: var(--text-dark);
    font-size: 0.95rem;
}
.pill-container {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin-top: 0.5rem;
}
.pill {
    background-color: rgba(255,255,255,0.4);
    border: 1px solid rgba(0,0,0,0.1);
    border-radius: 20px;
    padding: 0.3rem 0.8rem;
    font-size: 0.85rem;
    color: var(--text-dark);
    font-weight: 500;
}

/* ---------- ประกาศสำคัญ (Alert Card) ---------- */
.alert-card {
    background-color: var(--alert-yellow);
    border-radius: 12px;
    padding: 1.2rem;
    margin-bottom: 2rem;
    border-left: 5px solid #dcb556;
}
.alert-card h4 {
    font-family: 'Kanit', sans-serif;
    margin: 0 0 0.3rem 0;
    color: #8c7128;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.alert-card p {
    margin: 0;
    font-size: 0.9rem;
    color: #6a5824;
}

/* ---------- แถบข้าง (Sidebar) ---------- */
[data-testid="stSidebar"] {
    background-color: var(--primary-green) !important;
}
[data-testid="stSidebar"] * {
    color: var(--text-light) !important;
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    font-family: 'Kanit', sans-serif;
}
.sidebar-info-card {
    background-color: var(--bg-main);
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
    color: var(--text-dark) !important;
}
.sidebar-info-card * {
    color: var(--text-dark) !important;
    margin: 0.2rem 0;
    font-size: 0.9rem;
}
.sidebar-info-card b {
    font-family: 'Kanit', sans-serif;
}
div[data-testid="stExpander"] {
    background-color: var(--bg-main);
    border-radius: 8px;
    margin-bottom: 0.5rem;
}
div[data-testid="stExpander"] * {
    color: var(--text-dark) !important;
}

/* ปุ่มใน Sidebar */
.stButton>button {
    background-color: var(--bg-main);
    color: var(--text-dark) !important;
    border: none;
    border-radius: 8px;
    font-family: 'Kanit', sans-serif;
    font-weight: 600;
    transition: all 0.2s;
    width: 100%;
}
.stButton>button:hover {
    background-color: var(--card-yellow);
    color: var(--text-dark) !important;
}

/* ---------- ข้อความแชท ---------- */
[data-testid="stChatMessage"] {
    background: transparent;
    border: none;
}
[data-testid="stChatMessageContent"] {
    background-color: #ffffff;
    border-radius: 12px;
    padding: 1rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    color: var(--text-dark);
}
[data-testid="stChatMessageContent"] p {
    color: var(--text-dark);
}
/* ฝั่งผู้ใช้ */
[data-testid="stChatMessage"]:nth-child(even) [data-testid="stChatMessageContent"] {
    background-color: var(--card-yellow);
}

/* กล่องพิมพ์ข้อความด้านล่าง */
[data-testid="stChatInput"] {
    border-radius: 25px;
    border: 2px solid var(--primary-light);
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ------------------------------------------------------------
# 2. System Instruction (คงเดิม)
# ------------------------------------------------------------

SYSTEM_INSTRUCTION = f"""
คุณคือ "{APP_NAME}" ผู้ช่วยสำหรับนักเดินป่ามือใหม่
ที่ให้ข้อมูลเฉพาะการเดินป่าและการพักค้างคืนที่
"อุทยานแห่งชาติดอยขุนตาล" เท่านั้น

บุคลิกของคุณ: เหมือนพี่ที่เคยเดินดอยขุนตาลมาหลายรอบ ใจดี รอบคอบ
พูดจาเป็นกันเองแบบพี่คุยกับน้อง ให้กำลังใจมือใหม่ แต่ไม่ประมาทเรื่องความปลอดภัย

กฎสำคัญ:

1. ขอบเขตสถานที่
- ตอบเฉพาะเรื่องดอยขุนตาล
- ครอบคลุมเส้นทาง สถานีรถไฟขุนตาน ที่ทำการอุทยาน
  Y1, Y2, Y3, Y4 การพักค้างคืน อุปกรณ์ น้ำ อาหาร
  การเตรียมร่างกาย ความปลอดภัย และการเดินทางที่เกี่ยวข้องกับทริปดอยขุนตาล
- ถ้าผู้ใช้ถามสถานที่เดินป่าอื่น เช่น ภูกระดึง เขาหลวงสุโขทัย
  ดอยหลวงเชียงดาว ฯลฯ ให้แจ้งอย่างสุภาพว่า
  ระบบนี้รองรับเฉพาะดอยขุนตาล และเสนอช่วยเรื่องดอยขุนตาลแทน
- ห้ามเปรียบเทียบหรือให้ข้อมูลรายละเอียดของสถานที่อื่น

2. กลุ่มผู้ใช้
- ถือว่าผู้ใช้เป็นมือใหม่ เว้นแต่ผู้ใช้ระบุว่ามีประสบการณ์
- อธิบายเป็นภาษาไทยง่าย ๆ เป็นกันเอง
- ให้ความสำคัญกับความปลอดภัยมากกว่าความเร็วหรือการพิชิตยอด
- ไม่กดดันให้ผู้ใช้ซื้ออุปกรณ์ราคาแพงหรือของที่ไม่จำเป็น

3. การใช้ Knowledge Base
- ใช้ "ข้อมูลจาก Knowledge Base" ที่ส่งมาในแต่ละคำถามเป็นแหล่งข้อมูลหลัก
- ห้ามสร้างระยะทาง จุดพัก สิ่งอำนวยความสะดวก กฎ หรือบริการขึ้นเอง
- ถ้า Knowledge Base ไม่มีข้อมูลเพียงพอ ให้บอกตรง ๆ ว่า
  "ข้อมูลส่วนนี้ยังไม่มีในฐานความรู้ดอยขุนตาล"
- สามารถอธิบายข้อมูลใน Knowledge Base ให้เข้าใจง่ายขึ้นได้
  แต่ห้ามเปลี่ยนข้อเท็จจริงของข้อมูล

4. ข้อมูลที่เปลี่ยนแปลงตามเวลา
ข้อมูลต่อไปนี้ห้ามฟันธงจากความจำของโมเดล:
- วันเปิดหรือปิดอุทยาน
- สถานะเปิดพัก Y2
- สถานะเส้นทาง Y3/Y4
- ค่าธรรมเนียม
- ค่าเช่าเต็นท์
- ราคาที่พัก
- ตารางรถไฟ
- เวลารถไฟ
- สภาพอากาศ
- พยากรณ์ฝน
- เวลาพระอาทิตย์ขึ้น
- ร้านค้าที่เปิดให้บริการ
- จุดเติมน้ำที่ใช้งานได้ในวันนั้น

หากผู้ใช้ถามข้อมูลเหล่านี้:
- ใช้ข้อมูลใน Knowledge Base เพื่ออธิบายวิธีตรวจสอบหรือแนวทางวางแผน
- ย้ำว่าต้องตรวจสอบข้อมูลล่าสุดจากอุทยานแห่งชาติดอยขุนตาล
  กรมอุทยานแห่งชาติ หรือการรถไฟแห่งประเทศไทยตามประเภทข้อมูล
- ห้ามเดาตัวเลขหรือสถานะปัจจุบันขึ้นเอง

5. Checklist
ถ้าผู้ใช้ขอ Checklist:
- จัดหมวดให้เหมาะกับดอยขุนตาล
- แยกได้ เช่น
  "ของที่ต้องพกติดตัวระหว่างเดิน"
  "ของสำหรับพักที่ Y2"
  "ของสำหรับขึ้น Y4 เช้ามืด"
  "ของสำรอง/ฉุกเฉิน"
- ห้ามแนะนำหมวด "ของฝากลูกหาบ"
  เพราะระบบนี้ไม่มีข้อมูลยืนยันบริการลูกหาบสำหรับทริปดอยขุนตาล

6. Y2 และ Y4
- หากพูดถึงการพัก Y2 ต้องเตือนให้ตรวจสอบสถานะการเปิดพักล่าสุด
- หากพูดถึงการขึ้น Y4 เช้ามืด ให้เน้นไฟฉายคาดหัว
  การเดินกับเพื่อน การเดินตามเส้นทาง และการประเมินสภาพอากาศ
- หากสภาพอากาศหรือเจ้าหน้าที่ไม่แนะนำให้ขึ้น ต้องให้ความปลอดภัยมาก่อน

7. ชื่อสถานที่
- "ดอยขุนตาล" คือชื่ออุทยาน/ดอย
- "สถานีรถไฟขุนตาน" ใช้ น สะกดท้าย
- อย่าสลับการสะกดสองชื่อนี้

8. รูปแบบคำตอบ
- ตอบตรงคำถามก่อน
- ใช้หัวข้อและ bullet เมื่อช่วยให้อ่านง่าย
- ไม่ต้องใส่ข้อมูลทุกอย่างจาก KB หากผู้ใช้ถามเพียงเรื่องเดียว
- หากผู้ใช้เป็นมือใหม่ ให้บอกข้อควรระวังที่สำคัญต่อคำถามนั้น
- ถ้าคำถามกำกวม ให้ถามเพิ่มเฉพาะเมื่อจำเป็นจริง ๆ

จงตอบโดยยึดข้อมูลดอยขุนตาลที่ให้มาใน Context ด้านล่าง
และอย่าอ้างว่าคุณตรวจสอบข้อมูลสดจากอินเทอร์เน็ต เพราะแอปนี้ไม่มีระบบค้นเว็บสด
"""

# ------------------------------------------------------------
# 3. ฟังก์ชันแบ่ง Markdown เป็น Chunk (คงเดิม)
# ------------------------------------------------------------


def split_markdown_into_chunks(text: str, max_chars: int = 2600):
    text = text.strip()
    if not text:
        return []
    sections = re.split(r"(?=^##\s+)", text, flags=re.MULTILINE)
    chunks = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        if len(section) <= max_chars:
            chunks.append(section)
            continue
        paragraphs = [p.strip()
                      for p in re.split(r"\n\s*\n", section) if p.strip()]
        current = ""
        for paragraph in paragraphs:
            candidate = paragraph if not current else current + "\n\n" + paragraph
            if len(candidate) <= max_chars:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                if len(paragraph) > max_chars:
                    for start in range(0, len(paragraph), max_chars):
                        piece = paragraph[start:start + max_chars].strip()
                        if piece:
                            chunks.append(piece)
                    current = ""
                else:
                    current = paragraph
        if current:
            chunks.append(current)
    return chunks


# ------------------------------------------------------------
# 4. โหลด RAG System (คงเดิม)
# ------------------------------------------------------------

@st.cache_resource(show_spinner="กำลังโหลดฐานความรู้ดอยขุนตาล...")
def load_rag_system():
    if not KB_PATH.exists():
        raise FileNotFoundError(f"ไม่พบไฟล์ Knowledge Base: {KB_PATH.name}")
    text = KB_PATH.read_text(encoding="utf-8")
    chunks = split_markdown_into_chunks(text)
    if not chunks:
        raise ValueError(
            "ไฟล์ Knowledge Base ว่าง หรือไม่สามารถสร้าง chunk ได้")
    model = SentenceTransformer(
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    embeddings = model.encode(
        chunks, normalize_embeddings=True, show_progress_bar=False)
    embeddings = np.asarray(embeddings, dtype="float32")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)
    return chunks, model, index


try:
    chunks, embedder, index = load_rag_system()
except Exception as e:
    st.error(f"⚠️ โหลด Knowledge Base ไม่สำเร็จ: {e}")
    st.stop()


# ------------------------------------------------------------
# 5. เชื่อมต่อ Gemini (คงเดิม)
# ------------------------------------------------------------

api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
if not api_key:
    st.error(
        "⚠️ ไม่พบ API Key กรุณาเพิ่ม GOOGLE_API_KEY หรือ GEMINI_API_KEY ในไฟล์ .env")
    st.stop()

client = genai.Client(api_key=api_key)
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")


# ------------------------------------------------------------
# 6. Retrieval Functions (คงเดิม)
# ------------------------------------------------------------

def retrieve_context(question: str, top_k: int = 6):
    if not question.strip():
        return [], []
    query_embedding = embedder.encode(
        [question], normalize_embeddings=True, show_progress_bar=False)
    query_embedding = np.asarray(query_embedding, dtype="float32")
    k = min(top_k, len(chunks))
    scores, indices = index.search(query_embedding, k)
    retrieved_chunks = []
    retrieved_scores = []
    for idx, score in zip(indices[0], scores[0]):
        if 0 <= idx < len(chunks):
            retrieved_chunks.append(chunks[idx])
            retrieved_scores.append(float(score))
    return retrieved_chunks, retrieved_scores


def get_recent_conversation(max_messages: int = 6):
    history = st.session_state.get("messages", [])
    if not history:
        return "ไม่มีประวัติการสนทนาก่อนหน้า"
    recent = history[-max_messages:]
    lines = []
    for message in recent:
        role = message.get("role")
        speaker = "ผู้ใช้" if role == "user" else "ผู้ช่วย" if role == "assistant" else None
        if not speaker:
            continue
        content = message.get("content", "").strip()
        if content:
            lines.append(f"{speaker}: {content[:1500]}")
    return "\n".join(lines) if lines else "ไม่มีประวัติการสนทนาก่อนหน้า"


def build_user_message(question: str, retrieved_chunks: list[str]):
    context = "\n\n---\n\n".join(retrieved_chunks)
    conversation = get_recent_conversation()
    return f"""
ต่อไปนี้คือข้อมูลที่ค้นคืนมาจาก Knowledge Base ดอยขุนตาล:

<knowledge_base>
{context}
</knowledge_base>

บริบทการสนทนาล่าสุด:
<conversation_history>
{conversation}
</conversation_history>

คำถามปัจจุบันของผู้ใช้:
<user_question>
{question}
</user_question>

จากข้อมูลข้างต้น โปรดตอบคำถามปัจจุบันโดยปฏิบัติตาม System Instruction
"""


# ------------------------------------------------------------
# 7. Session State
# ------------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []


# ------------------------------------------------------------
# 8. Sidebar (ดีไซน์ใหม่)
# ------------------------------------------------------------

with st.sidebar:
    st.markdown("<h3>🧭 เนเจอร์นู้บไกด์ ⛰️</h3>", unsafe_allow_html=True)

    # การ์ดข้อมูลทั่วไป
    st.markdown(
        """
        <div class="sidebar-info-card">
            <b>ข้อมูลทั่วไป</b><br>
            สถานที่: ดอยขุนตาล<br>
            เหมาะสำหรับ: ผู้เริ่มต้น (มือใหม่มากๆ)<br>
            ฐานความรู้: <code>trekking_gear_kb.md</code>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<b>คำแนะนำตามเส้นทาง</b>", unsafe_allow_html=True)
    with st.expander("⛰️ Y1-Y4"):
        st.write("ภาพรวมเส้นทางตั้งแต่เริ่มจนถึงยอด")
    with st.expander("🚶‍♂️ Y1: เดินยังไงให้ไม่เหนื่อย?"):
        st.write("เทคนิคการเดินป่าช่วงเริ่มต้น")
    with st.expander("📸 Y3: แวะถ่ายรูปตรงไหนดี?"):
        st.write("จุดเช็คอินที่ไม่ควรพลาด")
    with st.expander("🏕️ Y4: เช้ามาต้องเตรียมอะไรบ้าง?"):
        st.write("การเตรียมตัวดูพระอาทิตย์ขึ้น")

    st.markdown("<b>เตรียมตัวและอุปกรณ์</b>", unsafe_allow_html=True)
    with st.expander("🎒 ต้องเตรียมของอะไรบ้าง?"):
        st.write("เช็คลิสต์อุปกรณ์สำหรับมือใหม่")
    with st.expander("💧 ควรเตรียมน้ำอาหารอย่างไร?"):
        st.write("การคำนวณเสบียงและน้ำดื่ม")

    st.write("")  # Spacer

    if st.button("🗑️ ล้างประวัติแชท"):
        st.session_state.messages = []
        st.rerun()

    if st.button("📄 PDF (Coming Soon)"):
        pass


# ------------------------------------------------------------
# 9. Header & ข้อความต้อนรับ (ดีไซน์ใหม่)
# ------------------------------------------------------------

st.markdown(
    f"""
    <div class="hero-container">
        <h1>🏕️ {APP_NAME} 🎒</h1>
        <p>{APP_TAGLINE}</p>
    </div>
    """,
    unsafe_allow_html=True
)

if not st.session_state.messages:
    # แสดงการ์ดต้อนรับและประกาศเฉพาะตอนเริ่มแชท
    st.markdown(
        """
        <div class="welcome-card">
            <div class="welcome-header">
                <div style="font-size: 3rem;">🤖</div>
                <div class="welcome-text">
                    <h3>สวัสดีครับเพื่อนใหม่! ให้ Nature Noob ช่วยก้าวแรกสู่ดอยขุนตาลของคุณ</h3>
                    <p>ไม่ต้องกลัวหลง หรือไม่พร้อม เรามีคำตอบ!</p>
                    <div class="pill-container">
                        <span class="pill">Y1: เดินยังไงให้ไม่เหนื่อย?</span>
                        <span class="pill">Y1 เหนื่อยไหม?</span>
                        <span class="pill">อาหารแนะนำตรงไหนดี?</span>
                        <span class="pill">Y4: เช้ามาต้องเตรียมอะไรบ้าง?</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="alert-card">
            <h4>⚠️ ประกาศสำคัญ</h4>
            <p>เปลี่ยนแปลงสภาพอากาศ โปรดเช็คการเตรียมพร้อม อุณหภูมิ น้ำ และอุปกรณ์กันฝนก่อนเดินทางเสมอ ข้อมูลเปิด-ปิด ราคา รถไฟ น้ำ อาจเปลี่ยนได้ ต้องตรวจสอบล่าสุดก่อนเดินทาง</p>
        </div>
        """,
        unsafe_allow_html=True
    )


# ------------------------------------------------------------
# 10. แสดงประวัติแชท (คงเดิม)
# ------------------------------------------------------------

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ------------------------------------------------------------
# 11. Chat Input -> Retrieve -> Generate (คงเดิม)
# ------------------------------------------------------------

prompt = st.chat_input("ถามเรื่องเดินป่าดอยขุนตาล")

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)

    retrieved_chunks, scores = retrieve_context(prompt, top_k=6)
    user_message = build_user_message(prompt, retrieved_chunks)

    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("กำลังค้นข้อมูลดอยขุนตาล..."):
            try:
                response = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=user_message,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                    ),
                )
                answer = response.text.strip(
                ) if response.text else "ขออภัยครับ ระบบไม่ได้รับข้อความตอบกลับจาก AI"
                st.markdown(answer)
                st.session_state.messages.append(
                    {"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาดในการเชื่อมต่อ Gemini\n\n`{e}`")
