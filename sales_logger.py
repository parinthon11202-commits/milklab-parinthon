import argparse
import json
import os
import sys
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import requests


def send_telegram(destination, product_name, qty, price, total, rental_or_purchase):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("ไม่พบ Token หรือ Chat ID ของ Telegram ข้ามการแจ้งเตือน")
        return

    text = f"🚨 อัปเดตรายการใหม่!\n🏔️ สถานที่: {destination}\n🎒 สินค้า: {product_name} ({rental_or_purchase})\n📦 จำนวน: {qty} ชิ้น\n💰 ราคา: {price} บาท\n💵 ยอดรวม: {total} บาท"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}

    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"ส่ง Telegram ไม่สำเร็จ: {e}")


def main():
    # 1. รับค่าจาก Command Line ตาม Schema ใหม่ของ Trekking & Camping Buddy
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", type=str, default="-")
    parser.add_argument("--trip_type", type=str, default="-")
    parser.add_argument("--experience_level", type=str, default="-")
    parser.add_argument("--gear_category", type=str, default="-")
    parser.add_argument("--product_name", required=True, type=str)
    parser.add_argument("--qty", required=True, type=int)
    parser.add_argument("--price", required=True, type=float)
    parser.add_argument("--rental_or_purchase", type=str, default="purchase")
    parser.add_argument("--porter", type=str, default="-")
    parser.add_argument("--notes", type=str, default="-")
    args = parser.parse_args()

    total = args.qty * args.price
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00")

    # 2. เตรียมเชื่อมต่อ Google Sheets
    creds_json = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    if not creds_json:
        print("Error: ไม่พบ GOOGLE_SHEETS_CREDENTIALS", file=sys.stderr)
        sys.exit(1)

    try:
        creds_dict = json.loads(creds_json)
        scopes = ["https://spreadsheets.google.com/feeds",
                  "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(
            creds_dict, scopes=scopes)
        gc = gspread.authorize(creds)

        # *** อย่าลืมสร้าง Sheet ใหม่หรือแก้คอลัมน์ใน Sheet เดิมให้ตรงกับข้อมูลชุดนี้นะครับ ***
        sheet = gc.open("Sales Logger").sheet1

        # 3. บันทึกลง Sheet (เรียงคอลัมน์: เวลา, ป่า, ประเภททริป, ประสบการณ์, หมวดหมู่อุปกรณ์, ชื่อสินค้า, จำนวน, ราคา, ยอดรวม, เช่า/ซื้อ, ลูกหาบ, หมายเหตุ)
        sheet.append_row([now, args.destination, args.trip_type, args.experience_level, args.gear_category,
                          args.product_name, args.qty, args.price, total, args.rental_or_purchase, args.porter, args.notes])
        print(
            f"บันทึก {args.product_name} จำนวน {args.qty} ลง Google Sheet สำเร็จ!")

    except Exception as e:
        # 4. จัดการ Error กรณีเข้า Sheet ไม่ได้
        print(
            f"Error: เข้าถึง Google Sheets ไม่ได้ โปรดตรวจสอบการแชร์ไฟล์ ({e})", file=sys.stderr)
        sys.exit(1)

    # ส่งแจ้งเตือนเข้า Telegram
    send_telegram(args.destination, args.product_name, args.qty,
                  args.price, total, args.rental_or_purchase)


if __name__ == "__main__":
    main()
