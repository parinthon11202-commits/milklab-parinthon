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
# Trekking & Camping Buddy
# Beginner Hiking Chatbot - DOI KHUN TAN ONLY
# ============================================================
#
# ขอบเขตของระบบ:
# - ผู้ใช้งานเป้าหมาย: นักเดินป่ามือใหม่
# - สถานที่: อุทยานแห่งชาติดอยขุนตาลเท่านั้น
# - Knowledge Base: trekking_gear_kb.md
# - AI: Gemini
# - Retrieval: Sentence Transformers + FAISS
#
# Environment Variable:
# - GOOGLE_API_KEY หรือ GEMINI_API_KEY
#
# หมายเหตุ:
# ข้อมูลที่เปลี่ยนตามเวลา เช่น
# - สถานะเปิด/ปิดอุทยาน
# - สถานะ Y2 / Y4
# - ราคา
# - ตารางรถไฟ
# - พยากรณ์อากาศ
# ต้องตรวจสอบล่าสุดจากแหล่งทางการ
# ระบบนี้จะไม่เดาข้อมูลดังกล่าวขึ้นเอง
# ============================================================


# ------------------------------------------------------------
# 0. Path และ Environment
# ------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
KB_PATH = BASE_DIR / "trekking_gear_kb.md"

load_dotenv(BASE_DIR / ".env", override=True)


# ------------------------------------------------------------
# 1. ตั้งค่าหน้าเว็บ
# ------------------------------------------------------------

st.set_page_config(
    page_title="Trekking & Camping Buddy | ดอยขุนตาล",
    page_icon="🏕️",
    layout="centered",
)

st.title("🏕️ Trekking & Camping Buddy")
st.caption(
    "ผู้ช่วยสำหรับนักเดินป่ามือใหม่ — ให้ข้อมูลเฉพาะการเดินป่าและค้างคืนที่ดอยขุนตาล"
)


# ------------------------------------------------------------
# 2. System Instruction
# ------------------------------------------------------------

SYSTEM_INSTRUCTION = """
คุณคือ "Trekking & Camping Buddy" ผู้ช่วยสำหรับนักเดินป่ามือใหม่
ที่ให้ข้อมูลเฉพาะการเดินป่าและการพักค้างคืนที่
"อุทยานแห่งชาติดอยขุนตาล" เท่านั้น

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
# 3. ฟังก์ชันแบ่ง Markdown เป็น Chunk
# ------------------------------------------------------------

def split_markdown_into_chunks(text: str, max_chars: int = 2600):
    """
    แบ่ง KB โดยพยายามเก็บหัวข้อ ## ไว้กับเนื้อหา
    ดีกว่าการ split ด้วยบรรทัดว่างเพียงอย่างเดียว
    """

    text = text.strip()

    if not text:
        return []

    # แยกก่อนทุกหัวข้อระดับ ## แต่ไม่ตัด ### ออกจาก ## โดยไม่จำเป็น
    sections = re.split(r"(?=^##\s+)", text, flags=re.MULTILINE)

    chunks = []

    for section in sections:
        section = section.strip()

        if not section:
            continue

        # ถ้าส่วนไม่ยาวเกินไป ให้เก็บเป็น chunk เดียว
        if len(section) <= max_chars:
            chunks.append(section)
            continue

        # ถ้ายาวมาก ค่อยแบ่งตามย่อหน้า
        paragraphs = [
            p.strip()
            for p in re.split(r"\n\s*\n", section)
            if p.strip()
        ]

        current = ""

        for paragraph in paragraphs:
            candidate = (
                paragraph
                if not current
                else current + "\n\n" + paragraph
            )

            if len(candidate) <= max_chars:
                current = candidate
            else:
                if current:
                    chunks.append(current)

                # กรณีย่อหน้าเดียวก็ยาวเกิน max_chars
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
# 4. โหลด RAG System
# ------------------------------------------------------------

@st.cache_resource(show_spinner="กำลังโหลดฐานความรู้ดอยขุนตาล...")
def load_rag_system():
    if not KB_PATH.exists():
        raise FileNotFoundError(
            f"ไม่พบไฟล์ Knowledge Base: {KB_PATH.name}"
        )

    text = KB_PATH.read_text(encoding="utf-8")

    chunks = split_markdown_into_chunks(text)

    if not chunks:
        raise ValueError("ไฟล์ Knowledge Base ว่าง หรือไม่สามารถสร้าง chunk ได้")

    # Multilingual model รองรับภาษาไทย
    model = SentenceTransformer(
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

    # normalize_embeddings=True เพื่อใช้ cosine similarity ผ่าน inner product
    embeddings = model.encode(
        chunks,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    embeddings = np.asarray(embeddings, dtype="float32")

    dimension = embeddings.shape[1]

    # เมื่อ normalize แล้ว IndexFlatIP ใช้จัดอันดับแบบ cosine similarity ได้
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    return chunks, model, index


try:
    chunks, embedder, index = load_rag_system()
except Exception as e:
    st.error(f"⚠️ โหลด Knowledge Base ไม่สำเร็จ: {e}")
    st.stop()


# ------------------------------------------------------------
# 5. เชื่อมต่อ Gemini
# ------------------------------------------------------------

api_key = (
    os.environ.get("GOOGLE_API_KEY")
    or os.environ.get("GEMINI_API_KEY")
)

if not api_key:
    st.error(
        "⚠️ ไม่พบ API Key กรุณาเพิ่ม GOOGLE_API_KEY "
        "หรือ GEMINI_API_KEY ในไฟล์ .env"
    )
    st.stop()

client = genai.Client(api_key=api_key)

# สามารถเปลี่ยนผ่าน .env ได้ เช่น GEMINI_MODEL=gemini-3.5-flash
GEMINI_MODEL = os.environ.get(
    "GEMINI_MODEL",
    "gemini-3.5-flash",
)


# ------------------------------------------------------------
# 6. Retrieval Functions
# ------------------------------------------------------------

def retrieve_context(question: str, top_k: int = 6):
    """
    ค้นหา chunk ที่เกี่ยวข้องกับคำถามมากที่สุด
    """

    if not question.strip():
        return [], []

    query_embedding = embedder.encode(
        [question],
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    query_embedding = np.asarray(
        query_embedding,
        dtype="float32",
    )

    k = min(top_k, len(chunks))

    scores, indices = index.search(
        query_embedding,
        k,
    )

    retrieved_chunks = []
    retrieved_scores = []

    for idx, score in zip(indices[0], scores[0]):
        if 0 <= idx < len(chunks):
            retrieved_chunks.append(chunks[idx])
            retrieved_scores.append(float(score))

    return retrieved_chunks, retrieved_scores


def get_recent_conversation(max_messages: int = 6):
    """
    สร้างข้อความบริบทสนทนาสั้น ๆ
    เพื่อให้คำถามต่อเนื่อง เช่น "แล้วต้องเอาน้ำกี่ลิตร"
    เข้าใจบริบทจากข้อความก่อนหน้าได้ดีขึ้น
    """

    history = st.session_state.get("messages", [])

    if not history:
        return "ไม่มีประวัติการสนทนาก่อนหน้า"

    recent = history[-max_messages:]

    lines = []

    for message in recent:
        role = message.get("role")

        if role == "user":
            speaker = "ผู้ใช้"
        elif role == "assistant":
            speaker = "ผู้ช่วย"
        else:
            continue

        content = message.get("content", "").strip()

        if content:
            # จำกัดขนาด history ไม่ให้ prompt โตเร็วเกินไป
            lines.append(f"{speaker}: {content[:1500]}")

    return "\n".join(lines) if lines else "ไม่มีประวัติการสนทนาก่อนหน้า"


def build_user_message(
    question: str,
    retrieved_chunks: list[str],
):
    """
    รวม Context จาก RAG + บริบทสนทนา + คำถาม
    โดยวางคำถามไว้ท้ายสุดเพื่อให้โมเดลโฟกัสคำถามปัจจุบัน
    """

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
# 8. Sidebar
# ------------------------------------------------------------

with st.sidebar:
    st.header("🏔️ ขอบเขตของผู้ช่วย")
    st.write("**สถานที่:** ดอยขุนตาลเท่านั้น")
    st.write("**เหมาะสำหรับ:** นักเดินป่ามือใหม่")
    st.write("**ฐานความรู้:** `trekking_gear_kb.md`")

    st.divider()

    st.markdown(
        """
**ถามได้ เช่น**
- ป่าแรกไปดอยขุนตาลไหวไหม
- ต้องเตรียมของอะไรบ้าง
- Y1–Y4 เดินอย่างไร
- นอน Y2 ต้องเตรียมอะไร
- ขึ้น Y4 เช้ามืดต้องพกอะไร
- เดินจากสถานีขุนตานอย่างไร
- ควรเตรียมน้ำและอาหารอย่างไร
"""
    )

    st.warning(
        "ข้อมูลเปิด-ปิด ราคา รถไฟ น้ำ และอากาศ "
        "อาจเปลี่ยนได้ ต้องตรวจสอบล่าสุดก่อนเดินทาง"
    )

    if st.button(
        "🗑️ ล้างประวัติแชท",
        use_container_width=True,
    ):
        st.session_state.messages = []
        st.rerun()


# ------------------------------------------------------------
# 9. ข้อความต้อนรับ
# ------------------------------------------------------------

if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.markdown(
            """
สวัสดีครับ 👋 ผมคือ **Trekking & Camping Buddy**

ผมช่วยเตรียมตัวสำหรับ **การเดินป่าดอยขุนตาล** โดยเฉพาะ
และออกแบบคำแนะนำสำหรับ **มือใหม่** ครับ

ลองถามผมได้ เช่น  
**“ผมไม่เคยเดินป่ามาก่อน ต้องเตรียมอะไรไปดอยขุนตาลบ้าง?”**
"""
        )


# ------------------------------------------------------------
# 10. แสดงประวัติแชท
# ------------------------------------------------------------

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ------------------------------------------------------------
# 11. Chat Input -> Retrieve -> Generate
# ------------------------------------------------------------

prompt = st.chat_input(
    "ถามเรื่องเดินป่าดอยขุนตาล เช่น Y2, Y4, อุปกรณ์ น้ำ อาหาร หรือการเตรียมตัว..."
)

if prompt:
    # แสดงและเก็บคำถามผู้ใช้
    with st.chat_message("user"):
        st.markdown(prompt)

    # Retrieval ทำก่อนเพิ่ม current user message เข้า history
    # เพื่อไม่ให้ข้อความปัจจุบันซ้ำใน conversation_history
    retrieved_chunks, scores = retrieve_context(
        prompt,
        top_k=6,
    )

    user_message = build_user_message(
        prompt,
        retrieved_chunks,
    )

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    # Generate
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

                answer = (
                    response.text.strip()
                    if response.text
                    else "ขออภัยครับ ระบบไม่ได้รับข้อความตอบกลับจาก AI"
                )

                st.markdown(answer)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                    }
                )

            except Exception as e:
                st.error(
                    "เกิดข้อผิดพลาดในการเชื่อมต่อ Gemini\n\n"
                    f"`{e}`"
                )


# ============================================================
# End of app.py
# ============================================================
