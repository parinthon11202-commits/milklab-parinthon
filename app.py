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
APP_TAGLINE = " คู่มือเฉพาะทางสำหรับมือใหม่"


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

CUSTOM_CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Kanit:wght@400;500;600;700&family=Sarabun:wght@400;500;600;700&display=swap');

:root{
  --forest:#214628;
  --forest-2:#315f36;
  --paper:#f5ecda;
  --paper-2:#fffaf0;
  --ink:#2f1b12;
  --muted:#6f6257;
  --gold:#f4b93f;
  --gold-2:#ffd46e;
  --line:#cbbfa7;
}

html, body, [class*="css"]{font-family:'Sarabun',sans-serif;}

/* ---------------- App background ---------------- */
.stApp{
  isolation:isolate;
  background-color:var(--paper);
  background-image:
    url("data:image/svg+xml,%3Csvg width='260' height='260' viewBox='0 0 260 260' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' stroke='%2388755b' stroke-opacity='.10' stroke-width='1'%3E%3Cpath d='M-10 38C38 2 58 61 109 35s64-9 101 17 70-16 86-42'/%3E%3Cpath d='M-20 64C28 28 53 80 102 58s61-9 96 14 66-10 92-35'/%3E%3Cpath d='M-12 98c43-29 78 17 115-9s68-6 102 18 61 1 78-26'/%3E%3Cpath d='M-18 130c39-29 75 15 110-10s67-7 103 16 63 4 90-24'/%3E%3Cpath d='M-5 166c33-24 69 14 103-11s62-3 95 20 59 2 86-20'/%3E%3Cpath d='M-14 205c44-33 72 11 113-13s68-2 102 20 64 0 90-30'/%3E%3Cpath d='M-10 238c42-30 73 14 111-10s65-5 99 17 62 0 88-24'/%3E%3C/g%3E%3C/svg%3E");
  background-attachment:fixed;
  position:relative;
}
.stApp::before{
  content:"";
  position:fixed;
  inset:0 0 0 auto;
  width:50vw;
  background-image:
    linear-gradient(90deg, rgba(245,236,218,1) 0%, rgba(245,236,218,.82) 20%, rgba(245,236,218,.24) 55%, rgba(245,236,218,.03) 100%),
    linear-gradient(180deg, rgba(255,210,164,.28), rgba(28,63,37,.18)),
    url('https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1800&q=88');
  background-size:cover;
  background-position:center;
  pointer-events:none;
  z-index:0;
}
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > .main{
  background:transparent!important;
}
.stApp > *{
  position:relative;
  z-index:1;
}
[data-testid="stAppViewContainer"]{
  position:relative;
  z-index:1;
}

/* hide default decorations */
#MainMenu{visibility:hidden;}
footer{visibility:hidden;}
header[data-testid="stHeader"]{background:transparent!important;}
[data-testid="stToolbar"]{right:1rem;}

/* main content sizing */
.block-container{
  max-width:1080px;
  padding-top:1.3rem;
  padding-bottom:7rem;
}

/* ---------------- Sidebar ---------------- */
[data-testid="stSidebar"]{
  width:320px!important;
  min-width:320px!important;
  background:
    linear-gradient(rgba(26,63,31,.96),rgba(34,76,39,.97)),
    repeating-linear-gradient(90deg,rgba(255,255,255,.025) 0 1px,transparent 1px 5px)!important;
  border-right:1px solid rgba(0,0,0,.18);
}
[data-testid="stSidebar"] > div:first-child{width:320px!important;}
[data-testid="stSidebar"] .block-container{padding:1.1rem .85rem 1rem .85rem;}
[data-testid="stSidebar"] *{font-family:'Sarabun',sans-serif;}

.sidebar-brand{
  font-family:'Kanit',sans-serif;
  font-size:1.64rem;
  font-weight:700;
  color:white;
  margin:.15rem 0 .85rem;
  text-shadow:0 1px 1px rgba(0,0,0,.25);
}
.sidebar-section-title{
  font-family:'Kanit',sans-serif;
  color:#fff;
  font-size:1.22rem;
  font-weight:700;
  margin:1rem 0 .35rem;
}
.sidebar-info-card{
  background:rgba(255,250,239,.96);
  color:#30271f!important;
  border:1px solid rgba(70,55,35,.22);
  border-radius:12px;
  padding:.72rem;
  display:grid;
  grid-template-columns:86px 1fr;
  gap:.62rem;
  box-shadow:0 4px 12px rgba(0,0,0,.10);
}
.sidebar-thumb{
  width:86px;height:100px;border-radius:7px;object-fit:cover;
  box-shadow:inset 0 0 0 1px rgba(0,0,0,.08);
}
.sidebar-info-card h4{
  font-family:'Kanit',sans-serif;margin:0 0 .15rem;font-size:1.05rem;color:#2d261f!important;
}
.sidebar-info-card p{margin:.12rem 0;line-height:1.38;font-size:.88rem;color:#2d261f!important;}
.sidebar-kb{
  grid-column:1/-1;margin-top:.1rem!important;padding-top:.32rem;border-top:1px solid rgba(0,0,0,.08);
}

/* expanders look like cream navigation rows */
[data-testid="stSidebar"] details{
  background:#faf3e5!important;
  border:1px solid rgba(39,57,38,.28)!important;
  border-radius:8px!important;
  margin:.2rem 0!important;
  overflow:hidden;
}
[data-testid="stSidebar"] details summary{
  padding:.28rem .45rem!important;
  min-height:42px!important;
}
[data-testid="stSidebar"] details summary p{
  color:#26231f!important;font-size:.92rem!important;font-weight:600!important;
}
[data-testid="stSidebar"] details [data-testid="stExpanderDetails"]{
  color:#393129!important;background:#fffaf0!important;padding:.2rem .65rem .7rem!important;
}
[data-testid="stSidebar"] details [data-testid="stExpanderDetails"] *{color:#393129!important;}

/* Sidebar buttons */
[data-testid="stSidebar"] .stButton > button{
  width:100%;
  border-radius:8px;
  min-height:42px;
  font-family:'Kanit',sans-serif;
  font-size:.95rem;
  font-weight:600;
  background:#fff!important;
  color:#29251f!important;
  border:1px solid rgba(255,255,255,.55)!important;
  box-shadow:none!important;
}
[data-testid="stSidebar"] .stButton > button:hover{background:#f5e4bd!important;border-color:#f5c869!important;}
[data-testid="stSidebar"] .pdf-btn + div button{}

/* ---------------- Sidebar important notice ---------------- */
.sidebar-alert-card{
  margin-top:.75rem;
  padding:.78rem .82rem;
  background:rgba(255,246,211,.97);
  border:1px solid rgba(177,145,63,.28);
  border-radius:11px;
  box-shadow:0 3px 10px rgba(0,0,0,.08);
  color:#4d391f!important;
}

.sidebar-alert-title{
  display:flex;
  align-items:center;
  gap:.45rem;
  font-family:'Kanit',sans-serif;
  font-size:.98rem;
  font-weight:700;
  color:#5c3b17!important;
  margin:0 0 .3rem;
}

.sidebar-alert-card p{
  margin:0!important;
  font-size:.82rem!important;
  line-height:1.45!important;
  color:#5e4d3b!important;
}

/* ---------------- Hero ---------------- */
.hero-container{text-align:center;padding:.4rem 1rem .9rem;color:var(--ink);}
.hero-container h1{
  font-family:'Kanit',sans-serif;
  font-size:2.72rem;
  line-height:1.05;
  font-weight:700;
  margin:.35rem 0 .45rem;
  color:#32170b;
  letter-spacing:-.02em;
}
.hero-container p{margin:0;font-size:1.05rem;color:#493c32;font-weight:500;}

/* ---------------- Welcome card ---------------- */
.welcome-card{
  background:linear-gradient(135deg,#f6bd43 0%,#f7c95b 55%,#f6b738 100%);
  border:1px solid rgba(128,85,18,.18);
  border-radius:10px;
  padding:1rem 1.1rem;
  margin:0 0 .82rem;
  box-shadow:0 5px 14px rgba(106,74,25,.18);
}
.welcome-grid{display:grid;grid-template-columns:125px 1fr;gap:1rem;align-items:center;}
.robot-wrap{display:flex;align-items:center;justify-content:center;}
.robot-svg{width:112px;height:112px;filter:drop-shadow(0 4px 2px rgba(77,44,18,.18));}
.welcome-copy h3{
  font-family:'Kanit',sans-serif;
  color:#44240f;
  font-size:1.06rem;
  margin:0 0 .22rem;
  font-weight:700;
}
.welcome-copy p{color:#4c2d16;margin:0 0 .65rem;font-size:.94rem;line-height:1.46;}
.pills{display:flex;flex-wrap:wrap;gap:.45rem;}
.pill{
  background:rgba(255,249,226,.72);
  border:1px solid rgba(122,82,19,.22);
  padding:.33rem .72rem;
  border-radius:999px;
  color:#5b3d1f;
  font-size:.84rem;
  font-weight:600;
  box-shadow:inset 0 1px rgba(255,255,255,.45);
}

/* ---------------- Alert ---------------- */
.alert-card{
  display:grid;grid-template-columns:38px 1fr;gap:.55rem;align-items:start;
  background:rgba(255,246,211,.94);
  border:1px solid rgba(177,145,63,.22);
  border-radius:10px;
  padding:.82rem 1rem;
  margin:0 0 .95rem;
  box-shadow:0 4px 12px rgba(90,69,30,.10);
}
.alert-icon{font-size:1.45rem;line-height:1.2;}
.alert-card h4{font-family:'Kanit',sans-serif;margin:0;color:#5c3b17;font-size:1rem;font-weight:700;}
.alert-card p{margin:.12rem 0 0;color:#5e4d3b;font-size:.86rem;line-height:1.45;}

/* ---------------- Chat ---------------- */
[data-testid="stChatMessage"]{background:transparent;border:none;}
[data-testid="stChatMessageContent"]{
  background:rgba(255,255,255,.95);
  border:1px solid rgba(76,62,47,.10);
  border-radius:13px;
  box-shadow:0 3px 10px rgba(58,45,32,.08);
  color:#2c2722;
  padding:.8rem 1rem;
}
[data-testid="stChatInput"]{
  background:rgba(255,255,255,.96)!important;
  border:1px solid rgba(92,79,62,.18)!important;
  border-radius:13px!important;
  box-shadow:0 8px 24px rgba(48,37,25,.14)!important;
}
[data-testid="stChatInput"] textarea{min-height:62px!important;font-size:.95rem!important;}

/* quick actions under chat */
.quick-title{height:0;margin:0;padding:0;}
div[data-testid="stHorizontalBlock"] .stButton > button{
  border-radius:999px!important;
  min-height:34px!important;
  padding:.2rem .72rem!important;
  background:rgba(255,248,231,.72)!important;
  color:#493828!important;
  border:1px solid rgba(98,78,55,.16)!important;
  font-weight:600!important;
  box-shadow:none!important;
  white-space:nowrap;
}
div[data-testid="stHorizontalBlock"] .stButton > button:hover{background:#f7d58d!important;border-color:#d7aa50!important;}

@media (max-width:900px){
  [data-testid="stSidebar"]{width:290px!important;min-width:290px!important;}
  [data-testid="stSidebar"] > div:first-child{width:290px!important;}
  .hero-container h1{font-size:2rem;}
  .welcome-grid{grid-template-columns:82px 1fr;}
  .robot-svg{width:78px;height:78px;}
  .stApp::before{width:66vw;opacity:.7;}
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


# สำคัญ:
# อย่าโหลด SentenceTransformer / FAISS ตรงนี้
# เพราะถ้ามีปัญหาหรือกำลังดาวน์โหลดโมเดล หน้า UI จะยังไม่ถูกวาด
# เราจะโหลด RAG แบบ lazy ตอนผู้ใช้ส่งคำถามครั้งแรกแทน


# ------------------------------------------------------------
# 5. เชื่อมต่อ Gemini
# ------------------------------------------------------------

api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")

# ไม่ใช้ st.stop() ตรงนี้ เพื่อให้ UI แสดงได้แม้ยังไม่ได้ตั้ง API key
client = genai.Client(api_key=api_key) if api_key else None
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")


# ------------------------------------------------------------
# 6. Retrieval Functions (คงเดิม)
# ------------------------------------------------------------

def retrieve_context(question: str, top_k: int = 6):
    if not question.strip():
        return [], []

    # โหลดโมเดลและ FAISS เมื่อมีคำถามครั้งแรกเท่านั้น
    # @st.cache_resource ทำให้ครั้งต่อไปไม่ต้องโหลดใหม่
    chunks, embedder, index = load_rag_system()

    query_embedding = embedder.encode(
        [question],
        normalize_embeddings=True,
        show_progress_bar=False,
    )
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
# 8. Sidebar — UI ตามภาพตัวอย่าง
# ------------------------------------------------------------

with st.sidebar:
    st.markdown(
        '<div class="sidebar-brand"></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="sidebar-info-card">
          <img class="sidebar-thumb"
              src="https://raw.githubusercontent.com/parinthon11202-commits/milklab-parinthon/release/demo-day/assets/khun_tan.jpg"
               alt="ดอยขุนตาล">
          <div>
            <h4>ข้อมูลทั่วไป</h4>
            <p><b>สถานที่:</b> ดอยขุนตาล</p>
            <p><b>เหมาะสำหรับ:</b> ผู้เริ่มต้นที่สนใจจะเดินป่า<br></p>
          </div>
          <p class="sidebar-kb"><b>ฐานความรู้:</b> ไม่มี</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ประกาศสำคัญ — แสดงในพื้นที่สีเขียวของ Sidebar
    st.markdown(
        """
        <div class="sidebar-alert-card">
          <div class="sidebar-alert-title">
            <span>⚠️</span>
            <span>ประกาศสำคัญ</span>
          </div>
          <p>กรุณาตรวจสอบข้อมูลล่าสุดก่อนเดินทางเสมอ</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------
# 9. Header + Welcome Card
# ------------------------------------------------------------

st.markdown(
    f"""
    <div class="hero-container">
      <h1>🏕️ {APP_NAME} 🎒</h1>
      <p>{APP_TAGLINE}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if not st.session_state.messages:
    st.markdown(
        r"""
        <div class="welcome-card">
          <div class="welcome-grid">
            <div class="robot-wrap">
              <svg class="robot-svg" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg" aria-label="Nature Noob robot">
                <ellipse cx="60" cy="108" rx="31" ry="6" fill="#9b6b2d" opacity=".18"/>
                <rect x="27" y="39" width="66" height="46" rx="18" fill="#bdd7d6" stroke="#49311e" stroke-width="3"/>
                <rect x="35" y="48" width="50" height="27" rx="11" fill="#9ccbd0" stroke="#49311e" stroke-width="2"/>
                <circle cx="50" cy="60" r="3.2" fill="#2d2b26"/><circle cx="70" cy="60" r="3.2" fill="#2d2b26"/>
                <path d="M52 68 Q60 73 68 68" fill="none" stroke="#2d2b26" stroke-width="2" stroke-linecap="round"/>
                <path d="M60 38v-9" stroke="#49311e" stroke-width="3" stroke-linecap="round"/>
                <circle cx="60" cy="25" r="4" fill="#f0b243" stroke="#49311e" stroke-width="2"/>
                <rect x="38" y="84" width="44" height="21" rx="8" fill="#73979a" stroke="#49311e" stroke-width="3"/>
                <rect x="50" y="89" width="20" height="11" rx="2" fill="#e8d69f" stroke="#49311e" stroke-width="2"/>
                <path d="M34 77 20 92M86 76 103 61" stroke="#49311e" stroke-width="5" stroke-linecap="round"/>
                <path d="M103 61 108 54M103 61 111 62" stroke="#49311e" stroke-width="3" stroke-linecap="round"/>
                <path d="M47 105 42 114M73 105 79 114" stroke="#49311e" stroke-width="5" stroke-linecap="round"/>
                <rect x="17" y="66" width="12" height="27" rx="5" fill="#cc8a3a" stroke="#49311e" stroke-width="2"/>
                <path d="M26 68 19 60" stroke="#49311e" stroke-width="3"/>
                <rect x="70" y="8" width="43" height="21" rx="10" fill="#fff7df" stroke="#49311e" stroke-width="2"/>
                <text x="91.5" y="22" text-anchor="middle" font-size="8" font-family="sans-serif" fill="#49311e">พร้อมลุย!</text>
              </svg>
            </div>
            <div class="welcome-copy">
              <h3>สวัสดีครับเพื่อนใหม่! ให้ Nature Noob ช่วยวางแผนทริปดอยขุนตาลของคุณ</h3>
              <p>ไม่ต้องกลัวหลง หรือไม่พร้อม เรามีคำตอบ!</p>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------
# 10. แสดงประวัติแชท
# ------------------------------------------------------------

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ปุ่มคำถามด่วนแบบในภาพ
quick_cols = st.columns([1.2, 1, 1, 4.6], gap="small")
if quick_cols[0].button("เตรียมอุปกรณ์ยังไง?", key="q_gear"):
    st.session_state.queued_prompt = "มือใหม่ไปดอยขุนตาลควรเตรียมอุปกรณ์อะไรบ้าง?"
    st.rerun()
if quick_cols[1].button("Y1 เหนื่อยไหม?", key="q_y1"):
    st.session_state.queued_prompt = "Y1 เหนื่อยไหม สำหรับมือใหม่ควรเดินอย่างไร?"
    st.rerun()
if quick_cols[2].button("อาหารแนะนำ?", key="q_food"):
    st.session_state.queued_prompt = "ควรเตรียมน้ำและอาหารสำหรับทริปดอยขุนตาลอย่างไร?"
    st.rerun()


# ------------------------------------------------------------
# 11. Chat Input -> Retrieve -> Generate
# ------------------------------------------------------------

queued_prompt = st.session_state.pop("queued_prompt", None)
typed_prompt = st.chat_input("ถามเรื่องเดินป่าดอยขุนตาล...")
prompt = queued_prompt or typed_prompt

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        if client is None:
            st.error(
                "⚠️ ยังไม่พบ GOOGLE_API_KEY หรือ GEMINI_API_KEY ในไฟล์ .env "
                "หน้า UI ใช้งานได้แล้ว แต่ต้องตั้ง API key ก่อนจึงจะให้ AI ตอบได้"
            )
        else:
            try:
                with st.spinner("กำลังโหลด/ค้นฐานความรู้ดอยขุนตาล..."):
                    retrieved_chunks, scores = retrieve_context(
                        prompt, top_k=6)

                user_message = build_user_message(prompt, retrieved_chunks)

                with st.spinner("กำลังคิดคำตอบ..."):
                    response = client.models.generate_content(
                        model=GEMINI_MODEL,
                        contents=user_message,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_INSTRUCTION,
                        ),
                    )

                answer = (
                    response.text.strip()
                    if response.text
                    else "ขออภัยครับ ระบบไม่ได้รับข้อความตอบกลับจาก AI"
                )

                st.markdown(answer)
                st.session_state.messages.append(
                    {"role": "assistant", "content": answer}
                )

            except FileNotFoundError as e:
                st.error(f"⚠️ ไม่พบ Knowledge Base: {e}")

            except Exception as e:
                st.error(f"เกิดข้อผิดพลาดระหว่างประมวลผล\n\n`{e}`")
