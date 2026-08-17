"""
Trekking & Camping Buddy - Caption Generator
=============================================
Caption Generator สำหรับเพจนักเดินป่ามือใหม่
ขอบเขต: "อุทยานแห่งชาติดอยขุนตาล" เท่านั้น

Master Knowledge Base:
    trekking_gear_kb.md
    (รองรับ auto-discover ไฟล์ trekking_gear_kb(2)(1).md ด้วย)

แนวคิด:
- ดึงข้อมูลจาก Master KB ก่อนสร้าง Caption
- ไม่แต่งข้อมูลนอก KB
- ไม่เดาข้อมูล [DYNAMIC] เช่น ราคาอุทยาน, สถานะ Y2/Y4, รถไฟ, อากาศ
- ใช้ Persona / Tone / Guardrail / Quality Checklist จาก KB เป็น Always-on policy
- ห้ามโปรโมตสถานที่เดินป่าอื่น
- ถ้าเป็น Caption สินค้า: ราคาใช้เฉพาะค่าที่ผู้ใช้ส่งเข้ามา
- มี Debug Mode แสดง Section ที่นำมาใช้
- ใช้ Gemini Structured Output เพื่อลด format หลุด

Environment (.env):
    GOOGLE_API_KEY=...
    # หรือ
    GEMINI_API_KEY=...

Optional:
    GEMINI_MODEL=gemini-3.5-flash
    KB_FILE=trekking_gear_kb.md
    CAPTION_TEMPERATURE=0.65
    CAPTION_MAX_OUTPUT_TOKENS=1200

Install:
    pip install google-genai python-dotenv

Examples:
    python caption_generator.py --topic "ไฟฉายคาดหัวสำหรับขึ้น Y4"
    python caption_generator.py --topic "เตรียมตัวขึ้น Y4 เช้ามืด" --kind safety --platform facebook
    python caption_generator.py --topic "เสื้อกันฝน" --kind gear --platform instagram --length short
    python caption_generator.py --topic "ไฟฉายคาดหัว" --kind promo --product-name "Headlamp Pro" --price 590
    python caption_generator.py --self-check
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


# ============================================================
# 0. Project / Environment
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=False)

APP_NAME = "Trekking & Camping Buddy"
DESTINATION = "ดอยขุนตาล"

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash",
)

CAPTION_TEMPERATURE = float(
    os.getenv(
        "CAPTION_TEMPERATURE",
        "0.65",
    )
)

CAPTION_MAX_OUTPUT_TOKENS = int(
    os.getenv(
        "CAPTION_MAX_OUTPUT_TOKENS",
        "1200",
    )
)


# ============================================================
# 1. KB Discovery / Normalization
# ============================================================

def discover_kb_path() -> Path:
    """
    ลำดับ:
    1) KB_FILE ใน .env
    2) trekking_gear_kb.md
    3) trekking_gear_kb(2)(1).md
    4) auto-discover .md ที่มี Section 84 และคำว่า ดอยขุนตาล
    """

    env_name = os.getenv("KB_FILE")

    if env_name:
        candidate = Path(env_name)
        if not candidate.is_absolute():
            candidate = BASE_DIR / candidate

        if not candidate.exists():
            raise FileNotFoundError(
                f"KB_FILE='{env_name}' แต่ไม่พบไฟล์"
            )

        return candidate

    preferred_names = (
        "trekking_gear_kb.md",
        "trekking_gear_kb(2)(1).md",
    )

    for name in preferred_names:
        candidate = BASE_DIR / name
        if candidate.exists():
            return candidate

    candidates: list[tuple[int, Path]] = []

    for path in BASE_DIR.glob("*.md"):
        try:
            sample = path.read_text(
                encoding="utf-8",
                errors="ignore",
            )
        except OSError:
            continue

        score = 0

        if "ดอยขุนตาล" in sample:
            score += 3

        if "Knowledge Base" in sample:
            score += 2

        if (
            "## 84." in sample
            or "**## 84." in sample
        ):
            score += 4

        if score >= 7:
            candidates.append(
                (score, path)
            )

    if not candidates:
        raise FileNotFoundError(
            "ไม่พบ Master KB ดอยขุนตาล "
            "กรุณาวาง trekking_gear_kb.md "
            "ไว้โฟลเดอร์เดียวกับ caption_generator.py"
        )

    candidates.sort(
        key=lambda item: (
            item[0],
            item[1].stat().st_size,
        ),
        reverse=True,
    )

    return candidates[0][1]


def normalize_markdown(text: str) -> str:
    """
    รองรับ KB ที่มี escaped markdown เช่น
        **## 67. ...**
        \\-
        \\>
        \\*
    """

    text = (
        text
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )

    replacements = {
        r"\>": ">",
        r"\|": "|",
        r"\-": "-",
        r"\*": "*",
        r"\_": "_",
        r"\#": "#",
        r"\`": "`",
    }

    for source, target in replacements.items():
        text = text.replace(
            source,
            target,
        )

    text = re.sub(
        r"(?m)^(\s*)(\d+)\\\.\s+",
        r"\1\2. ",
        text,
    )

    text = re.sub(
        r"(?m)^\*\*(#{1,6}\s+.*?)\*\*\s*$",
        r"\1",
        text,
    )

    text = re.sub(
        r"(?m)^\*\*---\*\*\s*$",
        "---",
        text,
    )

    previous = None

    while previous != text:
        previous = text
        text = text.replace(
            "****",
            "**",
        )

    return text.strip()


@dataclass(frozen=True)
class KBSection:
    number: int
    title: str
    text: str


SECTION_RE = re.compile(
    r"(?m)^##\s+(\d+)\.\s+(.+?)\s*$"
)


def parse_kb_sections(
    text: str,
) -> dict[int, KBSection]:
    matches = list(
        SECTION_RE.finditer(text)
    )

    if not matches:
        raise ValueError(
            "ไม่พบ numbered sections ใน KB"
        )

    sections: dict[int, KBSection] = {}

    for index, match in enumerate(matches):
        number = int(match.group(1))
        title = match.group(2).strip()

        end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(text)
        )

        sections[number] = KBSection(
            number=number,
            title=title,
            text=text[
                match.start():end
            ].strip(),
        )

    return sections


try:
    KB_PATH = discover_kb_path()
    KB_TEXT = normalize_markdown(
        KB_PATH.read_text(
            encoding="utf-8"
        )
    )
    KB_SECTIONS = parse_kb_sections(
        KB_TEXT
    )
except Exception as exc:
    KB_PATH = None
    KB_TEXT = ""
    KB_SECTIONS = {}
    KB_LOAD_ERROR = exc
else:
    KB_LOAD_ERROR = None


# ============================================================
# 2. Caption Scope / Policy
# ============================================================

# Always-on behavior จาก Master KB
ALWAYS_ON_POLICY_SECTIONS = {
    65,  # Dynamic data
    67,  # Guardrail
    79,  # Data confidence
    80,  # Source hierarchy
    81,  # Persona
    84,  # Quality checklist
}


def get_sections_text(
    numbers: Iterable[int],
    max_chars: int = 18000,
) -> str:
    parts = []
    used = 0

    for number in sorted(
        set(numbers)
    ):
        section = KB_SECTIONS.get(
            number
        )

        if not section:
            continue

        block = section.text

        if (
            used + len(block)
            > max_chars
        ):
            continue

        parts.append(block)
        used += len(block)

    return "\n\n---\n\n".join(
        parts
    )


POLICY_CONTEXT = get_sections_text(
    ALWAYS_ON_POLICY_SECTIONS,
    max_chars=18000,
)


# ============================================================
# 3. Topic Routing to KB Sections
# ============================================================

TOPIC_SECTION_RULES: list[
    tuple[tuple[str, ...], set[int]]
] = [
    (
        (
            "มือใหม่",
            "ป่าแรก",
            "ยาก",
            "เหมาะไหม",
        ),
        {1, 4, 54, 56, 57, 63, 68},
    ),
    (
        (
            "เส้นทาง",
            "y1",
            "y2",
            "y3",
            "y4",
            "ยอด",
        ),
        {3, 4, 5, 6, 7, 8, 51, 52, 73},
    ),
    (
        (
            "y2",
            "เต็นท์",
            "กางเต็นท์",
            "พักค้าง",
            "ค้างคืน",
        ),
        {9, 10, 11, 12, 20, 39, 40, 60, 72},
    ),
    (
        (
            "y4",
            "พระอาทิตย์ขึ้น",
            "เช้ามืด",
            "daypack",
        ),
        {8, 21, 32, 41, 52, 53, 61, 69, 73},
    ),
    (
        (
            "น้ำ",
            "ขวดน้ำ",
            "hydration",
        ),
        {19, 20, 21, 53, 58, 60},
    ),
    (
        (
            "อาหาร",
            "ขนม",
            "energy",
            "พลังงาน",
        ),
        {22, 23, 24, 53},
    ),
    (
        (
            "กระเป๋า",
            "backpack",
            "เป้",
        ),
        {25, 26, 38, 53},
    ),
    (
        (
            "รองเท้า",
            "ถุงเท้า",
            "เทรล",
            "แผลพุพอง",
        ),
        {27, 28, 29, 35, 43, 55, 63},
    ),
    (
        (
            "เสื้อ",
            "เสื้อผ้า",
            "กันหนาว",
            "หนาว",
            "อุณหภูมิ",
            "fleece",
        ),
        {30, 31, 40, 45, 47, 69},
    ),
    (
        (
            "ฝน",
            "กันฝน",
            "rain",
            "poncho",
            "rain cover",
        ),
        {31, 45, 47, 55, 69},
    ),
    (
        (
            "ไฟฉาย",
            "headlamp",
            "ไฟคาดหัว",
        ),
        {32, 41, 53, 61, 63},
    ),
    (
        (
            "power bank",
            "แบต",
            "โทรศัพท์",
            "มือถือ",
        ),
        {33, 34, 53, 58, 70},
    ),
    (
        (
            "แผนที่",
            "offline",
            "หลง",
            "นำทาง",
        ),
        {34, 41, 49, 70, 71},
    ),
    (
        (
            "ปฐมพยาบาล",
            "ฉุกเฉิน",
            "บาดเจ็บ",
            "งูกัด",
        ),
        {35, 44, 71, 74},
    ),
    (
        (
            "trekking pole",
            "ไม้เท้า",
            "ไม้เดิน",
            "pole",
        ),
        {36, 43},
    ),
    (
        (
            "ของจำเป็น",
            "อุปกรณ์",
            "checklist",
            "เตรียมของ",
        ),
        {25, 27, 30, 31, 32, 33, 34, 35, 37, 38, 40, 53, 58},
    ),
    (
        (
            "solo",
            "คนเดียว",
            "ไปคนเดียว",
        ),
        {41, 48, 49, 70, 71, 83},
    ),
    (
        (
            "ทาก",
            "แมลง",
        ),
        {45, 46},
    ),
    (
        (
            "งู",
            "สัตว์ป่า",
            "หมูป่า",
        ),
        {46, 74},
    ),
    (
        (
            "รถไฟ",
            "ขุนตาน",
            "เดินทาง",
        ),
        {2, 15, 16, 17, 18, 51, 78},
    ),
    (
        (
            "ราคา",
            "งบ",
            "ค่าใช้จ่าย",
            "ค่าเข้า",
            "ค่าเช่า",
        ),
        {65, 75, 79, 80},
    ),
    (
        (
            "กฎ",
            "ห้าม",
            "โดรน",
            "สัตว์เลี้ยง",
            "แอลกอฮอล์",
            "ขยะ",
            "ธรรมชาติ",
        ),
        {50, 77},
    ),
    (
        (
            "ผู้สูงอายุ",
            "เด็ก",
            "โรค",
            "ความดัน",
            "หัวใจ",
        ),
        {57, 67, 71, 76},
    ),
]


def select_topic_sections(
    topic: str,
) -> list[int]:
    lowered = topic.lower()
    sections: set[int] = set()

    for triggers, numbers in TOPIC_SECTION_RULES:
        if any(
            trigger.lower() in lowered
            for trigger in triggers
        ):
            sections.update(
                numbers
            )

    # fallback: basic beginner overview + equipment
    if not sections:
        sections.update(
            {1, 37, 44, 57, 68}
        )

    return sorted(
        sections
    )


# ============================================================
# 4. Scope / Dynamic Guards
# ============================================================

OUT_OF_SCOPE_TERMS = (
    "ภูกระดึง",
    "ภูสอยดาว",
    "ดอยอินทนนท์",
    "อินทนนท์",
    "เชียงดาว",
    "ดอยหลวงเชียงดาว",
    "เขาหลวงสุโขทัย",
    "เขาหลวง",
    "ม่อนจอง",
    "ดอยม่อนจอง",
    "ภูชี้ฟ้า",
    "ดอยผ้าห่มปก",
)

DYNAMIC_TERMS = (
    "วันนี้",
    "ตอนนี้",
    "พรุ่งนี้",
    "ล่าสุด",
    "ปัจจุบัน",
    "เปิดไหม",
    "ปิดไหม",
    "ราคาเข้า",
    "ค่าเข้า",
    "ค่ากางเต็นท์",
    "ค่าเช่าเต็นท์",
    "ตารางรถไฟ",
    "รถไฟกี่โมง",
    "ขบวนรถไฟ",
    "ฝนตกไหม",
    "พยากรณ์",
    "อากาศวันนี้",
    "มีน้ำไหม",
    "ห้องน้ำใช้ได้ไหม",
    "มีสัญญาณไหม",
    "พระอาทิตย์ขึ้นกี่โมง",
)


def is_in_scope(
    topic: str,
) -> bool:
    lowered = topic.lower()

    return not any(
        term.lower() in lowered
        for term in OUT_OF_SCOPE_TERMS
    )


def is_dynamic_topic(
    topic: str,
) -> bool:
    lowered = topic.lower()

    return any(
        term.lower() in lowered
        for term in DYNAMIC_TERMS
    )


# ============================================================
# 5. Caption Settings
# ============================================================

VALID_KINDS = {
    "educational",
    "gear",
    "route",
    "safety",
    "promo",
    "checklist",
}

VALID_PLATFORMS = {
    "facebook",
    "instagram",
    "tiktok",
    "general",
}

VALID_LENGTHS = {
    "short",
    "medium",
    "long",
}

LENGTH_GUIDES = {
    "short": (
        "ประมาณ 2–3 ประโยคสั้น กระชับ "
        "เหมาะกับโพสต์เร็วหรือภาพเดี่ยว"
    ),
    "medium": (
        "ประมาณ 4–6 ประโยค หรือ 1 ย่อหน้าสั้น "
        "อ่านง่ายบน Social Media"
    ),
    "long": (
        "ประมาณ 6–10 ประโยค สามารถใช้ bullet สั้นได้ "
        "แต่ยังต้องเป็น Caption ไม่ใช่บทความ"
    ),
}

PLATFORM_GUIDES = {
    "facebook": (
        "Facebook: อ่านง่าย มี hook เปิดเรื่อง "
        "แล้วให้ข้อมูลที่เป็นประโยชน์ก่อน CTA"
    ),
    "instagram": (
        "Instagram: กระชับ มีภาพในหัว ใช้ emoji พอดี "
        "และ hashtag ไม่มากเกินไป"
    ),
    "tiktok": (
        "TikTok caption: hook เร็ว ประโยคสั้น "
        "เน้น takeaway ชัดเจน"
    ),
    "general": (
        "Social media ทั่วไป: อ่านง่าย กระชับ "
        "และนำไปใช้ได้หลายแพลตฟอร์ม"
    ),
}

DEFAULT_CTAS = {
    "educational": (
        "เซฟโพสต์นี้ไว้ แล้วทักมาขอ Checklist "
        "ดอยขุนตาลสำหรับมือใหม่ได้ครับ"
    ),
    "gear": (
        "ยังไม่แน่ใจว่าต้องพกอะไรบ้าง "
        "ทักมาขอ Checklist ดอยขุนตาลได้ครับ"
    ),
    "route": (
        "กำลังวางแผนดอยขุนตาลอยู่ "
        "ทักมาขอ Checklist สำหรับมือใหม่ได้ครับ"
    ),
    "safety": (
        "ก่อนออกเดินทาง อย่าลืมตรวจข้อมูลล่าสุดกับอุทยาน "
        "และเซฟ Checklist นี้ไว้ครับ"
    ),
    "promo": (
        "สนใจอุปกรณ์สำหรับทริปดอยขุนตาล "
        "ทักแชทมาสอบถามได้ครับ"
    ),
    "checklist": (
        "อยากได้ Checklist แบบเต็มสำหรับดอยขุนตาล "
        "ทักแชทมาได้ครับ"
    ),
}


# ============================================================
# 6. Structured Output
# ============================================================

CAPTION_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "caption": {
            "type": "string",
        },
        "hashtags": {
            "type": "array",
            "items": {
                "type": "string",
            },
            "maxItems": 8,
        },
        "disclaimer": {
            "type": "string",
        },
        "source_sections": {
            "type": "array",
            "items": {
                "type": "integer",
            },
        },
    },
    "required": [
        "caption",
        "hashtags",
        "disclaimer",
        "source_sections",
    ],
    "additionalProperties": False,
}


# ============================================================
# 7. Gemini
# ============================================================

def require_genai():
    if genai is None or types is None:
        raise RuntimeError(
            "ยังไม่ได้ติดตั้ง google-genai "
            "กรุณารัน: pip install google-genai"
        )


def get_api_key(
    api_key: str | None = None,
) -> str:
    key = (
        api_key
        or os.getenv("GOOGLE_API_KEY")
        or os.getenv("GEMINI_API_KEY")
    )

    if not key:
        raise RuntimeError(
            "ไม่พบ GOOGLE_API_KEY หรือ GEMINI_API_KEY"
        )

    return key


def create_client(
    api_key: str | None = None,
):
    require_genai()

    return genai.Client(
        api_key=get_api_key(
            api_key
        )
    )


# ============================================================
# 8. System Instruction
# ============================================================

SYSTEM_INSTRUCTION = f"""
คุณคือ Social Media Manager ของเพจ "{APP_NAME}"

เพจนี้ให้ความรู้และช่วยเตรียมตัวสำหรับ
"นักเดินป่ามือใหม่ที่ต้องการไปอุทยานแห่งชาติดอยขุนตาล"
เท่านั้น

========================
SCOPE
========================

- สร้าง Caption เฉพาะเรื่องดอยขุนตาล
- ห้ามสร้าง Caption โปรโมตอุทยาน/ภูเขาอื่น
- ห้ามเปรียบเทียบรายละเอียดของสถานที่อื่น
- "ดอยขุนตาล" = ชื่อดอย/อุทยาน
- "สถานีรถไฟขุนตาน" = ชื่อสถานีรถไฟ

========================
VOICE
========================

- ภาษาไทย
- สุภาพ เป็นกันเอง
- ใช้ "ครับ" อย่างเป็นธรรมชาติ
- มือใหม่อ่านแล้วเข้าใจได้
- ไม่สั่งสอนหรือทำให้ผู้ใช้อาย
- ไม่ขายของเกินจำเป็น
- เน้นความปลอดภัยแบบพอดี
- ใช้ emoji ได้เล็กน้อย ไม่ใส่ทุกบรรทัด
- ห้ามใช้ em dash (—)

========================
FACTUAL GROUNDING
========================

- ใช้ KB Context ที่ให้มาเป็นแหล่งข้อเท็จจริง
- ห้ามเติมข้อมูลดอยขุนตาลจากความจำของโมเดล
- ถ้า KB ไม่รองรับข้อมูล ให้หลีกเลี่ยงข้ออ้างนั้น
- ห้ามแต่งราคา เวลาเปิด/ปิด ตารางรถไฟ อากาศ
  น้ำ ห้องน้ำ สัญญาณโทรศัพท์ หรือกฎเฉพาะวัน
- ข้อมูล [ESTIMATE] ต้องใช้คำว่า
  "ประมาณ", "โดยทั่วไป", หรือ "ควรเผื่อ"

========================
DYNAMIC DATA
========================

ถ้าหัวข้อเกี่ยวกับ:
ราคา / สถานะ Y2-Y4 / อากาศ / รถไฟ /
น้ำ / ห้องน้ำ / ร้านค้า / สัญญาณ /
เบอร์ติดต่อ / เวลาพระอาทิตย์ขึ้น

ห้ามเขียนให้ดูเหมือนเป็นข้อมูลสด เว้นแต่ input ระบุว่า
ข้อมูลนั้นมาจากแหล่งปัจจุบันและให้ตัวเลขมาโดยตรง

ควรใช้ถ้อยคำเช่น:
"ข้อมูลอาจเปลี่ยนได้ ควรตรวจสอบล่าสุดจากช่องทางทางการก่อนเดินทาง"

========================
PROMOTION
========================

- Caption ประเภท educational/safety/route:
  ให้คุณค่าก่อน CTA
- Caption ประเภท gear:
  อธิบายว่าอุปกรณ์ช่วยอะไรกับทริปดอยขุนตาล
  โดยไม่กล่าวอ้างเกิน KB
- Caption ประเภท promo:
  ห้ามแต่งราคา ส่วนลด สต๊อก หรือโปรโมชั่น
- ถ้ามีราคา ให้ใช้เฉพาะราคาที่ user input ส่งมา
- ห้ามใช้คำว่า "ดีที่สุด", "ปลอดภัย 100%",
  "รับประกัน", "ต้องซื้อ" ถ้าไม่มีหลักฐาน
- ไม่ควร CTA ว่า "สั่งเลย" ในโพสต์ความรู้
  เว้นแต่เป็น promo จริงและผู้ใช้ตั้งใจทำโพสต์ขาย

========================
QUALITY
========================

ก่อนส่ง Caption ตรวจแบบเงียบ ๆ:
1. Scope ถูกไหม
2. ข้อเท็จจริงมีใน KB ไหม
3. Dynamic data ถูก disclaimer ไหม
4. Safety ไม่เกินจริงไหม
5. Persona สุภาพ/เป็นกันเองไหม
6. CTA เข้ากับชนิดโพสต์ไหม
7. ไม่มี hallucination ไหม

========================
MASTER KB POLICY
========================

<master_kb_policy>
{POLICY_CONTEXT}
</master_kb_policy>
""".strip()


# ============================================================
# 9. Build Prompt
# ============================================================

def build_caption_prompt(
    *,
    topic: str,
    kind: str,
    platform: str,
    length: str,
    cta: str | None,
    product_name: str | None,
    price: float | None,
    extra_notes: str | None,
) -> tuple[str, list[int]]:
    selected_sections = select_topic_sections(
        topic
    )

    # เพิ่ม policy sections เข้า source context เฉพาะที่จำเป็น
    context_sections = sorted(
        set(selected_sections)
        | {65, 67, 79, 80, 81, 84}
    )

    kb_context = get_sections_text(
        context_sections,
        max_chars=22000,
    )

    dynamic = is_dynamic_topic(
        topic
    )

    final_cta = (
        cta.strip()
        if cta and cta.strip()
        else DEFAULT_CTAS[kind]
    )

    product_context = "ไม่มีข้อมูลสินค้าเฉพาะ"

    if product_name:
        product_context = (
            f"ชื่อสินค้า: {product_name}"
        )

        if price is not None:
            product_context += (
                f"\nราคาที่ผู้ใช้ให้มา: {price:,.2f} บาท"
            )
        else:
            product_context += (
                "\nไม่มีราคาที่ผู้ใช้ให้มา "
                "ห้ามสร้างราคาเอง"
            )

    elif price is not None:
        product_context = (
            f"ผู้ใช้ให้ราคา: {price:,.2f} บาท "
            "แต่ไม่ได้ระบุชื่อสินค้า"
        )

    dynamic_directive = (
        "หัวข้อนี้มีลักษณะ [DYNAMIC] "
        "ต้องมี disclaimer และห้ามเขียนเหมือนตรวจข้อมูลสดแล้ว"
        if dynamic
        else "ไม่พบ trigger ของข้อมูลสดโดยตรง"
    )

    prompt = f"""
สร้าง Social Media Caption ตามข้อมูลนี้

<topic>
{topic}
</topic>

<caption_type>
{kind}
</caption_type>

<platform>
{platform}
</platform>

<length>
{length}: {LENGTH_GUIDES[length]}
</length>

<platform_style>
{PLATFORM_GUIDES[platform]}
</platform_style>

<call_to_action>
{final_cta}
</call_to_action>

<product_context>
{product_context}
</product_context>

<dynamic_directive>
{dynamic_directive}
</dynamic_directive>

<extra_notes>
{extra_notes.strip() if extra_notes else "-"}
</extra_notes>

<kb_context>
{kb_context}
</kb_context>

ข้อกำหนดของ Caption:
- เปิดด้วย hook ที่สัมพันธ์กับหัวข้อ
- ให้ข้อมูลที่ใช้ได้จริงสำหรับมือใหม่
- ถ้าเป็น gear ให้บอก "ใช้ทำอะไร/ช่วยลดความเสี่ยงอะไร"
  โดยยึด KB
- ถ้าเป็น safety ให้ใช้รูปแบบ
  "ความเสี่ยง → เหตุผล → วิธีลดความเสี่ยง"
- ใช้ emoji 0–3 ตัวโดยประมาณ
- CTA อยู่ท้าย
- ห้ามใช้ em dash
- Hashtag 3–6 อัน
- Hashtag ต้องเกี่ยวกับดอยขุนตาล/เดินป่ามือใหม่/หัวข้อ
- อย่าใส่ #ภูกระดึง #เชียงดาว หรือสถานที่อื่น
- disclaimer ให้เป็นข้อความสั้น ถ้าไม่จำเป็นให้คืน string ว่าง
- source_sections ให้คืนเฉพาะเลข Section จาก KB ที่ใช้จริง
""".strip()

    return prompt, selected_sections


# ============================================================
# 10. Post-generation Validation
# ============================================================

def sanitize_hashtag(
    tag: str,
) -> str:
    tag = str(tag).strip()

    if not tag:
        return ""

    if not tag.startswith("#"):
        tag = "#" + tag

    tag = re.sub(
        r"\s+",
        "",
        tag,
    )

    return tag[:80]


def validate_generated_output(
    result: dict[str, Any],
    *,
    topic: str,
    kind: str,
    product_name: str | None,
    price: float | None,
) -> dict[str, Any]:
    caption = str(
        result.get(
            "caption",
            "",
        )
    ).strip()

    disclaimer = str(
        result.get(
            "disclaimer",
            "",
        )
    ).strip()

    source_sections = []

    for value in result.get(
        "source_sections",
        [],
    ):
        try:
            number = int(value)
        except (
            TypeError,
            ValueError,
        ):
            continue

        if number in KB_SECTIONS:
            source_sections.append(
                number
            )

    source_sections = sorted(
        set(source_sections)
    )

    hashtags = []

    for tag in result.get(
        "hashtags",
        [],
    ):
        cleaned = sanitize_hashtag(
            tag
        )

        if (
            cleaned
            and cleaned not in hashtags
        ):
            hashtags.append(
                cleaned
            )

    hashtags = hashtags[:8]

    if not caption:
        raise RuntimeError(
            "Gemini ไม่คืน Caption"
        )

    # System rule: no em dash
    caption = caption.replace(
        "—",
        "-"
    )

    disclaimer = disclaimer.replace(
        "—",
        "-"
    )

    # Scope check
    full_output = (
        caption
        + "\n"
        + disclaimer
        + "\n"
        + " ".join(hashtags)
    ).lower()

    for term in OUT_OF_SCOPE_TERMS:
        if term.lower() in full_output:
            raise RuntimeError(
                "Caption ที่สร้างมีสถานที่นอกขอบเขต "
                f"('{term}') จึงยกเลิกผลลัพธ์เพื่อป้องกัน hallucination"
            )

    # Dynamic freshness enforcement
    if (
        is_dynamic_topic(topic)
        and not disclaimer
    ):
        disclaimer = (
            "ข้อมูลส่วนนี้อาจเปลี่ยนได้ "
            "ควรตรวจสอบล่าสุดจากช่องทางทางการก่อนเดินทางครับ"
        )

    # Promo price rule
    if kind == "promo" and price is None:
        # ไม่จำเป็นต้องมีคำว่า บาท ถ้าไม่มีราคา
        # หาก model แต่งเลขราคา ให้หยุดแทนการพยายามแก้
        if re.search(
            r"\b\d[\d,]*(?:\.\d+)?\s*บาท\b",
            caption,
        ):
            raise RuntimeError(
                "พบราคาที่โมเดลสร้างขึ้นทั้งที่ผู้ใช้ไม่ได้ให้ราคา "
                "จึงยกเลิก Caption"
            )

    # ถ้าระบุราคา ให้ตรวจว่าราคาที่ปรากฏไม่ต่างจาก user input
    if price is not None:
        money_values = re.findall(
            r"(\d[\d,]*(?:\.\d+)?)\s*บาท",
            caption,
        )

        for value in money_values:
            try:
                parsed = float(
                    value.replace(
                        ",",
                        "",
                    )
                )
            except ValueError:
                continue

            if abs(
                parsed - float(price)
            ) > 0.01:
                raise RuntimeError(
                    "Caption มีราคาที่ไม่ตรงกับราคาที่ผู้ใช้ให้มา "
                    "จึงยกเลิกผลลัพธ์"
                )

    # CTA must exist roughly
    if not any(
        word in caption
        for word in (
            "ทัก",
            "เซฟ",
            "สอบถาม",
            "Checklist",
            "เช็กลิสต์",
            "ติดตาม",
            "แชร์",
        )
    ):
        caption = (
            caption.rstrip()
            + "\n\n"
            + DEFAULT_CTAS[kind]
        )

    return {
        "caption": caption,
        "hashtags": hashtags,
        "disclaimer": disclaimer,
        "source_sections": source_sections,
    }


# ============================================================
# 11. Public Generate Function
# ============================================================

def generate_caption(
    topic: str,
    api_key: str | None = None,
    *,
    kind: str = "educational",
    platform: str = "facebook",
    length: str = "medium",
    cta: str | None = None,
    product_name: str | None = None,
    price: float | None = None,
    extra_notes: str | None = None,
) -> dict[str, Any]:
    """
    Generate Caption จาก Master KB

    Returns:
        {
            "caption": str,
            "hashtags": list[str],
            "disclaimer": str,
            "source_sections": list[int],
            "kb_file": str,
            "model": str,
        }
    """

    topic = str(
        topic
    ).strip()

    if not topic:
        raise ValueError(
            "topic ห้ามว่าง"
        )

    if kind not in VALID_KINDS:
        raise ValueError(
            "kind ต้องเป็น: "
            + ", ".join(
                sorted(
                    VALID_KINDS
                )
            )
        )

    if platform not in VALID_PLATFORMS:
        raise ValueError(
            "platform ต้องเป็น: "
            + ", ".join(
                sorted(
                    VALID_PLATFORMS
                )
            )
        )

    if length not in VALID_LENGTHS:
        raise ValueError(
            "length ต้องเป็น: "
            + ", ".join(
                sorted(
                    VALID_LENGTHS
                )
            )
        )

    if not is_in_scope(
        topic
    ):
        raise ValueError(
            "ระบบ Caption Generator นี้รองรับเฉพาะดอยขุนตาล "
            "จึงไม่สร้าง Caption ของสถานที่อื่นครับ"
        )

    if KB_LOAD_ERROR is not None:
        raise RuntimeError(
            f"โหลด Master KB ไม่สำเร็จ: {KB_LOAD_ERROR}"
        )

    client = create_client(
        api_key
    )

    prompt, selected_sections = build_caption_prompt(
        topic=topic,
        kind=kind,
        platform=platform,
        length=length,
        cta=cta,
        product_name=product_name,
        price=price,
        extra_notes=extra_notes,
    )

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=CAPTION_TEMPERATURE,
                max_output_tokens=CAPTION_MAX_OUTPUT_TOKENS,
                response_mime_type="application/json",
                response_json_schema=CAPTION_OUTPUT_SCHEMA,
            ),
        )
    except Exception as exc:
        raise RuntimeError(
            f"Gemini generation failed: {exc}"
        ) from exc

    if not getattr(
        response,
        "text",
        None,
    ):
        raise RuntimeError(
            "Gemini ไม่คืนข้อความตอบกลับ"
        )

    try:
        raw_result = json.loads(
            response.text
        )
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Gemini Structured Output ไม่ใช่ JSON ที่ถูกต้อง"
        ) from exc

    result = validate_generated_output(
        raw_result,
        topic=topic,
        kind=kind,
        product_name=product_name,
        price=price,
    )

    # หาก model ไม่คืน source sections
    # ใช้ selected sections เป็น traceability fallback
    if not result[
        "source_sections"
    ]:
        result[
            "source_sections"
        ] = selected_sections

    result[
        "kb_file"
    ] = (
        KB_PATH.name
        if KB_PATH
        else None
    )

    result[
        "model"
    ] = GEMINI_MODEL

    result[
        "topic"
    ] = topic

    result[
        "kind"
    ] = kind

    result[
        "platform"
    ] = platform

    return result


# ============================================================
# 12. Formatting
# ============================================================

def format_caption(
    result: dict[str, Any],
    *,
    include_debug: bool = False,
) -> str:
    parts = [
        result["caption"].strip()
    ]

    if result.get(
        "disclaimer"
    ):
        parts.append(
            result[
                "disclaimer"
            ].strip()
        )

    hashtags = result.get(
        "hashtags",
        [],
    )

    if hashtags:
        parts.append(
            " ".join(
                hashtags
            )
        )

    if include_debug:
        parts.append(
            (
                "[DEBUG] "
                f"KB={result.get('kb_file')} | "
                "Sections="
                + ",".join(
                    str(number)
                    for number in result.get(
                        "source_sections",
                        [],
                    )
                )
                + f" | Model={result.get('model')}"
            )
        )

    return "\n\n".join(
        parts
    )


# ============================================================
# 13. Self Check
# ============================================================

def self_check() -> dict[str, Any]:
    return {
        "kb_found": (
            KB_PATH is not None
        ),
        "kb_file": (
            KB_PATH.name
            if KB_PATH
            else None
        ),
        "kb_sections": len(
            KB_SECTIONS
        ),
        "kb_has_section_65": (
            65 in KB_SECTIONS
        ),
        "kb_has_section_67": (
            67 in KB_SECTIONS
        ),
        "kb_has_section_81": (
            81 in KB_SECTIONS
        ),
        "kb_has_section_84": (
            84 in KB_SECTIONS
        ),
        "google_genai_installed": (
            genai is not None
            and types is not None
        ),
        "api_key_found": bool(
            os.getenv(
                "GOOGLE_API_KEY"
            )
            or os.getenv(
                "GEMINI_API_KEY"
            )
        ),
        "model": GEMINI_MODEL,
        "ready": (
            KB_LOAD_ERROR is None
            and genai is not None
            and types is not None
            and bool(
                os.getenv(
                    "GOOGLE_API_KEY"
                )
                or os.getenv(
                    "GEMINI_API_KEY"
                )
            )
        ),
    }


# ============================================================
# 14. CLI
# ============================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Trekking & Camping Buddy Caption Generator "
            "- ดอยขุนตาลเท่านั้น"
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--topic",
        type=str,
        help="หัวข้อ Caption",
    )

    parser.add_argument(
        "--kind",
        choices=sorted(
            VALID_KINDS
        ),
        default="educational",
        help=(
            "ประเภทโพสต์: educational, gear, route, "
            "safety, promo, checklist"
        ),
    )

    parser.add_argument(
        "--platform",
        choices=sorted(
            VALID_PLATFORMS
        ),
        default="facebook",
    )

    parser.add_argument(
        "--length",
        choices=sorted(
            VALID_LENGTHS
        ),
        default="medium",
    )

    parser.add_argument(
        "--cta",
        type=str,
        help="กำหนด CTA เอง",
    )

    parser.add_argument(
        "--product-name",
        type=str,
        help="ชื่อสินค้า สำหรับ gear/promo",
    )

    parser.add_argument(
        "--price",
        type=float,
        help=(
            "ราคาที่ผู้ใช้ให้มาเท่านั้น "
            "ระบบจะไม่สร้างราคาเอง"
        ),
    )

    parser.add_argument(
        "--notes",
        type=str,
        help="คำสั่งเสริมสำหรับ Caption",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="แสดง KB Sections ที่ใช้",
    )

    parser.add_argument(
        "--json-output",
        action="store_true",
        help="พิมพ์ผลลัพธ์เป็น JSON",
    )

    parser.add_argument(
        "--self-check",
        action="store_true",
        help="ตรวจ KB / SDK / API key โดยไม่เรียก Gemini",
    )

    return parser.parse_args()


def main() -> int:
    load_dotenv(
        BASE_DIR / ".env",
        override=False,
    )

    args = parse_args()

    if args.self_check:
        print(
            json.dumps(
                self_check(),
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    topic = (
        args.topic.strip()
        if args.topic
        else ""
    )

    # รองรับ interactive แบบไฟล์เดิม
    if not topic:
        try:
            topic = input(
                "หัวข้อ Caption ดอยขุนตาล: "
            ).strip()
        except EOFError:
            topic = ""

    if not topic:
        print(
            "❌ กรุณาใส่ --topic หรือกรอกหัวข้อ",
            file=sys.stderr,
        )
        return 2

    if (
        args.price is not None
        and args.price < 0
    ):
        print(
            "❌ price ต้องไม่น้อยกว่า 0",
            file=sys.stderr,
        )
        return 2

    try:
        result = generate_caption(
            topic,
            kind=args.kind,
            platform=args.platform,
            length=args.length,
            cta=args.cta,
            product_name=args.product_name,
            price=args.price,
            extra_notes=args.notes,
        )

        if args.json_output:
            print(
                json.dumps(
                    result,
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            print()
            print(
                format_caption(
                    result,
                    include_debug=args.debug,
                )
            )

        return 0

    except Exception as exc:
        print(
            f"❌ Error: {exc}",
            file=sys.stderr,
        )

        return 1


if __name__ == "__main__":
    sys.exit(
        main()
    )
