# Pivot to: Trekking & Camping Buddy

## ผู้ช่วย AI วางแผนเดินป่าและเตรียมอุปกรณ์สำหรับมือใหม่ — ดอยขุนตาล

> **ประเภท Domain:** Prototype / ธุรกิจสมมติใหม่สำหรับโปรเจกต์ Session 4  
> **ขอบเขตระบบปัจจุบัน:** อุทยานแห่งชาติดอยขุนตาลเท่านั้น  
> **กลุ่มผู้ใช้หลัก:** นักเดินป่ามือใหม่ที่ต้องการวางแผนทริป 2 วัน 1 คืน เตรียมอุปกรณ์ และลดความเสี่ยงก่อนเดินทาง

---

## Context

- **เจ้าของ / Persona:**  
  Persona ของระบบคือผู้ช่วยที่มีความรู้เรื่องการเดินป่าและการเตรียมอุปกรณ์สำหรับมือใหม่ อธิบายด้วยภาษาไทยแบบสุภาพ เป็นกันเอง ใช้คำว่า “ครับ” อย่างเป็นธรรมชาติ และให้ความสำคัญกับความปลอดภัยมากกว่าการพิชิตยอด

- **ธุรกิจ / ระบบคืออะไร:**  
  Trekking & Camping Buddy เป็น AI Chatbot + RAG Knowledge Base สำหรับช่วยนักเดินป่ามือใหม่เตรียมทริป **ดอยขุนตาล** โดยเฉพาะ ตั้งแต่ทำความเข้าใจเส้นทาง Y1–Y4, การพักที่ Y2, การเตรียมน้ำ อาหาร เสื้อผ้า รองเท้า ไฟฉาย อุปกรณ์นอน การเดินช่วงเช้ามืด ไปจนถึง Checklist และ Safety Plan

- **ปัญหา Solopreneur ที่ต้องการแก้:**  
  มือใหม่มักถามคำถามซ้ำ ๆ และไม่รู้ว่าจะเริ่มเตรียมตัวจากจุดใด เช่น
  - ต้องเตรียมอุปกรณ์อะไร
  - ต้องพกน้ำเท่าไร
  - นอน Y2 ต้องเตรียมอะไร
  - ขึ้น Y4 เช้ามืดต้องใช้ไฟฉายหรือเสื้อกันหนาวไหม
  - เส้นทางใช้เวลาประมาณกี่ชั่วโมง
  - ไปคนเดียวได้หรือไม่
  - ถ้าฝนตกหรือเกิดอุบัติเหตุควรทำอย่างไร
  - ข้อมูลเปิด/ปิด ราคา น้ำ รถไฟ และอากาศเชื่อถือได้แค่ไหน

  ระบบช่วยตอบคำถามพื้นฐานเหล่านี้ได้ตลอด 24 ชั่วโมง และช่วยลดภาระการตอบคำถามซ้ำของผู้ดูแลบริการ

---

## กลุ่มผู้ใช้งานหลัก

1. มือใหม่ที่ยังไม่เคยเดินป่า
2. ผู้ที่กำลังวางแผนไปดอยขุนตาลเป็นป่าแรก
3. ผู้ที่ไม่รู้ว่าต้องเตรียมอุปกรณ์อะไร
4. ผู้ที่ต้องการ Checklist สำหรับทริป 2 วัน 1 คืน
5. ผู้ที่ต้องการวางแผนการพัก Y2 และขึ้น Y4
6. ผู้ที่ต้องการคำแนะนำเรื่องน้ำ อาหาร เสื้อผ้า รองเท้า และอุปกรณ์ฉุกเฉิน
7. ผู้ที่ต้องการซื้อหรือเช่าอุปกรณ์หลังจากได้รับคำแนะนำ
8. ผู้ที่ต้องการข้อมูลความปลอดภัยและแผนฉุกเฉินก่อนเดินทาง

---

## ขอบเขตที่ตั้งใจจำกัด

ระบบเวอร์ชันนี้ **ไม่ใช่ Chatbot แนะนำป่าทั่วประเทศไทย**

รองรับเฉพาะ:

> **อุทยานแห่งชาติดอยขุนตาล**

เหตุผลที่จำกัด Scope คือ

- ทำให้ Knowledge Base มีความลึกมากกว่าการกระจายข้อมูลหลายพื้นที่
- ลด Hallucination จากการนำข้อมูลคนละอุทยานมาปนกัน
- ทำให้ทดสอบ RAG ได้ง่าย
- ทำ Guardrail ได้ชัดเจน
- เหมาะกับการ Demo ระบบที่มี Domain ชัดเจน

ถ้าผู้ใช้ถามรายละเอียดของอุทยานอื่น ระบบจะตอบอย่างสุภาพว่าฐานความรู้ปัจจุบันรองรับเฉพาะดอยขุนตาล

---

# สิ่งที่เปลี่ยนจาก MilkLab°

## 1. `caption_generator.py`

### เดิม

สร้าง Caption สำหรับธุรกิจ MilkLab° และสินค้า/เมนูของร้าน

### หลัง Pivot

เปลี่ยนเป็น Social Media Caption Generator สำหรับ Trekking & Camping Buddy

ความสามารถหลัก:

- อ่านข้อมูลจาก `trekking_gear_kb.md`
- สร้าง Caption เฉพาะดอยขุนตาล
- รองรับโพสต์แบบ educational, gear, route, safety, promo และ checklist
- รองรับ Facebook / Instagram / TikTok / General
- ใช้ Persona และ Guardrail จาก KB
- ไม่แต่งราคา โปรโมชั่น หรือข้อมูลสดเอง
- ถ้าเป็นข้อมูล `[DYNAMIC]` จะใส่ Disclaimer
- รองรับ Debug เพื่อดูว่า Caption อ้างอิง Section ใดของ KB
- ใช้ Structured JSON Output ก่อนประกอบ Caption

---

## 2. `sales_logger.py`

### เดิม

บันทึกข้อมูลยอดขายตาม Schema ของธุรกิจ MilkLab°

### หลัง Pivot

เปลี่ยนเป็น Sales / Rental Logger สำหรับอุปกรณ์ Trekking & Camping Buddy

ข้อมูลสำคัญที่รองรับ เช่น:

```text
transaction_id
timestamp
destination
trip_type
experience_level
party_size
route_plan
overnight_area
y4_plan
transport
booking_status
park_status
y2_status
weather_check
water_check
emergency_contact_check
recommendation_level
gear_category
kb_sections
product_name
qty
unit_price
discount_percent
total
rental_or_purchase
rental_days
notes
safety_flags
```

จุดสำคัญ:

- Destination ถูกล็อกเป็น **ดอยขุนตาล**
- รองรับทั้ง `purchase` และ `rental`
- เชื่อมหมวดสินค้าเข้ากับ Section ใน KB
- มี `safety_flags`
- ข้อมูล Dynamic เช่น Y2, อากาศ และน้ำ มีค่าเริ่มต้นเป็น `unknown` / `not_checked`
- ใช้ Google Sheets เป็น Sales Log
- สามารถส่ง Notification ไป Telegram
- ไม่เก็บข้อมูลสุขภาพส่วนบุคคลที่ไม่จำเป็นใน Sales Sheet

---

## 3. `agent_harness.py`

### เดิม

Tool Schema ยังเป็น Domain เดิม สามารถรับหลาย Destination และมี `porter`

### หลัง Pivot

เปลี่ยนเป็น Agent / Tool Router สำหรับดอยขุนตาล

Actions หลัก:

```text
log_sale
generate_checklist
send_alert
no_action
```

ความสามารถหลัก:

- ใช้ Gemini Structured Output แปลงคำสั่งภาษาไทยเป็น Tool Decision
- ล็อก Scope เป็นดอยขุนตาล
- ไม่มี `porter`
- มี Local Confirmation Gate
- ไม่บันทึก Sale เพียงเพราะผู้ใช้ถามเรื่องสินค้า
- เรียก `sales_logger.log_sale()` เมื่อผู้ใช้ยืนยันซื้อ/เช่าชัดเจนเท่านั้น
- มี Checklist Generator
- มี Telegram Alert
- มี `agent_trace.jsonl` สำหรับ Debug
- รองรับ `--dry-run`, `--self-check`, `--json-output`

---

## 4. RAG Knowledge Base

### เดิม

```text
menu_kb.md
```

เป็น Knowledge Base สำหรับเมนู/สินค้า MilkLab°

### หลัง Pivot

เปลี่ยนเป็น:

```text
trekking_gear_kb.md
```

Master KB เป็นฐานความรู้เฉพาะ **ดอยขุนตาล** ครอบคลุม Section 0–84 เช่น:

- ภาพรวมและเส้นทาง Y1–Y4
- ระยะทาง / ความสูง / เวลาเดิน
- การพัก Y2
- รถไฟและการเดินทาง
- น้ำและอาหาร
- รองเท้า / เสื้อผ้า / กันฝน
- ไฟฉาย / Power Bank / Offline Map
- First Aid / Trekking Pole
- Tent / Sleep System
- การเดินกลางคืน
- ฤดูฝน / ทาก / แมลง
- Solo Safety
- Daypack Y4
- Checklist / FAQ
- Dynamic Data
- Guardrail
- อุณหภูมิ / สัญญาณ / ห้องน้ำ
- Emergency Plan
- สัตว์ป่า / งู
- เด็ก / ผู้สูงอายุ / โรคประจำตัว
- Data Confidence / Source Hierarchy
- Persona / Tone
- Few-shot Dialogue
- Risk Persistence
- Quality Checklist

---

## 5. `app.py`

### เดิม

หน้า Chatbot และ Branding ยังอิง MilkLab°

### หลัง Pivot

เปลี่ยนเป็น:

> **Trekking & Camping Buddy | ดอยขุนตาล**

Architecture:

```text
User
  ↓
Streamlit Chat UI
  ↓
Query Understanding
  ↓
RAG Retrieval
  ├─ Sentence Transformer
  ├─ FAISS
  ├─ Query Expansion
  └─ Forced Safety Sections
  ↓
Always-on System Policy
  ↓
Gemini
  ↓
Answer
```

จุดเด่น:

- ใช้ multilingual embedding สำหรับคำถามภาษาไทย
- ใช้ FAISS cosine similarity
- Section 0 สารบัญไม่ถูกนำเข้า Vector Index
- Section 65, 67, 79, 80, 81, 83, 84 เป็น Always-on Policy
- มี Forced Safety Routing เช่น Y4 / Solo / งู / ฉุกเฉิน
- มี Dynamic Data Detection
- มี RAG Debug Mode
- Chatbot ไม่อ้างว่าตรวจข้อมูลสดถ้าระบบไม่มี Live Web Tool

---

## 6. `requirements.txt`

Dependency หลัก:

```text
google-genai
python-dotenv
sentence-transformers
faiss-cpu
numpy
streamlit
gspread
google-auth
requests
tzdata
pytest
```

ติดตั้งด้วย:

```bash
python -m pip install -r requirements.txt
```

---

# Product / Service Catalog

| Service / Product | ราคา | หมายเหตุ |
|---|---:|---|
| Doi Khun Tan RAG Chatbot | ฟรี | ถามข้อมูลเตรียมทริปดอยขุนตาล |
| Trekking Checklist Generator | ฟรี | สร้าง Checklist ตามบริบททริป |
| Safety Planning Assistant | ฟรี | ช่วยเตรียมแผนลดความเสี่ยง |
| Gear Recommendation | ฟรี | แนะนำหมวดอุปกรณ์ตาม KB |
| Caption Generator | ฟรี | สร้าง Content สำหรับเพจ |
| Purchase / Rental Logging | ตามราคาที่ผู้ใช้/ผู้ดูแลระบุ | ระบบไม่เดาราคาสินค้าเอง |
| Telegram Notification | ฟรีใน Prototype | แจ้งรายการที่ Agent บันทึก |

> ราคาและโปรโมชั่นสินค้าไม่ถูกเก็บเป็นข้อเท็จจริงถาวรใน KB  
> เมื่อต้องบันทึก Sales Transaction ราคาต้องมาจาก Input ของผู้ใช้หรือระบบในขณะนั้น

---

# Knowledge Base Design

## Data Confidence

KB แบ่งข้อมูลเป็น 4 ประเภท:

### `[STATIC]`

ข้อมูลค่อนข้างคงที่ เช่น ชื่อสถานที่ ลำดับ Y1–Y4 และหลักความปลอดภัยพื้นฐาน

### `[ESTIMATE]`

ข้อมูลประมาณการ เช่น เวลาเดิน ระดับความยาก และอุณหภูมิสำหรับวางแผน

AI ต้องใช้คำว่า:

```text
ประมาณ
โดยทั่วไป
ควรเผื่อ
```

### `[DYNAMIC]`

ข้อมูลที่เปลี่ยนได้ เช่น:

- เปิด/ปิด
- ราคา
- รถไฟ
- อากาศ
- Y2/Y4
- น้ำ
- ห้องน้ำ
- ร้านค้า
- สัญญาณโทรศัพท์
- เวลาพระอาทิตย์ขึ้น
- เบอร์ติดต่อ

AI ห้ามเดาข้อมูลเหล่านี้เป็นข้อมูลปัจจุบัน

### `[ANECDOTAL]`

ข้อมูลจากประสบการณ์ผู้เดินทาง ใช้ประกอบประสบการณ์ แต่ไม่ใช้แทนประกาศทางการ

---

# Guardrails

## Scope Guardrail

ถ้าผู้ใช้ถามรายละเอียดสถานที่อื่น ระบบจะระบุว่ารองรับเฉพาะดอยขุนตาลและไม่แต่งข้อมูลเพิ่ม

## Dynamic Data Guardrail

ตัวอย่างคำถาม:

```text
พรุ่งนี้ Y2 เปิดไหม
วันนี้รถไฟออกกี่โมง
ตอนนี้ค่าเช่าเต็นท์เท่าไร
พรุ่งนี้ฝนตกไหม
```

ระบบต้องไม่เดา และแนะนำให้ตรวจสอบข้อมูลล่าสุดจากแหล่งทางการ

## Safety Guardrail

ระบบ:

- ไม่วินิจฉัยโรค
- ไม่ปรับยา
- ไม่รับรองว่าผู้ใช้ปลอดภัย 100%
- ไม่สนับสนุนการฝ่าฝืนการปิดเส้นทาง
- ให้ Safety Plan เมื่อผู้ใช้ยังยืนยันทำสิ่งที่เสี่ยง

## Transaction Guardrail

คำถาม:

> “ไฟฉายราคา 590 ดีไหม”

ไม่ถือว่าเป็นคำสั่งซื้อ

คำสั่ง:

> “ยืนยันซื้อไฟฉายคาดหัว 1 ชิ้น ราคา 590 บาท”

จึงสามารถผ่าน Confirmation Gate ไปยัง Sales Logger ได้

---

# Test Plan สำหรับ Session 4

ก่อนส่งงาน ทดสอบ Domain ใหม่อย่างน้อย 5 คำถาม:

| # | คำถามทดสอบ | สิ่งที่ต้องตรวจ | ผล |
|---|---|---|---|
| 1 | ผมไม่เคยเดินป่ามาก่อน ดอยขุนตาลเหมาะไหม | Beginner answer + KB grounding | ✅ PASS |
| 2 | ขึ้น Y4 เช้ามืดต้องเอาอะไรไปบ้าง | Y4 / Daypack / Headlamp | ✅ PASS |
| 3 | พรุ่งนี้ Y2 เปิดไหม แล้วมีน้ำไหม | Dynamic Guardrail ไม่ Hallucinate | ✅ PASS |
| 4 | ผมจะไปคนเดียวแน่นอน ต้องเตรียมอะไร | Risk Persistence + Safety Plan | ✅ PASS |
| 5 | ช่วยจัด Checklist ดอยขุนตาล 2 วัน 1 คืน | Checklist ครบและตรง Scope | ✅ PASS |

> **ผลทดสอบบน Streamlit Deploy จริง: PASS 5/5**

---

# Technology Stack

```text
Python
Streamlit
Google Gemini API
Google Gen AI SDK
Sentence Transformers
FAISS
NumPy
Google Sheets
gspread
Google Auth
Telegram Bot API
python-dotenv
pytest
```

---

# Repository Structure

```text
project/
├── app.py
├── caption_generator.py
├── sales_logger.py
├── agent_harness.py
├── trekking_gear_kb.md
├── requirements.txt
├── PIVOT.md
├── README.md
└── .env
```

> `.env` ต้องไม่ Commit API Key หรือ Secret ขึ้น GitHub

---

# Deployment

## Streamlit Community Cloud

ระบบถูก Deploy เป็น Public App ด้วย Streamlit Community Cloud

### Deploy URL

https://trekking-camping-buddy.streamlit.app

### Deploy Configuration

```text
Repository: parinthon11202-commits/milklab-parinthon
Deploy Branch: pivot
Main file path: app.py
Platform: Streamlit Community Cloud
```

### Deploy Checklist

- [x] Push branch `pivot`
- [x] ตรวจ `requirements.txt`
- [x] ตั้ง Streamlit Secrets
- [x] ตั้ง Gemini API Key ผ่าน Streamlit Secrets
- [x] Deploy บน Streamlit Community Cloud
- [x] เปิดหน้า App จาก Public URL ได้
- [x] ทดสอบ 5 คำถาม
- [x] Test PASS 5/5
- [x] ไม่มี MilkLab° reference ใน UI หลัก
- [x] ไม่มี API Key หรือ Secret ถูก Commit ใน GitHub

### URL สำหรับส่งใน S4 Worksheet — Question 1

```text
https://trekking-camping-buddy.streamlit.app
```

---

# Pull Request

## Branch

```text
release/demo-day
```

## Target

```text
main
```

## PR Direction

```text
release/demo-day → main
```

## PR Title

```text
Pivot to Trekking & Camping Buddy
```

## PR URL

```text
https://github.com/parinthon11202-commits/milklab-parinthon/pull/1
```

## PR Requirement ก่อนส่ง

- [x] สร้าง branch `release/demo-day`
- [x] Push branch `release/demo-day` ขึ้น GitHub
- [x] เปิด Pull Request จาก `release/demo-day` เข้า `main`
- [x] Copy PR URL หลังเปิด PR
- [ ] มี Reviewer ใน Cohort Comment อย่างน้อย 1 ข้อ
- [ ] Merge Pull Request เข้า `main`

### URL สำหรับส่งใน S4 Worksheet — Question 2

```text
รอ Reviewer Comment และ Merge เข้า main ก่อน แล้วใช้ URL นี้:
https://github.com/parinthon11202-commits/milklab-parinthon/pull/1
```

---

# Peer Review

เพื่อให้ครบตาม Session 4 และ S4 Worksheet ต้องทำ 2 ส่วน

## A. ให้เพื่อนใน Cohort Review PR ของเรา

PR `release/demo-day → main` ต้องมี Reviewer ใน Cohort Comment อย่างน้อย 1 ข้อก่อน Merge

หลังมี Comment แล้วจึง Merge PR เข้า `main`

## B. Review PR ของเพื่อนอย่างน้อย 1 คน

Comment อย่างน้อย:

### Strength

> จุดที่ทำได้ดีคือ Domain ชัดและเห็นการเปลี่ยน Schema/Prompt จาก MilkLab° ชัดเจนครับ

### Question

> ถ้าข้อมูลที่เปลี่ยนตามเวลา เช่น ราคา หรือสถานะบริการเปลี่ยน ระบบมีวิธีป้องกันข้อมูลเก่าอย่างไรครับ

### Suggestion

> แนะนำให้เพิ่ม Test Case สำหรับคำถามที่อยู่นอก Domain เพื่อดูว่า Chatbot ปฏิเสธได้ถูกต้องหรือไม่ครับ

### Peer Review Checklist

- [ ] PR ของเรามี Cohort Reviewer Comment อย่างน้อย 1 ข้อ
- [ ] Review PR ของเพื่อนอย่างน้อย 1 คน
- [ ] มี Strength อย่างน้อย 1 ข้อ
- [ ] มี Question อย่างน้อย 1 ข้อ
- [ ] มี Suggestion อย่างน้อย 1 ข้อ
- [ ] Screenshot หลักฐานเก็บไว้แล้ว

---

# Reflection

## สิ่งที่ได้เรียนรู้จากการ Pivot

การ Pivot จาก MilkLab° มาเป็น Trekking & Camping Buddy ทำให้เห็นว่า Pattern หลักของระบบ AI สามารถนำไปใช้กับ Domain อื่นได้ โดยไม่จำเป็นต้องสร้างทุกอย่างใหม่จากศูนย์

สิ่งที่เปลี่ยนจริงไม่ใช่แค่ชื่อหน้าเว็บ แต่ต้องเปลี่ยน:

- Prompt
- Knowledge Base
- RAG Retrieval
- Tool Schema
- Transaction Schema
- Guardrail
- Persona
- Error Handling
- Test Cases
- UX ของคำตอบ

สิ่งที่เรียนรู้มากที่สุดคือ **ข้อมูลแต่ละ Domain มีระดับความน่าเชื่อถือไม่เหมือนกัน**

ใน Domain เดินป่า ข้อมูลบางอย่าง เช่น เส้นทางพื้นฐานสามารถเก็บใน KB ได้ แต่ข้อมูลอย่างสถานะเปิด/ปิด น้ำ อากาศ ราคา และรถไฟสามารถเปลี่ยนได้ จึงไม่ควรให้ AI เดาจากข้อมูลเก่า

จึงเพิ่มแนวคิด:

```text
STATIC
ESTIMATE
DYNAMIC
ANECDOTAL
```

อีกสิ่งที่ได้เรียนรู้คือ RAG อย่างเดียวไม่เพียงพอสำหรับกฎสำคัญ เพราะ Vector Search อาจไม่ดึง Guardrail Section ทุกครั้ง จึงย้ายกฎสำคัญ เช่น Scope, Dynamic Data, Persona และ Safety ไปเป็น **Always-on System Policy**

ในส่วน Agent ได้เรียนรู้เรื่อง Side Effect ว่า AI ไม่ควรเขียนข้อมูลลง Google Sheets เพียงเพราะตีความว่าผู้ใช้สนใจสินค้า จึงเพิ่ม Local Confirmation Gate และให้ `sales_logger.py` เป็นจุดเดียวที่เขียน Transaction

จากโปรเจกต์นี้ได้ฝึก:

- RAG
- Prompt Engineering
- Structured Output
- Agent / Tool Routing
- Guardrail
- Sales Logging
- API Integration
- UX
- Safety Design
- Testing
- Deployment Workflow

---

# Main System Goal

เป้าหมายของ **Trekking & Camping Buddy** คือ:

> **ช่วยให้นักเดินป่ามือใหม่ที่ต้องการไปดอยขุนตาล สามารถเข้าใจเส้นทาง วางแผนทริป เตรียมอุปกรณ์ ตรวจความเสี่ยง และออกเดินทางได้อย่างเป็นระบบมากขึ้น โดย AI ต้องไม่สร้างความมั่นใจเกินข้อมูลที่มี**

แกนหลัก:

```text
Doi Khun Tan Knowledge Base
+
RAG Chatbot
+
Checklist Generator
+
Safety Guardrails
+
Agent Tool Router
+
Sales / Rental Logger
+
Caption Generator
```

---

# Session 4 Deliverable Status

| Deliverable | Status |
|---|---|
| Pivot Domain | ✅ Trekking & Camping Buddy |
| `caption_generator.py` | ✅ Pivot แล้ว |
| `sales_logger.py` | ✅ Pivot แล้ว |
| `agent_harness.py` | ✅ Pivot แล้ว |
| RAG KB | ✅ `trekking_gear_kb.md` |
| `app.py` branding + RAG | ✅ Pivot แล้ว |
| `requirements.txt` | ✅ อัปเดตแล้ว |
| `PIVOT.md` | ✅ อัปเดตแล้ว |
| Test 5 questions | ✅ PASS 5/5 |
| Streamlit Community Cloud | ✅ Deploy แล้ว |
| Deploy URL | ✅ https://trekking-camping-buddy.streamlit.app |
| branch `release/demo-day` | ✅ สร้างและ Push แล้ว |
| PR `release/demo-day` → `main` | ✅ เปิดแล้ว |
| PR URL | ✅ https://github.com/parinthon11202-commits/milklab-parinthon/pull/1 |
| Cohort Reviewer Comment ใน PR | ⬜ รอ Reviewer |
| Merge PR เข้า `main` | ⬜ รอหลัง Reviewer Comment |
| Review PR ของเพื่อน | ⬜ ต้องทำ |
| Peer Review Screenshot | ⬜ ต้องแนบ |
| Reflection | ✅ พร้อมใช้ |

---

## Final Note

ตอนนี้ส่วนที่เสร็จแล้ว:

1. ✅ Pivot Domain
2. ✅ ปรับโค้ดหลักและ KB
3. ✅ Deploy Streamlit
4. ✅ Test PASS 5/5
5. ✅ เปิด PR `release/demo-day → main`
6. ✅ มี PR URL

สิ่งที่ยังเหลือก่อนส่งให้ครบ:

1. ให้ Reviewer ใน Cohort Comment PR อย่างน้อย 1 ข้อ
2. Merge PR เข้า `main`
3. Review PR ของเพื่อนอย่างน้อย 1 คน
4. เก็บ Screenshot Peer Review
5. ใช้ PR URL ตอบ S4 Worksheet Question 2 หลัง Merge

**Deploy URL**

```text
https://trekking-camping-buddy.streamlit.app
```

**PR URL**

```text
https://github.com/parinthon11202-commits/milklab-parinthon/pull/1
```
