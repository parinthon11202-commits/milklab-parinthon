"""Trekking & Camping Buddy Agent Harness (S4 Pivot)."""

import argparse
import json
import os
import sys
import requests
import gspread
from datetime import datetime

from dotenv import load_dotenv
from google import genai

# ==========================================
# ออกแบบ tool schema ใหม่สำหรับ Trekking Buddy
# ==========================================
TOOL_SCHEMA = [
    {
        "name": "log_sale",
        "description": "บันทึกการจัดเตรียม/เช่า/ซื้ออุปกรณ์ลง Google Sheets และส่ง notification",
        "parameters": {
            "type": "object",
            "properties": {
                "destination": {"type": "string", "description": "สถานที่เดินป่า เช่น ภูกระดึง, ภูสอยดาว"},
                "trip_type": {"type": "string", "description": "ประเภททริป เช่น 2D1N, 3D2N"},
                "experience_level": {"type": "string", "description": "ระดับประสบการณ์ เช่น beginner, experienced"},
                "gear_category": {"type": "string", "description": "หมวดหมู่อุปกรณ์"},
                "product_name": {"type": "string", "description": "ชื่อสินค้าหรืออุปกรณ์"},
                "qty": {"type": "integer", "description": "จำนวน"},
                "price": {"type": "number", "description": "ราคา"},
                "rental_or_purchase": {"type": "string", "description": "รูปแบบ (rental หรือ purchase)"},
                "porter": {"type": "string", "description": "มีการใช้ลูกหาบหรือไม่ (yes/no)"},
                "notes": {"type": "string", "description": "หมายเหตุเพิ่มเติม"}
            },
            "required": ["product_name", "qty", "price"],
        },
    },
    {
        "name": "trekking_checklist_generator",
        "description": "สร้าง Checklist อุปกรณ์ตามข้อมูลของทริป",
        "parameters": {
            "type": "object",
            "properties": {
                "destination": {"type": "string", "description": "สถานที่"},
                "days": {"type": "integer", "description": "จำนวนวัน"},
                "nights": {"type": "integer", "description": "จำนวนคืน"},
                "season": {"type": "string", "description": "ฤดูกาล (summer, rainy, winter)"},
                "porter": {"type": "boolean", "description": "ใช้ลูกหาบหรือไม่"},
            },
            "required": ["destination", "days", "nights"],
        },
    },
    {
        "name": "send_alert",
        "description": "ส่ง message แจ้งเตือนผ่าน Bot",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
            },
            "required": ["message"],
        },
    },
]


def parse_command(cmd: str, api_key: str | None = None) -> dict:
    api_key = api_key or os.environ.get(
        "GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    prompt = f"""
    คุณคือ AI Agent ผู้ช่วยจัดเตรียมอุปกรณ์เดินป่า แปลงคำสั่งภาษาไทยเป็น JSON
    คำสั่ง: "{cmd}"
    Tool Schema: {json.dumps(TOOL_SCHEMA, ensure_ascii=False)}
    
    ตอบเป็น JSON เท่านั้น รูปแบบ: {{"tool": "ชื่อ_tool", "args": {{"ชื่อตัวแปร": "ค่า"}}}}
    ห้ามมีข้อความอื่นปนเด็ดขาด
    """

    try:
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=prompt,
        )

        clean_text = response.text.strip()
        if clean_text.startswith('```json'):
            clean_text = clean_text[7:]
        elif clean_text.startswith('```'):
            clean_text = clean_text[3:]

        if clean_text.endswith('```'):
            clean_text = clean_text[:-3]

        return json.loads(clean_text.strip())
    except Exception as e:
        raise RuntimeError(f"Parse failed: {e}")


def dispatch_tool(tool_call: dict) -> str:
    tool_name = tool_call.get("tool")
    args = tool_call.get("args", {})

    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    sheets_creds_str = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")

    if tool_name == "log_sale":
        qty = args.get('qty', 0)
        price = args.get('price', 0)
        if qty <= 0:
            raise ValueError("quantity must be positive")
        if price < 0:
            raise ValueError("price cannot be negative")

        now_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07")
        destination = args.get('destination', '-')
        product_name = args.get('product_name', 'ไม่ระบุ')
        rental_or_purchase = args.get('rental_or_purchase', 'purchase')
        total = qty * price

        # 1. ส่งแจ้งเตือนเข้า Telegram
        if bot_token and chat_id:
            msg = f"🚨 แจ้งเตือนการจัดอุปกรณ์!\n🏔️ สถานที่: {destination}\n🎒 สินค้า: {product_name} ({rental_or_purchase})\n📦 จำนวน: {qty} ชิ้น\n💰 ยอดรวม: {total} บาท"
            tg_api = "https://" + "api.telegram.org/bot"
            url = f"{tg_api}{bot_token}/sendMessage"
            requests.post(url, json={"chat_id": chat_id, "text": msg})

        # 2. บันทึกลง Google Sheets
        if sheets_creds_str:
            try:
                if not sheets_creds_str.strip():
                    raise ValueError("ข้อมูลใน .env ว่างเปล่า")

                creds_dict = json.loads(sheets_creds_str)
                gc = gspread.service_account_from_dict(creds_dict)
                sheet = gc.open("Sales Logger").sheet1
                
                # เรียงคอลัมน์ตาม Schema ใหม่
                row_data = [
                    now_str,
                    destination,
                    args.get('trip_type', '-'),
                    args.get('experience_level', '-'),
                    args.get('gear_category', '-'),
                    product_name,
                    qty,
                    price,
                    total,
                    rental_or_purchase,
                    args.get('porter', '-'),
                    args.get('notes', '-')
                ]
                sheet.append_row(row_data)
            except Exception as e:
                raise RuntimeError(f"Google Sheets Error: {e}")

        return f"OK: row appended at {now_str}"

    elif tool_name == "trekking_checklist_generator":
        dest = args.get('destination')
        days = args.get('days')
        return f"OK: กำลังสร้าง Checklist สำหรับ {dest} จำนวน {days} วัน..."

    elif tool_name == "send_alert":
        message_text = args.get('message', 'ไม่มีข้อความ')
        if not bot_token or not chat_id:
            raise ValueError("ยังไม่ได้ใส่ TELEGRAM_BOT_TOKEN หรือ TELEGRAM_CHAT_ID")

        tg_api = "https://" + "api.telegram.org/bot"
        url = f"{tg_api}{bot_token}/sendMessage"
        resp = requests.post(
            url, json={"chat_id": chat_id, "text": f"🏕️ [Trekking Buddy]:\n{message_text}"})

        if resp.ok:
            return "OK: ส่งข้อความเข้ามือถือสำเร็จแล้ว!"
        else:
            raise RuntimeError(f"พังจ้า Telegram บ่นว่า: {resp.text}")

    else:
        raise ValueError(f"Unknown tool: {tool_name}")


def main() -> int:
    load_dotenv(override=True)

    parser = argparse.ArgumentParser()
    parser.add_argument("--cmd", required=True, help="คำสั่งภาษาไทย")
    args = parser.parse_args()

    try:
        msg_user_in = f"[USER] {args.cmd}"
        print(msg_user_in)

        tool_call = parse_command(args.cmd)
        args_str = ", ".join(
            [f"{k}: {v}" for k, v in tool_call.get("args", {}).items()])
        msg_llm = f"[LLM]  tool={tool_call['tool']} args={{{args_str}}}"
        print(msg_llm)

        result = dispatch_tool(tool_call)
        msg_tool = f"[TOOL] {tool_call['tool']} {result}"
        print(msg_tool)

        if tool_call['tool'] == "log_sale":
            total = tool_call["args"].get("qty", 0) * tool_call["args"].get("price", 0)
            final_ans = f"บันทึกข้อมูลเรียบร้อยแล้ว ยอดรวม {total} บาท"
        else:
            final_ans = "ดำเนินการสำเร็จ"

        msg_user_out = f"[USER] ←  {final_ans}"
        print(msg_user_out)

        # -------------------------------------------------------------
        # เขียนลงไฟล์ agent_trace.log
        try:
            with open("agent_trace.log", "a", encoding="utf-8") as log_file:
                log_file.write(f"{msg_user_in}\n")
                log_file.write(f"{msg_llm}\n")
                log_file.write(f"{msg_tool}\n")
                log_file.write(f"{msg_user_out}\n")
                log_file.write("-" * 50 + "\n")
        except Exception as e:
            print(f"[Warning] ไม่สามารถบันทึกลงไฟล์ log ได้: {e}")
        # -------------------------------------------------------------

    except Exception as e:
        print(f"[ERROR] {e}")
        try:
            with open("agent_trace.log", "a", encoding="utf-8") as log_file:
                log_file.write(f"[USER] {args.cmd}\n")
                log_file.write(f"[ERROR] {e}\n")
                log_file.write("-" * 50 + "\n")
        except:
            pass

    return 0


if __name__ == "__main__":
    sys.exit(main())