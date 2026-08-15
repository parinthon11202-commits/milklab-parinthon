"""Trekking & Camping Buddy Caption Generator (S4 Pivot).

Usage:
    python caption_generator.py

Reads GOOGLE_API_KEY from env. Generates a Thai caption for trekking gear or routes.
"""

import os
import sys

from dotenv import load_dotenv
from google import genai


PROMPT_TEMPLATE = """\
คุณคือ social media manager ของเพจ Trekking & Camping Buddy (ผู้ช่วยวางแผนและจัดอุปกรณ์เดินป่าสำหรับมือใหม่)

จงเขียนแคปชั่นภาษาไทย 2 ถึง 3 ประโยค เพื่อโปรโมตอุปกรณ์, เส้นทาง, หรือให้ความรู้เรื่อง: {topic}

เงื่อนไข:
- โทนสนุก เป็นกันเอง อธิบายให้มือใหม่เข้าใจง่าย ใส่ emoji ได้
- เน้นเรื่องความปลอดภัยและการเตรียมตัวที่ถูกต้อง
- ต้องมี call-to-action ปิดท้าย เช่น "ทักแชทมาขอ Checklist ฟรีจาก Trekking & Camping Buddy ได้เลย!" หรือ "สั่งเลย"
- ห้ามใช้ em dash
"""


def generate_caption(topic: str, api_key: str | None = None) -> str:
    """Generate a Thai caption for the given trekking topic."""
    key = api_key or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("GOOGLE_API_KEY not set in env or argument")
    client = genai.Client(api_key=key)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=PROMPT_TEMPLATE.format(topic=topic),
    )
    return response.text or ""


def main() -> int:
    load_dotenv(override=True)
    topic = input("อุปกรณ์ เส้นทาง หรือเทคนิคที่จะโปรโมต: ").strip()
    if not topic:
        print("กรุณาใส่หัวข้อที่จะโปรโมต")
        return 1
    caption = generate_caption(topic)
    print()
    print(caption)
    return 0


if __name__ == "__main__":
    sys.exit(main())