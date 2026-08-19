"""
Trekking & Camping Buddy - Sales Logger
========================================
Sales / Rental Logger สำหรับ Chatbot นักเดินป่ามือใหม่
ขอบเขต: อุทยานแห่งชาติดอยขุนตาลเท่านั้น

Master Knowledge Base:
    trekking_gear_kb.md
    (Doi Khun Tan Hiking & Overnight Knowledge Base)

แนวคิดการออกแบบ:
- Sales Logger ไม่ทำสำเนา KB ทั้งไฟล์
- เก็บเฉพาะ "ข้อมูลธุรกรรม + บริบททริป + สถานะตรวจข้อมูล Dynamic"
- ผูกหมวดอุปกรณ์เข้ากับ Section ของ KB เพื่อ trace/debug ได้
- ไม่เดาข้อมูลสด เช่น สถานะเปิด/ปิด ราคาอุทยาน น้ำ อากาศ หรือรถไฟ
- สร้าง Safety Flags จากบริบท แต่ไม่วินิจฉัยสุขภาพผู้ใช้
- รองรับทั้งการ import เป็น Python function และการเรียกผ่าน Command Line

Environment Variables:
    GOOGLE_SHEETS_CREDENTIALS       Service Account JSON แบบ string
    GOOGLE_SHEETS_CREDENTIALS_FILE  หรือ path ไปยังไฟล์ Service Account JSON
    GOOGLE_SHEET_ID                 แนะนำให้ใช้ Spreadsheet ID
    GOOGLE_SHEET_NAME               fallback ถ้าไม่มี ID (default: Sales Logger)
    GOOGLE_WORKSHEET_NAME            worksheet (default: Sales_v2)

    TELEGRAM_BOT_TOKEN              optional
    TELEGRAM_CHAT_ID                optional

ติดตั้ง:
    pip install gspread google-auth requests python-dotenv

ตัวอย่าง:
    python sales_logger.py ^
      --gear_category lighting ^
      --product_name "ไฟฉายคาดหัว" ^
      --qty 1 ^
      --price 590 ^
      --trip_type 2d1n ^
      --experience_level beginner ^
      --party_size 2 ^
      --route_plan station_y4 ^
      --overnight_area y2 ^
      --y4_plan yes ^
      --transport train ^
      --booking_status booked ^
      --park_status open_confirmed ^
      --y2_status open_confirmed ^
      --weather_check checked ^
      --water_check checked ^
      --emergency_contact_check confirmed ^
      --recommendation_level essential ^
      --record_status confirmed
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

# External dependencies are loaded defensively so --dry_run can still be used
# to validate Agent payloads even before Google/Telegram packages are installed.
try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    gspread = None
    Credentials = None

try:
    import requests
except ImportError:
    requests = None

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False


# ============================================================
# 0. Project / KB Metadata
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=False)

DESTINATION = "ดอยขุนตาล"
KB_FILE = "trekking_gear_kb.md"
KB_VERSION = "2026-08-18"
SCHEMA_VERSION = "2.0"
CURRENCY = "THB"


# ============================================================
# 1. Canonical choices - ให้สอดคล้องกับ Master KB
# ============================================================

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

# Dynamic status:
# ห้ามให้ AI เปลี่ยน unknown -> confirmed เอง ถ้าไม่ได้ตรวจจากแหล่งที่เกี่ยวข้อง
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

RENTAL_OR_PURCHASE = {
    "purchase": "ซื้อ",
    "rental": "เช่า",
}

# หมวดสินค้าเชื่อมกับ Master KB
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

# Traceability: หมวดอุปกรณ์อ้างอิงส่วนใดของ KB
GEAR_KB_SECTIONS = {
    "backpack": "25-26",
    "footwear": "27-29",
    "shelter": "9,39",
    "sleep_system": "40,69",
    "rain_gear": "31,45,47,69",
    "lighting": "32,41,53",
    "water": "19-21,53",
    "food": "22-24,53",
    "first_aid": "35,71,74",
    "navigation": "34,70-71",
    "trekking_pole": "36,43",
    "power": "33,70",
    "clothing": "30,45,69",
    "emergency_safety": "35,49,71,83",
    "other": "-",
}


# ============================================================
# 2. Google Sheets Schema
# ============================================================

HEADERS = [
    "schema_version",
    "transaction_id",
    "timestamp",
    "kb_file",
    "kb_version",
    "destination",
    "record_status",
    "trip_type",
    "experience_level",
    "party_size",
    "travel_party",
    "route_plan",
    "overnight_area",
    "y4_plan",
    "transport",
    "booking_status",
    "park_status",
    "y2_status",
    "weather_check",
    "water_check",
    "emergency_contact_check",
    "recommendation_level",
    "gear_category",
    "kb_sections",
    "product_name",
    "qty",
    "unit_price",
    "discount_percent",
    "subtotal",
    "discount_amount",
    "total",
    "currency",
    "rental_or_purchase",
    "rental_days",
    "notes",
    "safety_flags",
]


# ============================================================
# 3. Helpers / Validation
# ============================================================

MONEY_QUANT = Decimal("0.01")


def bangkok_now_iso() -> str:
    """เวลาประเทศไทยแบบ ISO 8601"""
    return datetime.now(ZoneInfo("Asia/Bangkok")).isoformat(timespec="seconds")


def new_transaction_id() -> str:
    """สร้าง Transaction ID ที่ไม่ซ้ำ"""
    return f"DKT-{datetime.now(ZoneInfo('Asia/Bangkok')).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"


def clean_text(value: Any, default: str = "-") -> str:
    """ทำความสะอาดข้อความก่อนบันทึก"""
    if value is None:
        return default
    value = str(value).strip()
    return value if value else default


def parse_positive_int(value: str) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError("ค่าต้องเป็นจำนวนเต็ม") from exc
    if number <= 0:
        raise argparse.ArgumentTypeError("ค่าต้องมากกว่า 0")
    return number


def parse_non_negative_int(value: str) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError("ค่าต้องเป็นจำนวนเต็ม") from exc
    if number < 0:
        raise argparse.ArgumentTypeError("ค่าต้องไม่น้อยกว่า 0")
    return number


def parse_money(value: str | int | float | Decimal) -> Decimal:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError("ราคาต้องเป็นตัวเลข") from exc

    if amount < 0:
        raise argparse.ArgumentTypeError("ราคาต้องไม่น้อยกว่า 0")

    return amount.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def parse_discount(value: str | int | float | Decimal) -> Decimal:
    try:
        discount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError("ส่วนลดต้องเป็นตัวเลข") from exc

    if discount < 0 or discount > 100:
        raise argparse.ArgumentTypeError(
            "discount_percent ต้องอยู่ระหว่าง 0 ถึง 100")

    return discount.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def label(mapping: dict[str, str], key: str) -> str:
    return mapping.get(key, key)


def travel_party_label(party_size: int) -> str:
    if party_size <= 0:
        return "ไม่ระบุ"
    if party_size == 1:
        return "Solo"
    return f"กลุ่ม {party_size} คน"


def route_has_y4(route_plan: str) -> bool:
    return route_plan in {"office_y4", "station_y4"}


def route_ends_y2(route_plan: str) -> bool:
    return route_plan in {"office_y2", "station_y2"}


def validate_context(data: "SaleInput") -> None:
    """
    Validate เฉพาะ logic ที่เป็นโครงสร้างคงที่ของทริป
    ไม่ validate ข้อมูล Dynamic ว่าเปิด/ปิดจริง เพราะต้องตรวจจากแหล่งล่าสุด
    """

    if not clean_text(data.product_name, ""):
        raise ValueError("product_name ห้ามว่าง")

    if data.qty <= 0:
        raise ValueError("qty ต้องมากกว่า 0")

    if data.party_size < 0:
        raise ValueError("party_size ต้องไม่น้อยกว่า 0")

    if data.trip_type == "day_hike" and data.overnight_area != "none":
        raise ValueError(
            "trip_type=day_hike ต้องใช้ --overnight_area none "
            "เพราะเป็นทริปไม่พักค้างคืน"
        )

    if data.trip_type == "2d1n" and data.overnight_area == "none":
        raise ValueError(
            "trip_type=2d1n ต้องมีพื้นที่พักค้างคืน "
            "เช่น --overnight_area y2"
        )

    if route_has_y4(data.route_plan) and data.y4_plan == "no":
        raise ValueError(
            "route_plan ที่เลือกมี Y4 แต่ --y4_plan no "
            "กรุณาเลือก route_plan ให้สอดคล้องกัน"
        )

    if route_ends_y2(data.route_plan) and data.y4_plan == "yes":
        raise ValueError(
            "--y4_plan yes แต่ route_plan ที่เลือกจบที่ Y2 "
            "กรุณาใช้ office_y4 หรือ station_y4"
        )

    if data.overnight_area == "y2" and data.y2_status == "not_applicable":
        raise ValueError(
            "เลือกพัก Y2 แต่ y2_status=not_applicable ไม่สอดคล้องกัน"
        )

    if data.overnight_area == "none" and data.y2_status == "open_confirmed":
        # ไม่ถือเป็น error เพราะผู้ใช้สามารถตรวจ Y2 ไว้ได้แม้ไม่ค้าง
        pass

    if data.rental_or_purchase == "rental" and data.rental_days <= 0:
        raise ValueError(
            "รายการเช่าต้องระบุ --rental_days มากกว่า 0"
        )

    if data.rental_or_purchase == "purchase" and data.rental_days != 0:
        raise ValueError(
            "รายการซื้อควรใช้ --rental_days 0"
        )


def build_safety_flags(data: "SaleInput") -> list[str]:
    """
    สร้าง Safety Flags เพื่อช่วย Agent / ผู้ดูแลเห็น context
    ไม่ใช่การวินิจฉัยความปลอดภัยแบบสมบูรณ์
    """
    flags: list[str] = []

    if data.experience_level == "beginner" and data.party_size == 1:
        flags.append("มือใหม่ + Solo: KB ไม่แนะนำ Solo เป็นป่าแรก")

    if data.y4_plan == "yes":
        flags.append(
            "แผนขึ้น Y4: ต้องให้ความสำคัญกับไฟฉาย/ไฟสำรองและการเดินเช้ามืด")

    if data.overnight_area == "y2":
        flags.append("พัก Y2: ต้องตรวจสถานะพื้นที่ น้ำ และห้องน้ำล่าสุด")

    if data.park_status == "unknown":
        flags.append("ยังไม่ได้ยืนยันสถานะเปิด/ปิดอุทยาน")

    if data.park_status == "closed_confirmed":
        flags.append("สถานะระบุว่าอุทยานปิด: ต้องตรวจแผนทริปก่อนดำเนินการ")

    if (
        data.overnight_area == "y2" or data.y4_plan == "yes"
    ) and data.y2_status == "unknown":
        flags.append("ยังไม่ได้ยืนยันสถานะ Y2")

    if data.y2_status == "closed_confirmed":
        flags.append("สถานะ Y2 ระบุว่าปิด/ไม่พร้อมใช้งาน")

    if data.weather_check == "not_checked":
        flags.append("ยังไม่ได้ตรวจสภาพอากาศล่าสุด")

    if (
        data.overnight_area == "y2" or data.y4_plan == "yes"
    ) and data.water_check == "not_checked":
        flags.append("ยังไม่ได้ตรวจสถานะน้ำล่าสุด")

    if data.trip_type == "2d1n" and data.booking_status not in {"booked"}:
        flags.append("ทริปค้างคืนแต่ยังไม่ได้ยืนยันว่าจองพื้นที่พักแล้ว")

    if data.party_size == 1 and data.emergency_contact_check != "confirmed":
        flags.append(
            "Solo แต่ยังไม่ได้ยืนยันการแจ้งคนที่บ้าน/ผู้ติดต่อฉุกเฉิน")

    return flags


# ============================================================
# 4. Data Model
# ============================================================

@dataclass
class SaleInput:
    product_name: str
    qty: int
    price: Decimal

    record_status: str = "confirmed"

    trip_type: str = "2d1n"
    experience_level: str = "beginner"
    party_size: int = 0

    route_plan: str = "station_y4"
    overnight_area: str = "y2"
    y4_plan: str = "yes"
    transport: str = "train"

    booking_status: str = "not_checked"

    # Dynamic data: default = unknown / not_checked
    park_status: str = "unknown"
    y2_status: str = "unknown"
    weather_check: str = "not_checked"
    water_check: str = "not_checked"
    emergency_contact_check: str = "not_checked"

    recommendation_level: str = "recommended"
    gear_category: str = "other"

    discount_percent: Decimal = Decimal("0")
    rental_or_purchase: str = "purchase"
    rental_days: int = 0

    notes: str = "-"


def build_record(data: SaleInput) -> dict[str, Any]:
    validate_context(data)

    unit_price = parse_money(data.price)
    discount_percent = parse_discount(data.discount_percent)

    subtotal = (unit_price * data.qty).quantize(
        MONEY_QUANT, rounding=ROUND_HALF_UP
    )

    discount_amount = (
        subtotal * discount_percent / Decimal("100")
    ).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)

    total = (subtotal - discount_amount).quantize(
        MONEY_QUANT, rounding=ROUND_HALF_UP
    )

    safety_flags = build_safety_flags(data)

    record = {
        "schema_version": SCHEMA_VERSION,
        "transaction_id": new_transaction_id(),
        "timestamp": bangkok_now_iso(),
        "kb_file": KB_FILE,
        "kb_version": KB_VERSION,
        "destination": DESTINATION,

        "record_status": label(RECORD_STATUSES, data.record_status),
        "trip_type": label(TRIP_TYPES, data.trip_type),
        "experience_level": label(EXPERIENCE_LEVELS, data.experience_level),
        "party_size": data.party_size if data.party_size > 0 else "",
        "travel_party": travel_party_label(data.party_size),

        "route_plan": label(ROUTE_PLANS, data.route_plan),
        "overnight_area": label(OVERNIGHT_AREAS, data.overnight_area),
        "y4_plan": label(Y4_PLANS, data.y4_plan),
        "transport": label(TRANSPORTS, data.transport),
        "booking_status": label(BOOKING_STATUSES, data.booking_status),

        "park_status": label(PARK_STATUSES, data.park_status),
        "y2_status": label(Y2_STATUSES, data.y2_status),
        "weather_check": label(CHECK_STATUSES, data.weather_check),
        "water_check": label(CHECK_STATUSES, data.water_check),
        "emergency_contact_check": label(
            EMERGENCY_CONTACT_STATUSES,
            data.emergency_contact_check,
        ),

        "recommendation_level": label(
            RECOMMENDATION_LEVELS,
            data.recommendation_level,
        ),
        "gear_category": label(GEAR_CATEGORIES, data.gear_category),
        "kb_sections": GEAR_KB_SECTIONS.get(data.gear_category, "-"),

        "product_name": clean_text(data.product_name),
        "qty": data.qty,
        "unit_price": float(unit_price),
        "discount_percent": float(discount_percent),
        "subtotal": float(subtotal),
        "discount_amount": float(discount_amount),
        "total": float(total),
        "currency": CURRENCY,

        "rental_or_purchase": label(
            RENTAL_OR_PURCHASE,
            data.rental_or_purchase,
        ),
        "rental_days": (
            data.rental_days
            if data.rental_or_purchase == "rental"
            else 0
        ),

        "notes": clean_text(data.notes),
        "safety_flags": " | ".join(safety_flags) if safety_flags else "-",
    }

    return record


# ============================================================
# 5. Google Sheets
# ============================================================

def require_google_dependencies() -> None:
    if gspread is None or Credentials is None:
        raise RuntimeError(
            "ยังไม่ได้ติดตั้ง dependency สำหรับ Google Sheets "
            "กรุณารัน: pip install gspread google-auth"
        )


def load_service_account_info() -> dict[str, Any]:
    """
    รองรับ 2 วิธี:
    1) GOOGLE_SHEETS_CREDENTIALS = JSON string
    2) GOOGLE_SHEETS_CREDENTIALS_FILE = path to JSON file
    """

    credentials_json = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    credentials_file = os.environ.get("GOOGLE_SHEETS_CREDENTIALS_FILE")

    if credentials_json:
        try:
            return json.loads(credentials_json)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "GOOGLE_SHEETS_CREDENTIALS ไม่ใช่ JSON ที่ถูกต้อง"
            ) from exc

    if credentials_file:
        path = Path(credentials_file).expanduser()
        if not path.exists():
            raise RuntimeError(
                f"ไม่พบไฟล์ credentials: {path}"
            )

        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "ไฟล์ GOOGLE_SHEETS_CREDENTIALS_FILE "
                "ไม่ใช่ JSON ที่ถูกต้อง"
            ) from exc

    raise RuntimeError(
        "ไม่พบ Google credentials กรุณาตั้งค่า "
        "GOOGLE_SHEETS_CREDENTIALS หรือ "
        "GOOGLE_SHEETS_CREDENTIALS_FILE"
    )


def get_google_client():
    require_google_dependencies()
    creds_info = load_service_account_info()

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    creds = Credentials.from_service_account_info(
        creds_info,
        scopes=scopes,
    )

    return gspread.authorize(creds)


def open_spreadsheet(gc):
    sheet_id = os.environ.get("GOOGLE_SHEET_ID")
    sheet_name = os.environ.get(
        "GOOGLE_SHEET_NAME",
        "Sales Logger",
    )

    if sheet_id:
        return gc.open_by_key(sheet_id)

    return gc.open(sheet_name)


def get_or_create_worksheet(spreadsheet):
    """
    ค่า default ใช้ Sales_v2 เพื่อไม่ชน Schema เก่าของ sales_logger.py เดิม
    """
    worksheet_name = os.environ.get(
        "GOOGLE_WORKSHEET_NAME",
        "Sales_v2",
    )

    try:
        return spreadsheet.worksheet(worksheet_name)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=worksheet_name,
            rows=2000,
            cols=len(HEADERS),
        )
        return worksheet


def ensure_headers(worksheet) -> None:
    """
    - Sheet ว่าง -> สร้าง Header
    - Header ตรง -> ใช้ได้
    - Header ไม่ตรง -> หยุด เพื่อไม่ให้ข้อมูลเลื่อนไปผิดคอลัมน์
    """

    first_row = worksheet.row_values(1)

    if not first_row:
        worksheet.append_row(
            HEADERS,
            value_input_option="RAW",
        )
        print("✅ สร้าง Header ของ Sales Logger v2 แล้ว")
        return

    normalized = [
        value.strip()
        for value in first_row[:len(HEADERS)]
    ]

    if normalized != HEADERS:
        expected = " | ".join(HEADERS)
        found = " | ".join(normalized)

        raise RuntimeError(
            "Header ของ Google Worksheet ไม่ตรงกับ Schema v2\n\n"
            f"Expected:\n{expected}\n\n"
            f"Found:\n{found}\n\n"
            "วิธีง่ายที่สุด: ใช้ Worksheet ใหม่ เช่น "
            "GOOGLE_WORKSHEET_NAME=Sales_v2"
        )


def append_record(worksheet, record: dict[str, Any]) -> None:
    row = [record[column] for column in HEADERS]

    # RAW ป้องกันข้อความจากผู้ใช้ที่ขึ้นต้นด้วย =, +, -, @
    # ถูกตีความเป็นสูตรของ Google Sheets
    worksheet.append_row(
        row,
        value_input_option="RAW",
    )


def write_to_google_sheet(record: dict[str, Any]) -> None:
    gc = get_google_client()
    spreadsheet = open_spreadsheet(gc)
    worksheet = get_or_create_worksheet(spreadsheet)
    ensure_headers(worksheet)
    append_record(worksheet, record)


# ============================================================
# 6. Telegram
# ============================================================

def telegram_status_icon(record_status: str) -> str:
    if record_status == "ยืนยันรายการแล้ว":
        return "✅"
    if record_status == "รอยืนยัน":
        return "🕓"
    if record_status == "ยกเลิก":
        return "❌"
    return "📌"


def format_money(value: Any) -> str:
    return f"{Decimal(str(value)):,.2f}"


def build_telegram_message(record: dict[str, Any]) -> str:
    icon = telegram_status_icon(record["record_status"])

    text = (
        f"{icon} Trekking & Camping Buddy - รายการอัปเดต\n"
        f"🧾 ID: {record['transaction_id']}\n"
        f"🏔️ สถานที่: {record['destination']}\n"
        f"📌 สถานะ: {record['record_status']}\n"
        f"🥾 ทริป: {record['trip_type']} | {record['experience_level']}\n"
        f"👥 ผู้เดินทาง: {record['travel_party']}\n"
        f"🗺️ เส้นทาง: {record['route_plan']}\n"
        f"⛺ จุดพัก: {record['overnight_area']}\n"
        f"🌄 Y4: {record['y4_plan']}\n"
        f"🚆 เดินทาง: {record['transport']}\n"
        f"🎒 หมวด: {record['gear_category']} "
        f"(KB §{record['kb_sections']})\n"
        f"📦 สินค้า: {record['product_name']}\n"
        f"🔢 จำนวน: {record['qty']} ชิ้น\n"
        f"💰 ราคาต่อชิ้น: {format_money(record['unit_price'])} บาท\n"
        f"🏷️ ส่วนลด: {record['discount_percent']:.2f}%\n"
        f"💵 ยอดรวม: {format_money(record['total'])} บาท\n"
        f"🛒 รูปแบบ: {record['rental_or_purchase']}"
    )

    if record["rental_days"]:
        text += f" ({record['rental_days']} วัน)"

    text += (
        f"\n\n🔎 Dynamic checks"
        f"\n• อุทยาน: {record['park_status']}"
        f"\n• Y2: {record['y2_status']}"
        f"\n• อากาศ: {record['weather_check']}"
        f"\n• น้ำ: {record['water_check']}"
    )

    if record["safety_flags"] != "-":
        text += f"\n\n⚠️ Safety flags:\n{record['safety_flags']}"

    if record["notes"] != "-":
        safe_notes = record["notes"][:600]
        text += f"\n\n📝 หมายเหตุ: {safe_notes}"

    # Telegram sendMessage limit ~4096 chars; เผื่อ margin
    return text[:3900]


def send_telegram(record: dict[str, Any]) -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print(
            "ℹ️ ไม่พบ TELEGRAM_BOT_TOKEN หรือ TELEGRAM_CHAT_ID "
            "- ข้าม Telegram"
        )
        return False

    if requests is None:
        print(
            "⚠️ มี Telegram credentials แต่ยังไม่ได้ติดตั้ง requests "
            "(pip install requests)",
            file=sys.stderr,
        )
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": build_telegram_message(record),
    }

    last_error = None

    # retry แบบเบา ๆ 2 ครั้ง
    for attempt in range(1, 3):
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=15,
            )
            response.raise_for_status()
            print("✅ ส่ง Telegram สำเร็จ")
            return True

        except requests.RequestException as exc:
            last_error = exc
            print(
                f"⚠️ Telegram attempt {attempt}/2 ไม่สำเร็จ: {exc}",
                file=sys.stderr,
            )

    print(
        f"⚠️ ส่ง Telegram ไม่สำเร็จหลัง retry: {last_error}",
        file=sys.stderr,
    )
    return False


# ============================================================
# 7. Public function สำหรับ Agent / app.py
# ============================================================

def log_sale(
    *,
    product_name: str,
    qty: int,
    price: float | int | str | Decimal,
    gear_category: str = "other",

    record_status: str = "confirmed",

    trip_type: str = "2d1n",
    experience_level: str = "beginner",
    party_size: int = 0,

    route_plan: str = "station_y4",
    overnight_area: str = "y2",
    y4_plan: str = "yes",
    transport: str = "train",

    booking_status: str = "not_checked",
    park_status: str = "unknown",
    y2_status: str = "unknown",
    weather_check: str = "not_checked",
    water_check: str = "not_checked",
    emergency_contact_check: str = "not_checked",

    recommendation_level: str = "recommended",

    discount_percent: float | int | str | Decimal = 0,
    rental_or_purchase: str = "purchase",
    rental_days: int = 0,

    notes: str = "-",

    write_sheet: bool = True,
    notify_telegram: bool = True,
) -> dict[str, Any]:
    """
    ฟังก์ชันหลักสำหรับ Agent เรียกใช้โดยตรง

    Returns:
        record dict ที่ถูก normalize แล้ว

    Important:
        - ตัวแปร dynamic เช่น park_status/y2_status ต้องส่งเป็น confirmed
          เฉพาะเมื่อระบบได้ตรวจสอบจากแหล่งล่าสุดจริง
        - ถ้าไม่ทราบ ให้ใช้ unknown/not_checked
    """

    mappings_to_validate = [
        ("record_status", record_status, RECORD_STATUSES),
        ("trip_type", trip_type, TRIP_TYPES),
        ("experience_level", experience_level, EXPERIENCE_LEVELS),
        ("route_plan", route_plan, ROUTE_PLANS),
        ("overnight_area", overnight_area, OVERNIGHT_AREAS),
        ("y4_plan", y4_plan, Y4_PLANS),
        ("transport", transport, TRANSPORTS),
        ("booking_status", booking_status, BOOKING_STATUSES),
        ("park_status", park_status, PARK_STATUSES),
        ("y2_status", y2_status, Y2_STATUSES),
        ("weather_check", weather_check, CHECK_STATUSES),
        ("water_check", water_check, CHECK_STATUSES),
        (
            "emergency_contact_check",
            emergency_contact_check,
            EMERGENCY_CONTACT_STATUSES,
        ),
        (
            "recommendation_level",
            recommendation_level,
            RECOMMENDATION_LEVELS,
        ),
        ("gear_category", gear_category, GEAR_CATEGORIES),
        (
            "rental_or_purchase",
            rental_or_purchase,
            RENTAL_OR_PURCHASE,
        ),
    ]

    for field_name, value, mapping in mappings_to_validate:
        if value not in mapping:
            raise ValueError(
                f"{field_name}='{value}' ไม่ถูกต้อง "
                f"เลือกได้: {', '.join(mapping.keys())}"
            )

    data = SaleInput(
        product_name=clean_text(product_name, ""),
        qty=int(qty),
        price=parse_money(price),

        record_status=record_status,

        trip_type=trip_type,
        experience_level=experience_level,
        party_size=int(party_size),

        route_plan=route_plan,
        overnight_area=overnight_area,
        y4_plan=y4_plan,
        transport=transport,

        booking_status=booking_status,
        park_status=park_status,
        y2_status=y2_status,
        weather_check=weather_check,
        water_check=water_check,
        emergency_contact_check=emergency_contact_check,

        recommendation_level=recommendation_level,
        gear_category=gear_category,

        discount_percent=parse_discount(discount_percent),
        rental_or_purchase=rental_or_purchase,
        rental_days=int(rental_days),

        notes=clean_text(notes),
    )

    record = build_record(data)

    if write_sheet:
        write_to_google_sheet(record)
        print(
            f"✅ บันทึก '{record['product_name']}' "
            f"จำนวน {record['qty']} ชิ้น "
            f"ยอดรวม {format_money(record['total'])} บาท "
            "ลง Google Sheets สำเร็จ"
        )

    if notify_telegram:
        send_telegram(record)

    return record


# ============================================================
# 8. CLI
# ============================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Trekking & Camping Buddy Sales Logger "
            "- ดอยขุนตาลเท่านั้น"
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Transaction
    parser.add_argument(
        "--record_status",
        choices=RECORD_STATUSES.keys(),
        default="confirmed",
    )

    # Trip context
    parser.add_argument(
        "--trip_type",
        choices=TRIP_TYPES.keys(),
        default="2d1n",
    )

    parser.add_argument(
        "--experience_level",
        choices=EXPERIENCE_LEVELS.keys(),
        default="beginner",
    )

    parser.add_argument(
        "--party_size",
        type=parse_non_negative_int,
        default=0,
        help="0 = ไม่ระบุ, 1 = Solo, >1 = กลุ่ม",
    )

    parser.add_argument(
        "--route_plan",
        choices=ROUTE_PLANS.keys(),
        default="station_y4",
    )

    parser.add_argument(
        "--overnight_area",
        choices=OVERNIGHT_AREAS.keys(),
        default="y2",
    )

    parser.add_argument(
        "--y4_plan",
        choices=Y4_PLANS.keys(),
        default="yes",
    )

    parser.add_argument(
        "--transport",
        choices=TRANSPORTS.keys(),
        default="train",
    )

    parser.add_argument(
        "--booking_status",
        choices=BOOKING_STATUSES.keys(),
        default="not_checked",
    )

    # Dynamic checks
    parser.add_argument(
        "--park_status",
        choices=PARK_STATUSES.keys(),
        default="unknown",
        help="ห้ามใช้ confirmed หากยังไม่ได้ตรวจข้อมูลล่าสุดจริง",
    )

    parser.add_argument(
        "--y2_status",
        choices=Y2_STATUSES.keys(),
        default="unknown",
        help="ห้ามใช้ confirmed หากยังไม่ได้ตรวจข้อมูลล่าสุดจริง",
    )

    parser.add_argument(
        "--weather_check",
        choices=CHECK_STATUSES.keys(),
        default="not_checked",
    )

    parser.add_argument(
        "--water_check",
        choices=CHECK_STATUSES.keys(),
        default="not_checked",
    )

    parser.add_argument(
        "--emergency_contact_check",
        choices=EMERGENCY_CONTACT_STATUSES.keys(),
        default="not_checked",
    )

    # Product
    parser.add_argument(
        "--recommendation_level",
        choices=RECOMMENDATION_LEVELS.keys(),
        default="recommended",
    )

    parser.add_argument(
        "--gear_category",
        choices=GEAR_CATEGORIES.keys(),
        required=True,
    )

    parser.add_argument(
        "--product_name",
        type=str,
        required=True,
    )

    parser.add_argument(
        "--qty",
        type=parse_positive_int,
        required=True,
    )

    parser.add_argument(
        "--price",
        type=parse_money,
        required=True,
        help="ราคาต่อชิ้น (บาท)",
    )

    parser.add_argument(
        "--discount_percent",
        type=parse_discount,
        default=Decimal("0"),
    )

    parser.add_argument(
        "--rental_or_purchase",
        choices=RENTAL_OR_PURCHASE.keys(),
        default="purchase",
    )

    parser.add_argument(
        "--rental_days",
        type=parse_non_negative_int,
        default=0,
    )

    parser.add_argument(
        "--notes",
        type=str,
        default="-",
    )

    # Runtime options
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Validate + สร้าง record แต่ไม่เขียน Sheet/Telegram",
    )

    parser.add_argument(
        "--skip_telegram",
        action="store_true",
        help="ไม่ส่ง Telegram",
    )

    parser.add_argument(
        "--json_output",
        action="store_true",
        help="พิมพ์ผลลัพธ์เป็น JSON สำหรับ Agent/automation",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    try:
        record = log_sale(
            product_name=args.product_name,
            qty=args.qty,
            price=args.price,
            gear_category=args.gear_category,

            record_status=args.record_status,

            trip_type=args.trip_type,
            experience_level=args.experience_level,
            party_size=args.party_size,

            route_plan=args.route_plan,
            overnight_area=args.overnight_area,
            y4_plan=args.y4_plan,
            transport=args.transport,

            booking_status=args.booking_status,
            park_status=args.park_status,
            y2_status=args.y2_status,
            weather_check=args.weather_check,
            water_check=args.water_check,
            emergency_contact_check=args.emergency_contact_check,

            recommendation_level=args.recommendation_level,

            discount_percent=args.discount_percent,
            rental_or_purchase=args.rental_or_purchase,
            rental_days=args.rental_days,

            notes=args.notes,

            write_sheet=not args.dry_run,
            notify_telegram=(
                not args.dry_run
                and not args.skip_telegram
            ),
        )

        if args.dry_run:
            print("✅ DRY RUN ผ่าน - ยังไม่ได้เขียน Google Sheet/Telegram")

        if args.json_output or args.dry_run:
            print(
                json.dumps(
                    {
                        "ok": True,
                        "record": record,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )

    except (
        ValueError,
        RuntimeError,
    ) as exc:
        error = {
            "ok": False,
            "error": str(exc),
        }

        if getattr(args, "json_output", False):
            print(
                json.dumps(
                    error,
                    ensure_ascii=False,
                    indent=2,
                ),
                file=sys.stderr,
            )
        else:
            print(
                f"❌ Error: {exc}",
                file=sys.stderr,
            )

        sys.exit(1)

    except Exception as exc:
        # เก็บ fallback เพื่อไม่ให้ stack trace หลุดไปยังผู้ใช้ทั่วไป
        print(
            f"❌ เกิดข้อผิดพลาดที่ไม่คาดคิด: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
