"""
Trekking & Camping Buddy - Agent Harness
=========================================
Agent / Tool Router สำหรับโปรเจกต์ AI Chatbot
ขอบเขต: "อุทยานแห่งชาติดอยขุนตาล" เท่านั้น

Master Knowledge Base:
    trekking_gear_kb.md

ทำงานร่วมกับ:
    app.py
    sales_logger.py
    trekking_gear_kb.md

หน้าที่ของไฟล์นี้:
1) รับคำสั่งภาษาไทยจาก CLI / โปรแกรมอื่น
2) ใช้ Gemini แปลงคำสั่งเป็น Structured Tool Call
3) ตรวจ Scope + Confirmation + Missing Fields ซ้ำด้วย Local Guard
4) เรียก sales_logger.log_sale() เมื่อผู้ใช้ "ยืนยันซื้อ/เช่า" ชัดเจนเท่านั้น
5) สร้าง Checklist สำหรับดอยขุนตาลจากกฎใน Master KB
6) ส่ง Telegram alert เมื่อผู้ใช้สั่งให้ส่งจริง
7) บันทึก Agent Trace เป็น JSONL สำหรับ debug / นำเสนออาจารย์

หลักสำคัญ:
- destination ถูกล็อกเป็น "ดอยขุนตาล"
- ไม่มี porter / ลูกหาบ
- ไม่เดาราคา สถานะ Y2 อากาศ น้ำ รถไฟ หรือข้อมูล [DYNAMIC]
- ไม่บันทึก sale เพียงเพราะผู้ใช้ถามว่าสินค้าน่าสนใจหรือไม่
- การเขียน Google Sheets ใช้ sales_logger.py เพียงจุดเดียว
- Agent Harness ไม่ duplicate Google Sheets schema

Environment Variables:
    GOOGLE_API_KEY=...
    # หรือ
    GEMINI_API_KEY=...

Optional:
    GEMINI_MODEL=gemini-3.5-flash
    KB_FILE=trekking_gear_kb.md
    AGENT_TRACE_FILE=agent_trace.jsonl
    AGENT_LOG_RAW_COMMANDS=true

Telegram:
    TELEGRAM_BOT_TOKEN=...
    TELEGRAM_CHAT_ID=...

Google Sheets:
    ใช้ค่าจาก sales_logger.py เช่น
    GOOGLE_SHEETS_CREDENTIALS / GOOGLE_SHEETS_CREDENTIALS_FILE
    GOOGLE_SHEET_ID
    GOOGLE_WORKSHEET_NAME

Install:
    pip install google-genai python-dotenv requests gspread google-auth

Run:
    python agent_harness.py --cmd "ยืนยันซื้อไฟฉายคาดหัว 1 ชิ้น ราคา 590 บาท"

Dry-run:
    python agent_harness.py --cmd "ยืนยันซื้อไฟฉายคาดหัว 1 ชิ้น ราคา 590 บาท" --dry-run

JSON output:
    python agent_harness.py --cmd "..." --json-output
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo

try:
    import requests
except ImportError:
    requests = None

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

TRACE_FILE = BASE_DIR / os.getenv(
    "AGENT_TRACE_FILE",
    "agent_trace.jsonl",
)

LOG_RAW_COMMANDS = (
    os.getenv("AGENT_LOG_RAW_COMMANDS", "true")
    .strip()
    .lower()
    in {"1", "true", "yes", "on"}
)


# ============================================================
# 1. Import Canonical Sales Logger
# ============================================================

SALES_LOGGER_IMPORT_ERROR: Exception | None = None

try:
    from sales_logger import (
        BOOKING_STATUSES,
        CHECK_STATUSES,
        EMERGENCY_CONTACT_STATUSES,
        EXPERIENCE_LEVELS,
        GEAR_CATEGORIES,
        OVERNIGHT_AREAS,
        PARK_STATUSES,
        RECOMMENDATION_LEVELS,
        RECORD_STATUSES,
        RENTAL_OR_PURCHASE,
        ROUTE_PLANS,
        TRANSPORTS,
        TRIP_TYPES,
        Y2_STATUSES,
        Y4_PLANS,
        log_sale,
    )
except Exception as exc:
    SALES_LOGGER_IMPORT_ERROR = exc

    # Fallback enums ทำให้ parse/checklist/dry-run ยังทำงานได้
    # แต่ log_sale จริงจะถูกบล็อกจนกว่า sales_logger.py พร้อม
    RECORD_STATUSES = {
        "confirmed": "ยืนยันรายการแล้ว",
        "pending": "รอยืนยัน",
        "cancelled": "ยกเลิก",
    }
    TRIP_TYPES = {
        "2d1n": "2 วัน 1 คืน",
        "day_hike": "ไปเช้าเย็นกลับ",
    }
    EXPERIENCE_LEVELS = {
        "beginner": "มือใหม่",
        "intermediate": "มีประสบการณ์",
        "advanced": "มีประสบการณ์สูง",
    }
    ROUTE_PLANS = {
        "office_y2": "ที่ทำการ → Y1 → Y2",
        "office_y4": "ที่ทำการ → Y1 → Y2 → Y3 → Y4",
        "station_y2": "สถานีรถไฟขุนตาน → ที่ทำการ → Y1 → Y2",
        "station_y4": "สถานีรถไฟขุนตาน → ที่ทำการ → Y1 → Y2 → Y3 → Y4",
    }
    OVERNIGHT_AREAS = {
        "y2": "Y2",
        "none": "ไม่พักค้างคืน",
        "other": "พื้นที่พักอื่นตามที่อุทยานเปิดให้บริการ",
    }
    Y4_PLANS = {
        "yes": "ขึ้น Y4",
        "no": "ไม่ขึ้น Y4",
    }
    TRANSPORTS = {
        "train": "รถไฟ - ลงสถานีรถไฟขุนตาน",
        "private_car": "รถส่วนตัว",
        "bus_van_plus_local": "รถบัส/รถตู้ + รถท้องถิ่น/รถรับจ้าง",
        "taxi_local": "รถรับจ้าง/แท็กซี่",
        "other": "อื่น ๆ",
    }
    BOOKING_STATUSES = {
        "not_checked": "ยังไม่ได้ตรวจสอบ",
        "checking": "กำลังตรวจสอบ",
        "booked": "จองแล้ว",
        "not_required": "ไม่ต้องจอง/ไม่พักค้างคืน",
    }
    PARK_STATUSES = {
        "unknown": "ยังไม่ได้ยืนยัน",
        "open_confirmed": "ยืนยันว่าเปิดแล้ว",
        "closed_confirmed": "ยืนยันว่าปิด",
    }
    Y2_STATUSES = {
        "unknown": "ยังไม่ได้ยืนยัน",
        "open_confirmed": "ยืนยันว่าเปิดแล้ว",
        "closed_confirmed": "ยืนยันว่าปิด",
        "not_applicable": "ไม่เกี่ยวข้อง",
    }
    CHECK_STATUSES = {
        "not_checked": "ยังไม่ได้ตรวจสอบ",
        "checked": "ตรวจสอบแล้ว",
        "not_applicable": "ไม่เกี่ยวข้อง",
    }
    EMERGENCY_CONTACT_STATUSES = {
        "not_checked": "ยังไม่ได้ยืนยัน",
        "confirmed": "แจ้งผู้ติดต่อฉุกเฉิน/คนที่บ้านแล้ว",
        "not_applicable": "ไม่เกี่ยวข้อง",
    }
    RECOMMENDATION_LEVELS = {
        "essential": "จำเป็นสำหรับแผนนี้",
        "recommended": "แนะนำ",
        "optional": "เสริม/ตามความเหมาะสม",
    }
    GEAR_CATEGORIES = {
        "backpack": "กระเป๋า",
        "footwear": "รองเท้า/ถุงเท้า",
        "shelter": "เต็นท์/ที่พัก",
        "sleep_system": "ถุงนอน/แผ่นรองนอน",
        "rain_gear": "อุปกรณ์กันฝน",
        "lighting": "ไฟฉาย/ไฟคาดหัว",
        "water": "น้ำ/อุปกรณ์ใส่น้ำ",
        "food": "อาหาร/พลังงาน",
        "first_aid": "ปฐมพยาบาล",
        "navigation": "แผนที่/การนำทาง",
        "trekking_pole": "Trekking Pole",
        "power": "Power Bank/พลังงาน",
        "clothing": "เสื้อผ้า",
        "emergency_safety": "อุปกรณ์ฉุกเฉิน/ความปลอดภัย",
        "other": "อื่น ๆ",
    }
    RENTAL_OR_PURCHASE = {
        "purchase": "ซื้อ",
        "rental": "เช่า",
    }
    log_sale = None


# ============================================================
# 2. KB Loading / Parsing
# ============================================================

def discover_kb_path() -> Path:
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

    canonical = BASE_DIR / "trekking_gear_kb.md"

    if canonical.exists():
        return canonical

    # รองรับกรณียังไม่ได้ rename ไฟล์ Master KB
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
        if "## 84." in sample or "**## 84." in sample:
            score += 4

        if score >= 7:
            candidates.append(
                (score, path)
            )

    if not candidates:
        raise FileNotFoundError(
            "ไม่พบ Master KB ดอยขุนตาล "
            "กรุณาวาง trekking_gear_kb.md "
            "ไว้โฟลเดอร์เดียวกับ agent_harness.py"
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
    รองรับ Master KB ที่ถูก escape เช่น
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


SECTION_RE = re.compile(
    r"(?m)^##\s+(\d+)\.\s+(.+?)\s*$"
)


@dataclass(frozen=True)
class KBSection:
    number: int
    title: str
    text: str


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


def get_kb_sections(
    numbers: Iterable[int],
) -> str:
    parts = []

    for number in numbers:
        section = KB_SECTIONS.get(
            number
        )
        if section:
            parts.append(section.text)

    return "\n\n---\n\n".join(parts)


# ============================================================
# 3. Agent Actions
# ============================================================

ACTION_LOG_SALE = "log_sale"
ACTION_CHECKLIST = "generate_checklist"
ACTION_SEND_ALERT = "send_alert"
ACTION_NONE = "no_action"

VALID_ACTIONS = {
    ACTION_LOG_SALE,
    ACTION_CHECKLIST,
    ACTION_SEND_ALERT,
    ACTION_NONE,
}


# ============================================================
# 4. Structured Output JSON Schema
# ============================================================

def enum_values(mapping: dict[str, str]) -> list[str]:
    return list(mapping.keys())


AGENT_DECISION_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": sorted(
                VALID_ACTIONS
            ),
            "description": (
                "เครื่องมือที่ควรใช้ หรือ no_action "
                "เมื่อเป็นเพียงคำถามข้อมูล"
            ),
        },
        "scope": {
            "type": "string",
            "enum": [
                "in_scope",
                "out_of_scope",
            ],
        },
        "explicit_confirmation": {
            "type": "boolean",
            "description": (
                "true เฉพาะเมื่อผู้ใช้ยืนยันซื้อ/เช่า "
                "หรือยืนยันให้ส่ง alert ชัดเจน"
            ),
        },
        "needs_confirmation": {
            "type": "boolean",
        },
        "reason": {
            "type": "string",
        },
        "missing_fields": {
            "type": "array",
            "items": {
                "type": "string"
            },
        },
        "args": {
            "type": "object",
            "properties": {
                # ---------- Sale ----------
                "record_status": {
                    "type": "string",
                    "enum": enum_values(
                        RECORD_STATUSES
                    ),
                },
                "trip_type": {
                    "type": "string",
                    "enum": enum_values(
                        TRIP_TYPES
                    ),
                },
                "experience_level": {
                    "type": "string",
                    "enum": enum_values(
                        EXPERIENCE_LEVELS
                    ),
                },
                "party_size": {
                    "type": "integer",
                    "minimum": 0,
                },
                "route_plan": {
                    "type": "string",
                    "enum": enum_values(
                        ROUTE_PLANS
                    ),
                },
                "overnight_area": {
                    "type": "string",
                    "enum": enum_values(
                        OVERNIGHT_AREAS
                    ),
                },
                "y4_plan": {
                    "type": "string",
                    "enum": enum_values(
                        Y4_PLANS
                    ),
                },
                "transport": {
                    "type": "string",
                    "enum": enum_values(
                        TRANSPORTS
                    ),
                },
                "booking_status": {
                    "type": "string",
                    "enum": enum_values(
                        BOOKING_STATUSES
                    ),
                },
                "park_status": {
                    "type": "string",
                    "enum": enum_values(
                        PARK_STATUSES
                    ),
                },
                "y2_status": {
                    "type": "string",
                    "enum": enum_values(
                        Y2_STATUSES
                    ),
                },
                "weather_check": {
                    "type": "string",
                    "enum": enum_values(
                        CHECK_STATUSES
                    ),
                },
                "water_check": {
                    "type": "string",
                    "enum": enum_values(
                        CHECK_STATUSES
                    ),
                },
                "emergency_contact_check": {
                    "type": "string",
                    "enum": enum_values(
                        EMERGENCY_CONTACT_STATUSES
                    ),
                },
                "recommendation_level": {
                    "type": "string",
                    "enum": enum_values(
                        RECOMMENDATION_LEVELS
                    ),
                },
                "gear_category": {
                    "type": "string",
                    "enum": enum_values(
                        GEAR_CATEGORIES
                    ),
                },
                "product_name": {
                    "type": "string",
                },
                "qty": {
                    "type": "integer",
                    "minimum": 1,
                },
                "price": {
                    "type": "number",
                    "minimum": 0,
                },
                "discount_percent": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 100,
                },
                "rental_or_purchase": {
                    "type": "string",
                    "enum": enum_values(
                        RENTAL_OR_PURCHASE
                    ),
                },
                "rental_days": {
                    "type": "integer",
                    "minimum": 0,
                },
                "notes": {
                    "type": "string",
                },

                # ---------- Checklist ----------
                "season": {
                    "type": "string",
                    "enum": [
                        "unspecified",
                        "hot",
                        "rainy",
                        "cool",
                    ],
                },

                # ---------- Alert ----------
                "message": {
                    "type": "string",
                },
            },
            "additionalProperties": False,
        },
    },
    "required": [
        "action",
        "scope",
        "explicit_confirmation",
        "needs_confirmation",
        "reason",
        "missing_fields",
        "args",
    ],
    "additionalProperties": False,
}


# ============================================================
# 5. Parser Prompt / Always-on Agent Guardrails
# ============================================================

PARSER_POLICY = """
คุณคือ Tool Router ของ Trekking & Camping Buddy

ขอบเขตระบบ:
- รองรับ "ดอยขุนตาล" เท่านั้น
- ห้ามสร้างรายละเอียดของอุทยาน/ภูเขาอื่น
- destination ไม่ใช่ argument เพราะระบบล็อกเป็นดอยขุนตาล
- ห้ามสร้าง field porter / ลูกหาบ

ACTIONS:

1) log_sale
ใช้เมื่อผู้ใช้ต้องการ "ซื้อ/เช่า/บันทึกรายการ" อุปกรณ์จริง

สำคัญ:
- explicit_confirmation=true เฉพาะเมื่อภาษาของผู้ใช้แสดงการยืนยันธุรกรรมจริง
  เช่น "ยืนยันซื้อ", "ซื้อเลย", "เอา 1 ชิ้น", "สั่งซื้อ",
       "ยืนยันเช่า", "เช่าเลย", "บันทึกการขาย..."
- ถ้าผู้ใช้แค่ถามว่า "น่าสนไหม", "ควรซื้อไหม", "ราคาเท่าไร",
  "ช่วยแนะนำ..." ให้ action=no_action
- ถ้าผู้ใช้ต้องการซื้อ/เช่าแต่ข้อมูลสำคัญไม่ครบ
  ให้ action=log_sale, needs_confirmation=true,
  execute ไม่ได้จนกว่าจะได้ข้อมูลครบ
- price ของสินค้าใช้เฉพาะตัวเลขที่ผู้ใช้/ระบบให้มา
  ห้ามเดาราคาจาก KB
- ห้ามใช้ราคาอุทยาน ค่าเช่าเต็นท์อุทยาน หรือค่าเดินทาง
  เป็น product price เว้นแต่คำสั่งระบุชัดว่าเป็นสินค้า/บริการที่กำลังบันทึก

Required สำหรับ log_sale:
- product_name
- qty
- price
- gear_category

Default ที่ปลอดภัยถ้าผู้ใช้ไม่บอก:
- record_status = confirmed เมื่อเป็นการยืนยันธุรกรรม
- trip_type = 2d1n
- experience_level = beginner
- party_size = 0 (ไม่ระบุ)
- route_plan = station_y4
- overnight_area = y2
- y4_plan = yes
- transport = train
- booking_status = not_checked
- park_status = unknown
- y2_status = unknown
- weather_check = not_checked
- water_check = not_checked
- emergency_contact_check = not_checked
- recommendation_level = recommended
- discount_percent = 0
- rental_or_purchase = purchase เว้นแต่ผู้ใช้พูดว่าเช่า
- rental_days = 0 สำหรับ purchase
- notes = "-"

ห้ามตั้ง:
park_status=open_confirmed
y2_status=open_confirmed
weather_check=checked
water_check=checked
เพียงเพราะ KB เคยมีข้อมูล
ค่าพวกนี้เป็น [DYNAMIC] และต้องมีคำสั่ง/ข้อมูลยืนยันจากระบบหรือผู้ใช้จริง

2) generate_checklist
ใช้เมื่อผู้ใช้ขอ:
- checklist
- รายการของที่ต้องเตรียม
- ของที่ต้องเอาไป Y2/Y4
- รายการเตรียมตัวก่อนทริป

ไม่ต้องมี confirmation
destination ถูกล็อกเป็นดอยขุนตาล

3) send_alert
ใช้เมื่อผู้ใช้สั่งให้ "ส่งข้อความ/แจ้งเตือน Telegram"
ต้องมี message
explicit_confirmation=true เมื่อผู้ใช้สั่งให้ส่งจริง

4) no_action
ใช้เมื่อ:
- เป็นคำถามทั่วไป
- ขอคำแนะนำ
- เปรียบเทียบสินค้า
- ถามข้อมูล KB
- คำถามอยู่นอกขอบเขต
- ยังไม่มีเหตุให้เรียก tool

OUT OF SCOPE:
ถ้าผู้ใช้ขอทำรายการ/Checklist สำหรับภูกระดึง ภูสอยดาว ดอยอินทนนท์
เขาหลวงสุโขทัย ดอยหลวงเชียงดาว หรือสถานที่อื่น
ให้ scope=out_of_scope และ action=no_action

ห้ามเดาข้อมูลที่ผู้ใช้ไม่ได้ให้ โดยเฉพาะราคา สถานะเปิด/ปิด
อากาศ น้ำ รถไฟ และข้อมูล Dynamic
"""


# ============================================================
# 6. Gemini Client
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
        api_key=get_api_key(api_key)
    )


# ============================================================
# 7. Parse Thai Command -> Structured Decision
# ============================================================

def parse_command(
    cmd: str,
    api_key: str | None = None,
) -> dict[str, Any]:
    """
    ใช้ Gemini Structured Output
    ไม่ใช้ markdown-code-fence stripping แบบเดิม
    """

    command = cmd.strip()

    if not command:
        raise ValueError(
            "คำสั่งว่างเปล่า"
        )

    client = create_client(
        api_key
    )

    prompt = f"""
{PARSER_POLICY}

คำสั่งจากผู้ใช้:
<user_command>
{command}
</user_command>

วิเคราะห์เจตนาและคืนข้อมูลให้ตรง JSON Schema เท่านั้น
""".strip()

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0,
                response_mime_type="application/json",
                response_json_schema=AGENT_DECISION_SCHEMA,
            ),
        )
    except Exception as exc:
        raise RuntimeError(
            f"Gemini parse failed: {exc}"
        ) from exc

    if not getattr(
        response,
        "text",
        None,
    ):
        raise RuntimeError(
            "Gemini ไม่คืน Structured Output"
        )

    try:
        decision = json.loads(
            response.text
        )
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Structured Output ไม่ใช่ JSON ที่ถูกต้อง"
        ) from exc

    return normalize_decision(
        decision
    )


# ============================================================
# 8. Local Confirmation / Scope Guard
# ============================================================

OUT_OF_SCOPE_TERMS = (
    "ภูกระดึง",
    "ภูสอยดาว",
    "ดอยอินทนนท์",
    "อินทนนท์",
    "ดอยหลวงเชียงดาว",
    "เชียงดาว",
    "เขาหลวงสุโขทัย",
    "เขาหลวง",
    "ม่อนจอง",
    "ดอยม่อนจอง",
    "ดอยผ้าห่มปก",
    "ภูชี้ฟ้า",
)

# ต้อง conservative เพื่อป้องกันบันทึก sale โดยไม่ได้ตั้งใจ
STRONG_PURCHASE_PATTERNS = (
    r"ยืนยัน\s*ซื้อ",
    r"ซื้อ\s*เลย",
    r"สั่ง\s*ซื้อ",
    r"ตกลง\s*ซื้อ",
    r"บันทึก.{0,20}(ซื้อ|ขาย|รายการ)",
    r"เอา.{0,20}\d+\s*(ชิ้น|อัน|ใบ|คู่|ชุด)",
)

STRONG_RENTAL_PATTERNS = (
    r"ยืนยัน\s*เช่า",
    r"เช่า\s*เลย",
    r"ตกลง\s*เช่า",
    r"บันทึก.{0,20}(เช่า|รายการเช่า)",
)

ALERT_CONFIRM_PATTERNS = (
    r"ส่ง.{0,20}(telegram|เทเลแกรม|แจ้งเตือน|ข้อความ)",
    r"แจ้งเตือน.{0,20}(เลย|ให้|ตอนนี้)",
)


def local_scope_check(
    cmd: str,
) -> bool:
    """
    True = อยู่ใน scope หรือไม่มีชื่อพื้นที่อื่นชัดเจน
    False = พบสถานที่อื่นที่รู้จัก
    """

    lowered = cmd.lower()

    if any(
        term.lower() in lowered
        for term in OUT_OF_SCOPE_TERMS
    ):
        # ถ้า user พูดถึงพื้นที่อื่นเพียงเพื่อบอกว่า "ไม่เอา..."
        # model scope ยังช่วยอีกชั้น แต่ local guard เลือก conservative
        return False

    return True


def matches_any_pattern(
    text: str,
    patterns: Iterable[str],
) -> bool:
    return any(
        re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )
        for pattern in patterns
    )


def local_transaction_confirmation(
    cmd: str,
    rental_or_purchase: str,
) -> bool:
    """
    Local gate สำคัญ:
    Model บอก confirmed อย่างเดียวไม่พอ
    ต้องมีภาษายืนยันในข้อความผู้ใช้ด้วย
    """

    if rental_or_purchase == "rental":
        return matches_any_pattern(
            cmd,
            STRONG_RENTAL_PATTERNS,
        )

    return matches_any_pattern(
        cmd,
        STRONG_PURCHASE_PATTERNS,
    )


def local_alert_confirmation(
    cmd: str,
) -> bool:
    return matches_any_pattern(
        cmd,
        ALERT_CONFIRM_PATTERNS,
    )


# ============================================================
# 9. Normalize / Validate Agent Decision
# ============================================================

DEFAULT_SALE_ARGS = {
    "record_status": "confirmed",
    "trip_type": "2d1n",
    "experience_level": "beginner",
    "party_size": 0,
    "route_plan": "station_y4",
    "overnight_area": "y2",
    "y4_plan": "yes",
    "transport": "train",
    "booking_status": "not_checked",
    "park_status": "unknown",
    "y2_status": "unknown",
    "weather_check": "not_checked",
    "water_check": "not_checked",
    "emergency_contact_check": "not_checked",
    "recommendation_level": "recommended",
    "discount_percent": 0,
    "rental_or_purchase": "purchase",
    "rental_days": 0,
    "notes": "-",
}

DEFAULT_CHECKLIST_ARGS = {
    "trip_type": "2d1n",
    "experience_level": "beginner",
    "party_size": 0,
    "route_plan": "station_y4",
    "overnight_area": "y2",
    "y4_plan": "yes",
    "season": "unspecified",
}


def normalize_decision(
    decision: dict[str, Any],
) -> dict[str, Any]:
    action = str(
        decision.get(
            "action",
            ACTION_NONE,
        )
    )

    if action not in VALID_ACTIONS:
        action = ACTION_NONE

    scope = str(
        decision.get(
            "scope",
            "in_scope",
        )
    )

    if scope not in {
        "in_scope",
        "out_of_scope",
    }:
        scope = "in_scope"

    args = decision.get(
        "args"
    )

    if not isinstance(args, dict):
        args = {}

    normalized = {
        "action": action,
        "scope": scope,
        "explicit_confirmation": bool(
            decision.get(
                "explicit_confirmation",
                False,
            )
        ),
        "needs_confirmation": bool(
            decision.get(
                "needs_confirmation",
                False,
            )
        ),
        "reason": str(
            decision.get(
                "reason",
                "",
            )
        ).strip(),
        "missing_fields": [
            str(item)
            for item in decision.get(
                "missing_fields",
                [],
            )
            if str(item).strip()
        ],
        "args": args,
    }

    return normalized


def validate_enum(
    field_name: str,
    value: Any,
    mapping: dict[str, str],
) -> str:
    value = str(value)

    if value not in mapping:
        raise ValueError(
            f"{field_name}='{value}' ไม่ถูกต้อง "
            f"เลือกได้: {', '.join(mapping.keys())}"
        )

    return value


def normalize_sale_args(
    raw_args: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    """
    เติม safe defaults และคืน missing required fields
    """

    args = {
        **DEFAULT_SALE_ARGS,
        **raw_args,
    }

    required = [
        "product_name",
        "qty",
        "price",
        "gear_category",
    ]

    missing = []

    for field in required:
        value = args.get(field)

        if value in (
            None,
            "",
        ):
            missing.append(field)

    if "qty" not in missing:
        try:
            args["qty"] = int(
                args["qty"]
            )
        except (
            TypeError,
            ValueError,
        ):
            missing.append("qty")
        else:
            if args["qty"] <= 0:
                missing.append("qty")

    if "price" not in missing:
        try:
            args["price"] = float(
                args["price"]
            )
        except (
            TypeError,
            ValueError,
        ):
            missing.append("price")
        else:
            if args["price"] < 0:
                missing.append("price")

    try:
        args["party_size"] = int(
            args.get(
                "party_size",
                0,
            )
        )
    except (
        TypeError,
        ValueError,
    ):
        args["party_size"] = 0

    try:
        args["discount_percent"] = float(
            args.get(
                "discount_percent",
                0,
            )
        )
    except (
        TypeError,
        ValueError,
    ):
        args["discount_percent"] = 0

    try:
        args["rental_days"] = int(
            args.get(
                "rental_days",
                0,
            )
        )
    except (
        TypeError,
        ValueError,
    ):
        args["rental_days"] = 0

    enum_fields = [
        (
            "record_status",
            RECORD_STATUSES,
        ),
        (
            "trip_type",
            TRIP_TYPES,
        ),
        (
            "experience_level",
            EXPERIENCE_LEVELS,
        ),
        (
            "route_plan",
            ROUTE_PLANS,
        ),
        (
            "overnight_area",
            OVERNIGHT_AREAS,
        ),
        (
            "y4_plan",
            Y4_PLANS,
        ),
        (
            "transport",
            TRANSPORTS,
        ),
        (
            "booking_status",
            BOOKING_STATUSES,
        ),
        (
            "park_status",
            PARK_STATUSES,
        ),
        (
            "y2_status",
            Y2_STATUSES,
        ),
        (
            "weather_check",
            CHECK_STATUSES,
        ),
        (
            "water_check",
            CHECK_STATUSES,
        ),
        (
            "emergency_contact_check",
            EMERGENCY_CONTACT_STATUSES,
        ),
        (
            "recommendation_level",
            RECOMMENDATION_LEVELS,
        ),
        (
            "gear_category",
            GEAR_CATEGORIES,
        ),
        (
            "rental_or_purchase",
            RENTAL_OR_PURCHASE,
        ),
    ]

    for field_name, mapping in enum_fields:
        if field_name == "gear_category" and field_name in missing:
            continue

        args[field_name] = validate_enum(
            field_name,
            args[field_name],
            mapping,
        )

    # Purchase / rental consistency
    if (
        args["rental_or_purchase"]
        == "purchase"
    ):
        args["rental_days"] = 0

    elif args["rental_days"] <= 0:
        missing.append(
            "rental_days"
        )

    # dedupe
    missing = list(
        dict.fromkeys(missing)
    )

    allowed = {
        "product_name",
        "qty",
        "price",
        "gear_category",
        *DEFAULT_SALE_ARGS.keys(),
    }

    cleaned = {
        key: value
        for key, value in args.items()
        if key in allowed
    }

    return cleaned, missing


def normalize_checklist_args(
    raw_args: dict[str, Any],
) -> dict[str, Any]:
    args = {
        **DEFAULT_CHECKLIST_ARGS,
        **raw_args,
    }

    args["trip_type"] = validate_enum(
        "trip_type",
        args["trip_type"],
        TRIP_TYPES,
    )

    args["experience_level"] = validate_enum(
        "experience_level",
        args["experience_level"],
        EXPERIENCE_LEVELS,
    )

    args["route_plan"] = validate_enum(
        "route_plan",
        args["route_plan"],
        ROUTE_PLANS,
    )

    args["overnight_area"] = validate_enum(
        "overnight_area",
        args["overnight_area"],
        OVERNIGHT_AREAS,
    )

    args["y4_plan"] = validate_enum(
        "y4_plan",
        args["y4_plan"],
        Y4_PLANS,
    )

    try:
        args["party_size"] = max(
            0,
            int(
                args.get(
                    "party_size",
                    0,
                )
            ),
        )
    except (
        TypeError,
        ValueError,
    ):
        args["party_size"] = 0

    season = str(
        args.get(
            "season",
            "unspecified",
        )
    )

    if season not in {
        "unspecified",
        "hot",
        "rainy",
        "cool",
    }:
        season = "unspecified"

    args["season"] = season

    return args


# ============================================================
# 10. Local Checklist Generator
# ============================================================

def add_unique(
    target: list[str],
    *items: str,
):
    for item in items:
        if item not in target:
            target.append(item)


def generate_checklist(
    *,
    trip_type: str = "2d1n",
    experience_level: str = "beginner",
    party_size: int = 0,
    route_plan: str = "station_y4",
    overnight_area: str = "y2",
    y4_plan: str = "yes",
    season: str = "unspecified",
) -> dict[str, Any]:
    """
    Checklist deterministic:
    ทำให้ tool ใช้งานได้แม้ไม่เรียก Gemini รอบที่สอง
    และสอดคล้องกับ Sections:
    25-40, 45-49, 53, 58-61, 69-71, 83
    """

    carry: list[str] = []
    camp: list[str] = []
    y4: list[str] = []
    emergency: list[str] = []
    before_trip: list[str] = []
    optional: list[str] = []
    warnings: list[str] = []

    # ---------- ของติดตัว ----------
    add_unique(
        carry,
        "รองเท้าที่พื้นยึดเกาะดีและเคยใช้งานแล้ว",
        "ถุงเท้าสำรอง",
        "เสื้อผ้าแห้งเร็ว",
        "เสื้อกันฝน/poncho",
        "ถุงกันน้ำสำหรับของสำคัญ",
        "น้ำและภาชนะใส่น้ำ",
        "อาหาร/ขนมให้พลังงาน",
        "โทรศัพท์",
        "Power bank ที่เก็บกันน้ำ",
        "แผนที่ Offline",
        "ชุดปฐมพยาบาลขนาดเล็ก",
        "ยาประจำตัวของผู้ใช้",
        "บัตรประชาชน/หลักฐานที่จำเป็น",
        "เงินสดสำรอง",
        "ถุงขยะ",
    )

    add_unique(
        optional,
        "Trekking Pole โดยเฉพาะช่วงลงหรือทางลื่น",
    )

    # ---------- ค้างคืน ----------
    if trip_type == "2d1n":
        add_unique(
            camp,
            "เต็นท์หรือยืนยันบริการเต็นท์ล่าสุดกับอุทยาน",
            "แผ่นรองนอน",
            "ถุงนอน/ผ้าห่มตามสภาพอากาศ",
            "ชุดแห้งสำหรับนอน",
        )

        if overnight_area == "y2":
            add_unique(
                before_trip,
                "ยืนยันว่า Y2 เปิดให้พักในวันเดินทาง",
                "ตรวจสถานะน้ำและห้องน้ำ Y2 ล่าสุด",
                "ตรวจเงื่อนไขการจองพื้นที่พัก/เต็นท์",
            )

    # ---------- Y4 ----------
    if y4_plan == "yes":
        add_unique(
            y4,
            "Daypack ใบเล็ก",
            "น้ำประมาณ 1–1.5 ลิตร แล้วปรับตามอากาศ/ร่างกาย",
            "ขนมให้พลังงาน",
            "ไฟฉายคาดหัว",
            "แบตเตอรี่/ไฟสำรอง",
            "โทรศัพท์",
            "Power bank",
            "เสื้อกันลม",
            "เสื้อกันฝน",
            "ปฐมพยาบาลเล็กน้อย",
        )

        add_unique(
            before_trip,
            "ตรวจสถานะเส้นทาง Y3–Y4 กับเจ้าหน้าที่",
            "ตรวจพยากรณ์อากาศและเวลาพระอาทิตย์ขึ้นล่าสุด",
        )

        warnings.append(
            "การออกจาก Y2 ไป Y4 เช้ามืดต้องใช้ไฟฉายคาดหัว "
            "และไม่ควรพึ่งแฟลชโทรศัพท์เป็นไฟหลัก"
        )

    # ---------- Season ----------
    if season == "rainy":
        add_unique(
            carry,
            "Rain cover กระเป๋า + ถุงกันน้ำด้านใน",
            "ถุงเท้าแห้งสำรอง",
            "อุปกรณ์ป้องกันทาก/แมลงตามความเหมาะสม",
        )
        warnings.append(
            "ฤดูฝนต้องเผื่อทางลื่น โคลน เสื้อผ้าเปียก "
            "และสถานะเส้นทางที่อาจเปลี่ยน"
        )

    elif season == "cool":
        add_unique(
            carry,
            "เสื้อเก็บความอุ่นน้ำหนักเบา เช่น fleece",
            "หมวกบาง/ผ้าบัฟถ้าเป็นคนขี้หนาว",
        )
        warnings.append(
            "อุณหภูมิจริงเป็นข้อมูล Dynamic "
            "ต้องตรวจพยากรณ์ล่าสุดก่อนเดินทาง"
        )

    elif season == "hot":
        warnings.append(
            "อากาศร้อนทำให้ความต้องการน้ำเพิ่มขึ้น "
            "ควรปรับน้ำตามอุณหภูมิ เหงื่อ และคำแนะนำเจ้าหน้าที่"
        )

    # ---------- Solo ----------
    if party_size == 1:
        add_unique(
            emergency,
            "แจ้งแผนทริปและเวลาคาดว่าจะกลับให้คนที่บ้าน",
            "กำหนดเวลา Check-in",
            "กำหนดแผนเมื่อขาดการติดต่อ",
            "บันทึกช่องทางติดต่อฉุกเฉินแบบ Offline",
        )

        warnings.append(
            "สำหรับมือใหม่ KB ไม่แนะนำให้ดอยขุนตาลเป็น Solo ครั้งแรก"
        )

    else:
        add_unique(
            emergency,
            "แจ้งคนที่บ้านว่ากลุ่มเดินวันไหน นอนที่ใด และคาดว่าจะกลับเมื่อไร",
        )

    add_unique(
        emergency,
        "โหลดแผนที่ Offline",
        "เก็บหมายเลข/ข้อมูลฉุกเฉินไว้แบบ Offline",
        "อย่าแยกจากกลุ่มช่วงเดินกลางคืน",
    )

    # ---------- Before trip ----------
    add_unique(
        before_trip,
        "ตรวจประกาศเปิด/ปิดอุทยานล่าสุด",
        "ตรวจการจอง",
        "ตรวจตั๋ว/แผนการเดินทางล่าสุด",
        "ตรวจพยากรณ์อากาศล่าสุด",
        "ชาร์จโทรศัพท์และ Power bank",
        "ทดลองไฟฉาย",
        "ตรวจรองเท้า",
        "ตรวจ Rain gear",
        "เตรียมน้ำและอาหาร",
        "แจ้งคนที่บ้าน",
    )

    if route_plan.startswith("station_"):
        add_unique(
            before_trip,
            "เผื่อเวลารถไฟขากลับ ไม่จองกระชั้นกับเวลาลงเขา",
        )

    # Section traceability
    source_sections = [
        "25-40",
        "45-49",
        "53",
        "58-61",
        "69-71",
    ]

    if party_size == 1:
        source_sections.append(
            "83"
        )

    return {
        "destination": DESTINATION,
        "trip_type": trip_type,
        "experience_level": experience_level,
        "party_size": party_size,
        "route_plan": route_plan,
        "overnight_area": overnight_area,
        "y4_plan": y4_plan,
        "season": season,
        "checklist": {
            "carry": carry,
            "camp": camp,
            "y4_daypack": y4,
            "emergency": emergency,
            "before_trip": before_trip,
            "optional": optional,
        },
        "warnings": warnings,
        "kb_sections": source_sections,
        "dynamic_disclaimer": (
            "สถานะเปิด/ปิด Y2/Y4 น้ำ ห้องน้ำ ราคา "
            "รถไฟ อากาศ และกฎเฉพาะช่วงต้องตรวจล่าสุด"
        ),
    }


def checklist_to_text(
    result: dict[str, Any],
) -> str:
    labels = {
        "carry": "ของที่พกติดตัว",
        "camp": "ของสำหรับพักค้างคืน",
        "y4_daypack": "ของสำหรับขึ้น Y4",
        "emergency": "ความปลอดภัย/ฉุกเฉิน",
        "before_trip": "ตรวจสอบก่อนออกเดินทาง",
        "optional": "อุปกรณ์เสริม",
    }

    lines = [
        "Checklist ดอยขุนตาล",
        f"ทริป: {result['trip_type']}",
        f"Y4: {result['y4_plan']}",
        "",
    ]

    for key, title in labels.items():
        items = result[
            "checklist"
        ].get(
            key,
            [],
        )

        if not items:
            continue

        lines.append(
            f"## {title}"
        )

        for item in items:
            lines.append(
                f"- {item}"
            )

        lines.append("")

    if result["warnings"]:
        lines.append(
            "## ข้อควรระวัง"
        )

        for warning in result["warnings"]:
            lines.append(
                f"- {warning}"
            )

        lines.append("")

    lines.append(
        "หมายเหตุ: "
        + result["dynamic_disclaimer"]
    )

    return "\n".join(lines)


# ============================================================
# 11. Telegram Alert
# ============================================================

def send_alert(
    message: str,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    message = str(message).strip()

    if not message:
        raise ValueError(
            "message ห้ามว่าง"
        )

    if dry_run:
        return {
            "sent": False,
            "dry_run": True,
            "message": message,
        }

    if requests is None:
        raise RuntimeError(
            "ยังไม่ได้ติดตั้ง requests "
            "กรุณารัน: pip install requests"
        )

    token = os.getenv(
        "TELEGRAM_BOT_TOKEN"
    )
    chat_id = os.getenv(
        "TELEGRAM_CHAT_ID"
    )

    if not token or not chat_id:
        raise RuntimeError(
            "ไม่พบ TELEGRAM_BOT_TOKEN "
            "หรือ TELEGRAM_CHAT_ID"
        )

    url = (
        "https://api.telegram.org/bot"
        f"{token}/sendMessage"
    )

    payload = {
        "chat_id": chat_id,
        "text": (
            "🏕️ [Trekking & Camping Buddy]\n"
            + message[:3800]
        ),
    }

    response = requests.post(
        url,
        json=payload,
        timeout=15,
    )

    response.raise_for_status()

    return {
        "sent": True,
        "dry_run": False,
        "status_code": response.status_code,
    }


# ============================================================
# 12. Tool Dispatcher
# ============================================================

def dispatch_tool(
    decision: dict[str, Any],
    *,
    original_command: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Model decision ไม่ถูก trust 100%
    ทุก side-effect ผ่าน local guard อีกครั้ง
    """

    action = decision[
        "action"
    ]

    # ---------- Scope ----------
    model_in_scope = (
        decision["scope"]
        == "in_scope"
    )

    local_in_scope = local_scope_check(
        original_command
    )

    if not model_in_scope or not local_in_scope:
        return {
            "ok": True,
            "executed": False,
            "action": ACTION_NONE,
            "status": "out_of_scope",
            "message": (
                "ระบบนี้รองรับเฉพาะการเดินป่าและอุปกรณ์ "
                "สำหรับดอยขุนตาลเท่านั้นครับ"
            ),
        }

    # ---------- No action ----------
    if action == ACTION_NONE:
        return {
            "ok": True,
            "executed": False,
            "action": ACTION_NONE,
            "status": "no_tool_needed",
            "message": (
                decision.get("reason")
                or "คำสั่งนี้ยังไม่จำเป็นต้องเรียก Tool"
            ),
        }

    # ---------- Checklist ----------
    if action == ACTION_CHECKLIST:
        args = normalize_checklist_args(
            decision.get(
                "args",
                {},
            )
        )

        result = generate_checklist(
            **args
        )

        return {
            "ok": True,
            "executed": True,
            "action": ACTION_CHECKLIST,
            "status": (
                "dry_run"
                if dry_run
                else "completed"
            ),
            "result": result,
            "message": checklist_to_text(
                result
            ),
        }

    # ---------- Alert ----------
    if action == ACTION_SEND_ALERT:
        message = str(
            decision.get(
                "args",
                {},
            ).get(
                "message",
                "",
            )
        ).strip()

        model_confirmed = bool(
            decision.get(
                "explicit_confirmation",
                False,
            )
        )

        local_confirmed = local_alert_confirmation(
            original_command
        )

        if (
            not model_confirmed
            or not local_confirmed
        ):
            return {
                "ok": True,
                "executed": False,
                "action": ACTION_SEND_ALERT,
                "status": "needs_confirmation",
                "message": (
                    "ยังไม่ได้ส่ง Telegram ครับ "
                    "กรุณายืนยันให้ชัดเจนว่าต้องการส่งข้อความ"
                ),
            }

        if not message:
            return {
                "ok": True,
                "executed": False,
                "action": ACTION_SEND_ALERT,
                "status": "missing_fields",
                "missing_fields": [
                    "message"
                ],
                "message": (
                    "ยังส่งไม่ได้เพราะไม่มีข้อความที่จะส่งครับ"
                ),
            }

        result = send_alert(
            message,
            dry_run=dry_run,
        )

        return {
            "ok": True,
            "executed": not dry_run,
            "action": ACTION_SEND_ALERT,
            "status": (
                "dry_run"
                if dry_run
                else "completed"
            ),
            "result": result,
            "message": (
                "DRY RUN: ยังไม่ได้ส่ง Telegram"
                if dry_run
                else "ส่ง Telegram สำเร็จแล้วครับ"
            ),
        }

    # ---------- Sale ----------
    if action == ACTION_LOG_SALE:
        sale_args, missing = normalize_sale_args(
            decision.get(
                "args",
                {},
            )
        )

        rental_or_purchase = sale_args.get(
            "rental_or_purchase",
            "purchase",
        )

        model_confirmed = bool(
            decision.get(
                "explicit_confirmation",
                False,
            )
        )

        local_confirmed = local_transaction_confirmation(
            original_command,
            rental_or_purchase,
        )

        # Merge model missing fields + local validation
        missing = list(
            dict.fromkeys(
                [
                    *decision.get(
                        "missing_fields",
                        [],
                    ),
                    *missing,
                ]
            )
        )

        if missing:
            return {
                "ok": True,
                "executed": False,
                "action": ACTION_LOG_SALE,
                "status": "missing_fields",
                "missing_fields": missing,
                "message": (
                    "ยังไม่บันทึกรายการครับ "
                    "เพราะข้อมูลยังไม่ครบ: "
                    + ", ".join(missing)
                ),
                "preview_args": sale_args,
            }

        if (
            not model_confirmed
            or not local_confirmed
            or decision.get(
                "needs_confirmation",
                False,
            )
        ):
            return {
                "ok": True,
                "executed": False,
                "action": ACTION_LOG_SALE,
                "status": "needs_confirmation",
                "message": (
                    "ผมยังไม่บันทึกลง Google Sheet ครับ "
                    "เพราะยังไม่พบการยืนยันซื้อ/เช่าที่ชัดเจน "
                    "กรุณาพูดเช่น "
                    "'ยืนยันซื้อไฟฉายคาดหัว 1 ชิ้น ราคา 590 บาท'"
                ),
                "preview_args": sale_args,
            }

        if SALES_LOGGER_IMPORT_ERROR is not None or log_sale is None:
            raise RuntimeError(
                "ไม่สามารถ import sales_logger.py ได้: "
                f"{SALES_LOGGER_IMPORT_ERROR}"
            )

        record = log_sale(
            **sale_args,
            write_sheet=not dry_run,
            notify_telegram=not dry_run,
        )

        return {
            "ok": True,
            "executed": not dry_run,
            "action": ACTION_LOG_SALE,
            "status": (
                "dry_run"
                if dry_run
                else "completed"
            ),
            "record": record,
            "message": (
                (
                    "DRY RUN ผ่านครับ "
                    f"รายการ {record['product_name']} "
                    f"ยอดรวม {record['total']:.2f} บาท "
                    "ยังไม่ได้เขียน Google Sheet/Telegram"
                )
                if dry_run
                else (
                    f"บันทึก {record['product_name']} "
                    f"จำนวน {record['qty']} ชิ้น "
                    f"ยอดรวม {record['total']:.2f} บาท "
                    "เรียบร้อยแล้วครับ"
                )
            ),
        }

    raise ValueError(
        f"Unknown action: {action}"
    )


# ============================================================
# 13. Trace Log (JSONL)
# ============================================================

def bangkok_now_iso() -> str:
    return datetime.now(
        ZoneInfo(
            "Asia/Bangkok"
        )
    ).isoformat(
        timespec="seconds"
    )


def safe_trace_command(
    command: str,
) -> str:
    if LOG_RAW_COMMANDS:
        return command[:4000]

    return "[raw command logging disabled]"


def write_trace(
    *,
    command: str,
    decision: dict[str, Any] | None,
    result: dict[str, Any] | None,
    error: str | None = None,
) -> None:
    event = {
        "timestamp": bangkok_now_iso(),
        "app": APP_NAME,
        "destination": DESTINATION,
        "kb_file": (
            KB_PATH.name
            if KB_PATH
            else None
        ),
        "model": GEMINI_MODEL,
        "command": safe_trace_command(
            command
        ),
        "decision": decision,
        "result": result,
        "error": error,
    }

    try:
        TRACE_FILE.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with TRACE_FILE.open(
            "a",
            encoding="utf-8",
        ) as file:
            file.write(
                json.dumps(
                    event,
                    ensure_ascii=False,
                    default=str,
                )
                + "\n"
            )

    except Exception as exc:
        print(
            f"[Warning] เขียน trace ไม่สำเร็จ: {exc}",
            file=sys.stderr,
        )


# ============================================================
# 14. Human-readable CLI Output
# ============================================================

def print_decision(
    decision: dict[str, Any],
) -> None:
    print(
        "[AGENT] "
        f"action={decision['action']} "
        f"scope={decision['scope']} "
        f"confirmed={decision['explicit_confirmation']} "
        f"needs_confirmation={decision['needs_confirmation']}"
    )

    if decision.get(
        "reason"
    ):
        print(
            "[AGENT] reason="
            + decision["reason"]
        )

    if decision.get(
        "missing_fields"
    ):
        print(
            "[AGENT] missing="
            + ", ".join(
                decision[
                    "missing_fields"
                ]
            )
        )


def print_result(
    result: dict[str, Any],
) -> None:
    message = result.get(
        "message",
        ""
    )

    if message:
        print(
            f"[RESULT] {message}"
        )

    if (
        result.get("action")
        == ACTION_CHECKLIST
        and message
    ):
        # Checklist มี multiline อยู่แล้ว
        pass


# ============================================================
# 15. Public API สำหรับ app.py / tests
# ============================================================

def run_agent(
    command: str,
    *,
    api_key: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    ฟังก์ชันหลักสำหรับ import ไปใช้จาก Python อื่น

    Example:
        from agent_harness import run_agent

        result = run_agent(
            "ยืนยันซื้อไฟฉายคาดหัว 1 ชิ้น ราคา 590 บาท",
            dry_run=True,
        )
    """

    decision = None
    result = None

    try:
        decision = parse_command(
            command,
            api_key=api_key,
        )

        result = dispatch_tool(
            decision,
            original_command=command,
            dry_run=dry_run,
        )

        write_trace(
            command=command,
            decision=decision,
            result=result,
        )

        return {
            "ok": True,
            "decision": decision,
            "result": result,
        }

    except Exception as exc:
        write_trace(
            command=command,
            decision=decision,
            result=result,
            error=str(exc),
        )

        raise


# ============================================================
# 16. Self-check
# ============================================================

def self_check() -> dict[str, Any]:
    checks = {
        "kb_found": KB_PATH is not None,
        "kb_sections": len(
            KB_SECTIONS
        ),
        "kb_has_section_67": (
            67 in KB_SECTIONS
        ),
        "kb_has_section_84": (
            84 in KB_SECTIONS
        ),
        "sales_logger_imported": (
            SALES_LOGGER_IMPORT_ERROR
            is None
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
        "telegram_configured": bool(
            os.getenv(
                "TELEGRAM_BOT_TOKEN"
            )
            and os.getenv(
                "TELEGRAM_CHAT_ID"
            )
        ),
        "trace_file": str(
            TRACE_FILE
        ),
        "model": GEMINI_MODEL,
    }

    checks["ready_for_parse"] = (
        checks[
            "google_genai_installed"
        ]
        and checks[
            "api_key_found"
        ]
    )

    checks["ready_for_sales"] = (
        checks[
            "sales_logger_imported"
        ]
    )

    return checks


# ============================================================
# 17. CLI
# ============================================================

def parse_cli_args():
    parser = argparse.ArgumentParser(
        description=(
            "Trekking & Camping Buddy Agent Harness "
            "- ดอยขุนตาลเท่านั้น"
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--cmd",
        type=str,
        help="คำสั่งภาษาไทย",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "ทดสอบ Agent โดยไม่เขียน Google Sheet "
            "และไม่ส่ง Telegram"
        ),
    )

    parser.add_argument(
        "--json-output",
        action="store_true",
        help="พิมพ์ผลลัพธ์ทั้งหมดเป็น JSON",
    )

    parser.add_argument(
        "--self-check",
        action="store_true",
        help="ตรวจ config/KB/dependencies โดยไม่เรียก Gemini",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_cli_args()

    if args.self_check:
        report = self_check()

        print(
            json.dumps(
                report,
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        )

        return 0

    if not args.cmd:
        print(
            "❌ ต้องระบุ --cmd "
            "หรือใช้ --self-check",
            file=sys.stderr,
        )
        return 2

    command = args.cmd.strip()

    if not command:
        print(
            "❌ --cmd ห้ามว่าง",
            file=sys.stderr,
        )
        return 2

    decision = None
    result = None

    try:
        if not args.json_output:
            print(
                f"[USER] {command}"
            )

        decision = parse_command(
            command
        )

        if not args.json_output:
            print_decision(
                decision
            )

        result = dispatch_tool(
            decision,
            original_command=command,
            dry_run=args.dry_run,
        )

        write_trace(
            command=command,
            decision=decision,
            result=result,
        )

        output = {
            "ok": True,
            "decision": decision,
            "result": result,
        }

        if args.json_output:
            print(
                json.dumps(
                    output,
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                )
            )
        else:
            print_result(
                result
            )

        return 0

    except Exception as exc:
        write_trace(
            command=command,
            decision=decision,
            result=result,
            error=str(exc),
        )

        if args.json_output:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "error": str(exc),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                file=sys.stderr,
            )
        else:
            print(
                f"[ERROR] {exc}",
                file=sys.stderr,
            )

        return 1


if __name__ == "__main__":
    sys.exit(
        main()
    )
