**# Pivot to: Trekking & Camping Buddy**

**## ผู้ช่วย AI วางแผนเดินป่าและเตรียมอุปกรณ์สำหรับมือใหม่ — ดอยขุนตาล**

\> **\*\*ประเภท Domain:\*\*** Prototype / ธุรกิจสมมติใหม่สำหรับโปรเจกต์ Session 4  
\> **\*\*ขอบเขตระบบปัจจุบัน:\*\*** อุทยานแห่งชาติดอยขุนตาลเท่านั้น  
\> **\*\*กลุ่มผู้ใช้หลัก:\*\*** นักเดินป่ามือใหม่ที่ต้องการวางแผนทริป 2 วัน 1 คืน เตรียมอุปกรณ์ และลดความเสี่ยงก่อนเดินทาง

**---**

**## Context**

\- **\*\*เจ้าของ / Persona:\*\***  
  Persona ของระบบคือผู้ช่วยที่มีความรู้เรื่องการเดินป่าและการเตรียมอุปกรณ์สำหรับมือใหม่ อธิบายด้วยภาษาไทยแบบสุภาพ เป็นกันเอง ใช้คำว่า “ครับ” อย่างเป็นธรรมชาติ และให้ความสำคัญกับความปลอดภัยมากกว่าการพิชิตยอด

\- **\*\*ธุรกิจ / ระบบคืออะไร:\*\***  
  Trekking & Camping Buddy เป็น AI Chatbot + RAG Knowledge Base สำหรับช่วยนักเดินป่ามือใหม่เตรียมทริป **\*\*ดอยขุนตาล\*\*** โดยเฉพาะ ตั้งแต่ทำความเข้าใจเส้นทาง Y1–Y4, การพักที่ Y2, การเตรียมน้ำ อาหาร เสื้อผ้า รองเท้า ไฟฉาย อุปกรณ์นอน การเดินช่วงเช้ามืด ไปจนถึง Checklist และ Safety Plan

\- **\*\*ปัญหา Solopreneur ที่ต้องการแก้:\*\***  
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

**---**

**## กลุ่มผู้ใช้งานหลัก**

1\. มือใหม่ที่ยังไม่เคยเดินป่า
2\. ผู้ที่กำลังวางแผนไปดอยขุนตาลเป็นป่าแรก
3\. ผู้ที่ไม่รู้ว่าต้องเตรียมอุปกรณ์อะไร
4\. ผู้ที่ต้องการ Checklist สำหรับทริป 2 วัน 1 คืน
5\. ผู้ที่ต้องการวางแผนการพัก Y2 และขึ้น Y4
6\. ผู้ที่ต้องการคำแนะนำเรื่องน้ำ อาหาร เสื้อผ้า รองเท้า และอุปกรณ์ฉุกเฉิน
7\. ผู้ที่ต้องการซื้อหรือเช่าอุปกรณ์หลังจากได้รับคำแนะนำ
8\. ผู้ที่ต้องการข้อมูลความปลอดภัยและแผนฉุกเฉินก่อนเดินทาง

**---**

**## ขอบเขตที่ตั้งใจจำกัด**

ระบบเวอร์ชันนี้ **\*\*ไม่ใช่ Chatbot แนะนำป่าทั่วประเทศไทย\*\***

รองรับเฉพาะ:

\> **\*\*อุทยานแห่งชาติดอยขุนตาล\*\***

เหตุผลที่จำกัด Scope คือ

\- ทำให้ Knowledge Base มีความลึกมากกว่าการกระจายข้อมูลหลายพื้นที่
\- ลด Hallucination จากการนำข้อมูลคนละอุทยานมาปนกัน
\- ทำให้ทดสอบ RAG ได้ง่าย
\- ทำ Guardrail ได้ชัดเจน
\- เหมาะกับการ Demo ระบบที่มี Domain ชัดเจน

ถ้าผู้ใช้ถามรายละเอียดของอุทยานอื่น ระบบจะตอบอย่างสุภาพว่าฐานความรู้ปัจจุบันรองรับเฉพาะดอยขุนตาล

**---**

**# สิ่งที่เปลี่ยนจาก MilkLab°**

**## 1. \`caption\_generator.py\`**

**### เดิม**

สร้าง Caption สำหรับธุรกิจ MilkLab° และสินค้า/เมนูของร้าน

**### หลัง Pivot**

เปลี่ยนเป็น Social Media Caption Generator สำหรับ Trekking & Camping Buddy

ความสามารถหลัก:

\- อ่านข้อมูลจาก \`trekking\_gear\_kb.md\`
\- สร้าง Caption เฉพาะดอยขุนตาล
\- รองรับประเภทโพสต์
  - educational
  - gear
  - route
  - safety
  - promo
  - checklist
\- รองรับ Facebook / Instagram / TikTok / General
\- ใช้ Persona และ Guardrail จาก KB
\- ไม่แต่งราคา โปรโมชั่น หรือข้อมูลสดเอง
\- ถ้าเป็นข้อมูล \`[DYNAMIC]\` จะใส่ Disclaimer
\- รองรับ Debug เพื่อดูว่า Caption อ้างอิง Section ใดของ KB
\- ใช้ Structured JSON Output ก่อนประกอบ Caption

ตัวอย่าง:

\`\`\`bash
python caption\_generator.py \\
  --topic "ไฟฉายคาดหัวสำหรับขึ้น Y4" \\
  --kind gear \\
  --platform facebook \\
  --debug
\`\`\`

**---**

**## 2. \`sales\_logger.py\`**

**### เดิม**

บันทึกข้อมูลยอดขายตาม Schema ของธุรกิจ MilkLab°

**### หลัง Pivot**

เปลี่ยนเป็น Sales / Rental Logger สำหรับอุปกรณ์ Trekking & Camping Buddy

ข้อมูลหลักที่บันทึก เช่น

\`\`\`text
schema\_version
transaction\_id
timestamp
kb\_file
kb\_version
destination
record\_status
trip\_type
experience\_level
party\_size
travel\_party
route\_plan
overnight\_area
y4\_plan
transport
booking\_status
park\_status
y2\_status
weather\_check
water\_check
emergency\_contact\_check
recommendation\_level
gear\_category
kb\_sections
product\_name
qty
unit\_price
discount\_percent
subtotal
discount\_amount
total
currency
rental\_or\_purchase
rental\_days
notes
safety\_flags
\`\`\`

จุดสำคัญ:

\- Destination ถูกล็อกเป็น **\*\*ดอยขุนตาล\*\***
\- รองรับทั้ง \`purchase\` และ \`rental\`
\- เชื่อมหมวดสินค้าเข้ากับ Section ใน KB
\- มี \`safety\_flags\`
\- ข้อมูล Dynamic เช่น Y2, อากาศ และน้ำ มีค่าเริ่มต้นเป็น \`unknown\` / \`not\_checked\`
\- ใช้ Google Sheets เป็น Sales Log
\- สามารถส่ง Notification ไป Telegram
\- ไม่เก็บข้อมูลโรคหรือข้อมูลสุขภาพส่วนบุคคลที่ไม่จำเป็นใน Sales Sheet

**---**

**## 3. \`agent\_harness.py\`**

**### เดิม**

Tool Schema ยังเป็น Domain เดิม และสามารถรับหลาย Destination รวมถึงมี \`porter\`

**### หลัง Pivot**

เปลี่ยนเป็น Agent / Tool Router สำหรับดอยขุนตาล

Actions หลัก:

\`\`\`text
log\_sale
generate\_checklist
send\_alert
no\_action
\`\`\`

ความสามารถหลัก:

\- ใช้ Gemini Structured Output เพื่อแปลงคำสั่งภาษาไทยเป็น Tool Decision
\- ล็อก Scope เป็นดอยขุนตาล
\- ไม่มี \`porter\`
\- มี Local Confirmation Gate
\- ไม่บันทึก Sale เพียงเพราะผู้ใช้ “ถาม” เรื่องสินค้า
\- จะเรียก \`sales\_logger.log\_sale()\` เมื่อผู้ใช้ยืนยันซื้อ/เช่าชัดเจนเท่านั้น
\- มี Checklist Generator
\- มี Telegram Alert
\- มี \`agent\_trace.jsonl\` สำหรับ Debug
\- มี \`--dry-run\`
\- มี \`--self-check\`
\- มี \`--json-output\`

ตัวอย่างคำสั่ง:

\`\`\`bash
python agent\_harness.py \\
  --cmd "ยืนยันซื้อไฟฉายคาดหัว 1 ชิ้น ราคา 590 บาท" \\
  --dry-run \\
  --json-output
\`\`\`

**---**

**## 4. RAG Knowledge Base**

**### เดิม**

\`\`\`text
menu\_kb.md
\`\`\`

เป็น Knowledge Base สำหรับเมนู/สินค้า MilkLab°

**### หลัง Pivot**

เปลี่ยนเป็น

\`\`\`text
trekking\_gear\_kb.md
\`\`\`

Master KB นี้เป็นฐานความรู้เฉพาะ **\*\*ดอยขุนตาล\*\***

ประกอบด้วย Section 0–84 โดยครอบคลุม

\- ภาพรวมดอยขุนตาล
\- การสะกด “ดอยขุนตาล” และ “สถานีรถไฟขุนตาน”
\- เส้นทาง Y1–Y4
\- ระยะทาง
\- ความสูง
\- ลักษณะเส้นทาง
\- การพัก Y2
\- การจอง
\- รถไฟ
\- น้ำ
\- อาหาร
\- กระเป๋า
\- รองเท้า
\- เสื้อผ้า
\- กันฝน
\- ไฟฉาย
\- Power bank
\- แผนที่ Offline
\- First Aid
\- Trekking Pole
\- Tent / Sleep System
\- การเดินกลางคืน
\- เทคนิคเดินขึ้น/ลง
\- ฤดูฝน
\- ทาก / แมลง
\- Solo
\- แผน 2 วัน 1 คืน
\- Daypack Y4
\- การซ้อม
\- Checklist
\- FAQ
\- Dynamic Data
\- Guardrail
\- อุณหภูมิ
\- สัญญาณโทรศัพท์
\- Emergency Plan
\- ห้องน้ำ
\- เวลาเดิน
\- สัตว์ป่า / งู
\- ค่าใช้จ่าย
\- เด็ก / ผู้สูงอายุ / โรคประจำตัว
\- Do / Don't
\- ทางเลือกการเดินทาง
\- Data Confidence
\- Source Hierarchy
\- Persona / Tone
\- Few-shot Dialogue
\- Risk Persistence
\- Quality Checklist

**---**

**## 5. \`app.py\`**

**### เดิม**

หน้า Chatbot และ Branding ยังอิงจาก MilkLab°

**### หลัง Pivot**

เปลี่ยนเป็น

\> **\*\*Trekking & Camping Buddy | ดอยขุนตาล\*\***

Architecture:

\`\`\`text
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
\`\`\`

จุดเด่น:

\- ใช้ multilingual embedding สำหรับคำถามภาษาไทย
\- ใช้ FAISS cosine similarity
\- Section 0 สารบัญไม่ถูกนำเข้า Vector Index
\- Section 65, 67, 79, 80, 81, 83, 84 เป็น Always-on Policy
\- มี Forced Safety Routing เช่นคำถาม Y4 / Solo / งู / ฉุกเฉิน
\- มี Dynamic Data detection
\- มี RAG Debug Mode
\- Cache จะสร้าง Index ใหม่เมื่อ KB ถูกแก้ไข
\- Chatbot ไม่อ้างว่าตรวจข้อมูลสด ถ้าระบบไม่มี Live Web Tool

**---**

**## 6. \`requirements.txt\`**

ปรับ Dependency ให้รองรับระบบใหม่ทั้งหมด

ประกอบด้วย

\`\`\`text
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
\`\`\`

ทำให้โปรเจกต์สามารถติดตั้ง Dependency หลักได้ด้วย

\`\`\`bash
python -m pip install -r requirements.txt
\`\`\`

**---**

**# Product / Service Catalog**

ระบบ Prototype นี้เน้นบริการ AI ก่อน และไม่ได้ Hard-code ราคาสินค้าจริงลงใน Knowledge Base

\| Service / Product | ราคา | หมายเหตุ |
\|---|---:|---|
\| Doi Khun Tan RAG Chatbot | ฟรี | ถามข้อมูลเตรียมทริปดอยขุนตาล |
\| Trekking Checklist Generator | ฟรี | สร้าง Checklist ตามบริบททริป |
\| Safety Planning Assistant | ฟรี | ช่วยเตรียมแผนลดความเสี่ยง |
\| Gear Recommendation | ฟรี | แนะนำหมวดอุปกรณ์ตาม KB |
\| Caption Generator | ฟรี | สร้าง Content สำหรับเพจ |
\| Purchase / Rental Logging | ตามราคาที่ผู้ใช้/ผู้ดูแลระบุ | ระบบไม่เดาราคาสินค้าเอง |
\| Telegram Notification | ฟรีใน Prototype | แจ้งรายการที่บันทึกจาก Agent |

**### ตัวอย่างหมวดอุปกรณ์ที่ Sales Logger รองรับ**

\`\`\`text
backpack
footwear
shelter
sleep\_system
rain\_gear
lighting
water
food
first\_aid
navigation
trekking\_pole
power
clothing
emergency\_safety
other
\`\`\`

\> ราคาและโปรโมชั่นสินค้าไม่ถูกเก็บเป็นข้อเท็จจริงถาวรใน KB  
\> เมื่อต้องบันทึก Sales Transaction ราคาจะต้องมาจาก Input ของผู้ใช้หรือระบบในขณะนั้น

**---**

**# Knowledge Base Design**

**## Data Confidence**

KB แบ่งข้อมูลออกเป็น 4 ประเภท

**### \`[STATIC]\`**

ข้อมูลค่อนข้างคงที่ เช่น

\- ชื่อสถานที่
\- ลำดับ Y1–Y4
\- หลักความปลอดภัยพื้นฐาน

**### \`[ESTIMATE]\`**

ข้อมูลประมาณการ เช่น

\- เวลาเดิน
\- ระดับความยาก
\- อุณหภูมิเพื่อวางแผนเสื้อผ้า

AI ต้องใช้คำว่า

\`\`\`text
ประมาณ
โดยทั่วไป
ควรเผื่อ
\`\`\`

**### \`[DYNAMIC]\`**

ข้อมูลที่เปลี่ยนได้ เช่น

\- เปิด/ปิด
\- ราคา
\- รถไฟ
\- อากาศ
\- Y2/Y4
\- น้ำ
\- ห้องน้ำ
\- ร้านค้า
\- สัญญาณโทรศัพท์
\- เวลาพระอาทิตย์ขึ้น
\- เบอร์ติดต่อ

AI ห้ามเดาข้อมูลเหล่านี้เป็นข้อมูลปัจจุบัน

**### \`[ANECDOTAL]\`**

ข้อมูลจากประสบการณ์ผู้เดินทาง ใช้เพื่อประกอบประสบการณ์ แต่ไม่ใช้แทนประกาศทางการ

**---**

**# Guardrails**

**## Scope Guardrail**

ถ้าผู้ใช้ถามรายละเอียดสถานที่อื่น:

\`\`\`text
ระบบนี้ออกแบบมาเพื่อให้ข้อมูลการเดินป่าดอยขุนตาลเท่านั้น
\`\`\`

และไม่แต่งข้อมูลเพิ่ม

**## Dynamic Data Guardrail**

ถ้าผู้ใช้ถาม

\`\`\`text
พรุ่งนี้ Y2 เปิดไหม
วันนี้รถไฟออกกี่โมง
ตอนนี้ค่าเช่าเต็นท์เท่าไร
พรุ่งนี้ฝนตกไหม
\`\`\`

ระบบต้องบอกว่าข้อมูลเปลี่ยนได้และควรตรวจสอบล่าสุดจากแหล่งทางการ

**## Safety Guardrail**

ระบบ

\- ไม่วินิจฉัยโรค
\- ไม่ปรับยา
\- ไม่รับรองว่าผู้ใช้ปลอดภัย 100%
\- ไม่สนับสนุนการฝ่าฝืนการปิดเส้นทาง
\- ให้ Safety Plan เมื่อผู้ใช้ยังยืนยันทำสิ่งที่เสี่ยง

**## Transaction Guardrail**

คำถาม:

\> “ไฟฉายราคา 590 ดีไหม”

ไม่ถือว่าเป็นคำสั่งซื้อ

คำสั่ง:

\> “ยืนยันซื้อไฟฉายคาดหัว 1 ชิ้น ราคา 590 บาท”

จึงสามารถผ่าน Confirmation Gate ไปยัง Sales Logger ได้

**---**

**# Conversation / User Flow**

ตัวอย่าง Flow หลัก

\`\`\`text
User
↓
ถามเรื่องดอยขุนตาล
↓
RAG ค้น Master KB
↓
Chatbot อธิบายข้อมูล
↓
ผู้ใช้ขอ Checklist
↓
Agent สร้าง Checklist
↓
แนะนำหมวดอุปกรณ์ตามบริบท
↓
ผู้ใช้ตัดสินใจซื้อ/เช่า
↓
Agent ตรวจ Explicit Confirmation
↓
sales\_logger.py
↓
Google Sheets
↓
Telegram Notification
\`\`\`

**---**

**# ตัวอย่าง Conversation**

**## Example 1 — Beginner Planning**

**\*\*User\*\***

\> ผมไม่เคยเดินป่ามาก่อน ดอยขุนตาลเหมาะไหม

**\*\*Expected Behavior\*\***

\- ดึง Section เรื่อง Beginner / Difficulty
\- อธิบายแบบมือใหม่เข้าใจง่าย
\- ไม่รับรองว่าทุกคนไปได้แน่นอน
\- แนะนำการซ้อมและการเตรียมอุปกรณ์

**---**

**## Example 2 — Y4**

**\*\*User\*\***

\> ถ้าจะขึ้น Y4 เช้ามืดต้องเอาอะไรไปบ้าง

**\*\*Expected Behavior\*\***

ระบบควรดึงข้อมูลเกี่ยวกับ

\- Daypack
\- น้ำ
\- ไฟฉายคาดหัว
\- ไฟสำรอง
\- เสื้อกันลม
\- เสื้อกันฝน
\- Power Bank
\- First Aid
\- ความหนาวช่วงเช้ามืด

**---**

**## Example 3 — Dynamic Data**

**\*\*User\*\***

\> พรุ่งนี้ Y2 เปิดไหม แล้วมีน้ำไหม

**\*\*Expected Behavior\*\***

ระบบต้องไม่เดาว่าเปิดหรือมีน้ำ

ควรตอบว่า

\- Y2 และน้ำเป็นข้อมูล Dynamic
\- ระบบไม่มี Live Web Check
\- ต้องตรวจล่าสุดจากช่องทางทางการก่อนเดินทาง

**---**

**## Example 4 — Safety**

**\*\*User\*\***

\> ผมจะไปคนเดียวแน่นอน ไม่ต้องห้าม ช่วยบอกว่าต้องทำอะไร

**\*\*Expected Behavior\*\***

\- ไม่ดุด่า
\- เตือนความเสี่ยงสั้น ๆ
\- ช่วยลดความเสี่ยง
\- แนะนำ Check-in
\- Offline Map
\- ไฟสำรอง
\- แจ้งเจ้าหน้าที่
\- Stop Conditions

**---**

**## Example 5 — Transaction**

**\*\*User\*\***

\> ยืนยันซื้อไฟฉายคาดหัว 1 ชิ้น ราคา 590 บาท

**\*\*Expected Behavior\*\***

\`\`\`text
Agent
↓
Structured Tool Decision
↓
Local Confirmation Gate
↓
log\_sale()
↓
Google Sheets
↓
Telegram
\`\`\`

**---**

**# Test Plan สำหรับ Session 4**

ก่อน Deploy ต้องทดสอบอย่างน้อย 5 คำถาม Domain ใหม่

\| # | คำถามทดสอบ | สิ่งที่ต้องตรวจ |
\|---|---|---|
\| 1 | ผมไม่เคยเดินป่ามาก่อน ดอยขุนตาลเหมาะไหม | Beginner answer + KB grounding |
\| 2 | ขึ้น Y4 เช้ามืดต้องเอาอะไรไปบ้าง | Retrieval ของ Y4 / Daypack / Headlamp |
\| 3 | พรุ่งนี้ Y2 เปิดไหม แล้วมีน้ำไหม | Dynamic guardrail ไม่ Hallucinate |
\| 4 | ผมจะไปคนเดียวแน่นอน ต้องเตรียมอะไร | Risk Persistence + Safety Plan |
\| 5 | ช่วยจัด Checklist ดอยขุนตาล 2 วัน 1 คืน | Checklist ครบและตรง Scope |

**### Test Status**

\> **\*\*ผลทดสอบบน Streamlit Deploy จริง:\*\*** PASS ทั้ง 5 คำถาม

\| # | Result | Note |
\|---|---|---|
\| 1 | ✅ PASS | Beginner answer + KB grounding ทำงานถูกต้อง |
\| 2 | ✅ PASS | Retrieval เรื่อง Y4 / Daypack / Headlamp ทำงานถูกต้อง |
\| 3 | ✅ PASS | Dynamic Guardrail ทำงาน และไม่เดาข้อมูลสด |
\| 4 | ✅ PASS | Risk Persistence + Safety Plan ทำงานถูกต้อง |
\| 5 | ✅ PASS | Checklist ตรง Scope ดอยขุนตาล |

**---**

**# Technology Stack**

\`\`\`text
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
dotenv
pytest
\`\`\`

**---**

**# Repository Structure**

\`\`\`text
project/
│
├── app.py
├── caption\_generator.py
├── sales\_logger.py
├── agent\_harness.py
├── trekking\_gear\_kb.md
├── requirements.txt
├── PIVOT.md
├── README.md
├── agent\_trace.jsonl
└── .env
\`\`\`

\> \`.env\` ต้องไม่ Commit API Key หรือ Secret ขึ้น GitHub

**---**

**# Deployment**

**## Streamlit Community Cloud**

ระบบถูก Deploy เป็น Public App ด้วย Streamlit Community Cloud จาก GitHub repository ของโปรเจกต์

**### Deploy URL**

https://trekking-camping-buddy.streamlit.app

**### Deploy Configuration**

\`\`\`text
Repository: parinthon11202-commits/milklab-parinthon
Deploy Branch: pivot
Main file path: app.py
Platform: Streamlit Community Cloud
\`\`\`

**### Deploy Checklist**

\- [x] Push branch \`pivot\`
\- [x] ตรวจ \`requirements.txt\`
\- [x] ตั้ง Streamlit Secrets
\- [x] ตั้ง Gemini API Key ผ่าน Streamlit Secrets โดยไม่ Commit ลง GitHub
\- [x] Deploy บน Streamlit Community Cloud
\- [x] เปิดหน้า App จาก Public URL ได้
\- [x] ทดสอบ 5 คำถาม Domain ใหม่
\- [x] Test PASS 5/5
\- [x] ไม่มี MilkLab° reference ใน UI หลัก
\- [x] ไม่มี API Key หรือ Secret ถูก Commit ใน GitHub

**### URL สำหรับส่งใน S4 Worksheet — Question 1**

\`\`\`text
https://trekking-camping-buddy.streamlit.app
\`\`\`

**---**

**# Pull Request**

**## Branch**

\`\`\`text
release/demo-day
\`\`\`

**## Target**

\`\`\`text
main
\`\`\`

**## PR Direction**

\`\`\`text
release/demo-day → main
\`\`\`

**## PR Title**

\`\`\`text
Pivot to Trekking & Camping Buddy
\`\`\`

**## PR Body**

PR ต้องอธิบาย Pivot อย่างน้อย 1 บรรทัด โดยสามารถใช้ข้อความนี้ได้:

\`\`\`text
Pivot จาก MilkLab° เป็น Trekking & Camping Buddy ซึ่งเป็น AI RAG Chatbot
สำหรับนักเดินป่ามือใหม่ที่วางแผนไปดอยขุนตาล พร้อม Knowledge Base,
Safety Guardrails, Checklist, Agent Tool Router และ Sales/Rental Logger
สำหรับ Domain ใหม่
\`\`\`

Deploy URL:

\`\`\`text
https://trekking-camping-buddy.streamlit.app
\`\`\`

รายละเอียดเพิ่มเติมใช้เนื้อหาจาก \`PIVOT.md\` นี้ได้

**### PR Requirement ก่อนส่ง**

\- [x] สร้าง branch \`release/demo-day\`
\- [x] Push branch \`release/demo-day\` ขึ้น GitHub
\- [ ] เปิด Pull Request จาก \`release/demo-day\` เข้า \`main\`
\- [ ] มี Reviewer ใน Cohort Comment อย่างน้อย 1 ข้อ
\- [ ] Merge Pull Request เข้า \`main\`
\- [ ] Copy PR URL หลังเปิด PR

**### PR URL**

\`\`\`text
TODO: ใส่ GitHub Pull Request URL หลังเปิด PR
\`\`\`

**### URL สำหรับส่งใน S4 Worksheet — Question 2**

\`\`\`text
TODO: ใส่ URL ของ PR release/demo-day ที่มี reviewer comment และ merge เข้า main แล้ว
\`\`\`

**---**

**# Peer Review**

เพื่อให้ครอบคลุมทั้งโจทย์ Session 4 และ S4 Worksheet ให้ทำ 2 ส่วน

**## A. ให้เพื่อนใน Cohort Review PR ของเรา**

PR \`release/demo-day → main\` ต้องมี Reviewer ใน Cohort Comment อย่างน้อย 1 ข้อก่อน Merge

ตัวอย่าง Comment ที่เพื่อนสามารถใช้เป็นแนวทาง:

\> จุดเด่นของโปรเจกต์นี้คือ Scope ดอยขุนตาลชัดเจน และมี Guardrail ป้องกันการเดาข้อมูล Dynamic เช่น สถานะ Y2 น้ำ อากาศ และรถไฟ

หลังมี Comment แล้วจึง Merge PR เข้า \`main\`

**## B. Review PR ของเพื่อนอย่างน้อย 1 คน**

Comment อย่างน้อย 3 ประเภท

**### Strength**

ตัวอย่าง:

\> จุดที่ทำได้ดีคือ Domain ชัดและเห็นการเปลี่ยน Schema/Prompt จาก MilkLab° ชัดเจนครับ

**### Question**

ตัวอย่าง:

\> ถ้าข้อมูลที่เปลี่ยนตามเวลา เช่น ราคา หรือสถานะบริการเปลี่ยน ระบบมีวิธีป้องกันข้อมูลเก่าอย่างไรครับ

**### Suggestion**

ตัวอย่าง:

\> แนะนำให้เพิ่ม Test Case สำหรับคำถามที่อยู่นอก Domain เพื่อดูว่า Chatbot ปฏิเสธได้ถูกต้องหรือไม่ครับ

**### หลักฐาน**

\`\`\`text
TODO: แนบ Screenshot Comment Peer Review ใน S4 Worksheet
\`\`\`

**### Peer Review Checklist**

\- [ ] PR ของเรามี Cohort Reviewer Comment อย่างน้อย 1 ข้อ
\- [ ] Review PR ของเพื่อนอย่างน้อย 1 คน
\- [ ] มี Strength อย่างน้อย 1 ข้อ
\- [ ] มี Question อย่างน้อย 1 ข้อ
\- [ ] มี Suggestion อย่างน้อย 1 ข้อ
\- [ ] Screenshot หลักฐานเก็บไว้แล้ว

**---**

**# Reflection**

**## สิ่งที่ได้เรียนรู้จากการ Pivot**

การ Pivot จาก MilkLab° มาเป็น Trekking & Camping Buddy ทำให้เห็นว่า Pattern หลักของระบบ AI สามารถนำไปใช้กับ Domain อื่นได้ โดยไม่จำเป็นต้องสร้างทุกอย่างใหม่จากศูนย์

สิ่งที่เปลี่ยนจริงไม่ใช่แค่ชื่อหน้าเว็บ แต่ต้องเปลี่ยน

\- Prompt
\- Knowledge Base
\- RAG Retrieval
\- Tool Schema
\- Transaction Schema
\- Guardrail
\- Persona
\- Error Handling
\- Test Cases
\- UX ของคำตอบ

สิ่งที่เรียนรู้มากที่สุดคือ **\*\*ข้อมูลแต่ละ Domain มีระดับความน่าเชื่อถือไม่เหมือนกัน\*\***

ใน Domain เดินป่า ข้อมูลบางอย่าง เช่น เส้นทางพื้นฐานสามารถเก็บใน KB ได้ แต่ข้อมูลอย่างสถานะเปิด/ปิด น้ำ อากาศ ราคา และรถไฟสามารถเปลี่ยนได้ จึงไม่ควรให้ AI เดาจากข้อมูลเก่า

จึงเพิ่มแนวคิด

\`\`\`text
STATIC
ESTIMATE
DYNAMIC
ANECDOTAL
\`\`\`

เพื่อช่วยควบคุมวิธีที่ AI ใช้ข้อมูล

อีกสิ่งที่ได้เรียนรู้คือ RAG อย่างเดียวไม่เพียงพอสำหรับกฎสำคัญ เพราะ Vector Search อาจไม่ดึง Guardrail Section ทุกครั้ง จึงย้ายกฎสำคัญ เช่น Scope, Dynamic Data, Persona และ Safety ไปเป็น **\*\*Always-on System Policy\*\***

ในส่วน Agent ได้เรียนรู้เรื่อง Side Effect ว่า AI ไม่ควรเขียนข้อมูลลง Google Sheets เพียงเพราะตีความว่าผู้ใช้สนใจสินค้า จึงเพิ่ม Local Confirmation Gate และให้ \`sales\_logger.py\` เป็นจุดเดียวที่เขียน Transaction

จากโปรเจกต์นี้จึงได้ฝึกทั้ง

\- RAG
\- Prompt Engineering
\- Structured Output
\- Agent / Tool Routing
\- Guardrail
\- Sales Logging
\- API Integration
\- UX
\- Safety Design
\- Testing
\- Deployment workflow

**---**

**# จุดที่แตกต่างจาก MilkLab° อย่างชัดเจน**

MilkLab° เป็นระบบสำหรับสินค้า/เมนูในร้านเครื่องดื่ม

Trekking & Camping Buddy เป็นระบบที่ต้องจัดการข้อมูลหลายประเภทมากขึ้น เช่น

\`\`\`text
Route
Distance
Elevation
Gear
Weather preparation
Water
Camping
Safety
Emergency
Solo risk
Dynamic park status
Transaction
\`\`\`

จึงต้องเพิ่ม Guardrail และ Safety Logic มากกว่าระบบเดิม

**---**

**# Main System Goal**

เป้าหมายของ **\*\*Trekking & Camping Buddy\*\*** คือ

\> **\*\*ช่วยให้นักเดินป่ามือใหม่ที่ต้องการไปดอยขุนตาล สามารถเข้าใจเส้นทาง วางแผนทริป เตรียมอุปกรณ์ ตรวจความเสี่ยง และออกเดินทางได้อย่างเป็นระบบมากขึ้น โดย AI ต้องไม่สร้างความมั่นใจเกินข้อมูลที่มี\*\***

แกนหลักของระบบคือ

\`\`\`text
Doi Khun Tan Knowledge Base
\+
RAG Chatbot
\+
Checklist Generator
\+
Safety Guardrails
\+
Agent Tool Router
\+
Sales / Rental Logger
\+
Caption Generator
\`\`\`

**---**

**# Session 4 Deliverable Status**

\| Deliverable | Status |
\|---|---|
\| Pivot Domain | ✅ Trekking & Camping Buddy |
\| \`caption_generator.py\` | ✅ Pivot แล้ว |
\| \`sales_logger.py\` | ✅ Pivot แล้ว |
\| \`agent_harness.py\` | ✅ Pivot แล้ว |
\| RAG KB | ✅ \`trekking_gear_kb.md\` |
\| \`app.py\` branding + RAG | ✅ Pivot แล้ว |
\| \`requirements.txt\` | ✅ อัปเดตแล้ว |
\| \`PIVOT.md\` | ✅ อัปเดตแล้ว |
\| Test 5 questions | ✅ PASS 5/5 |
\| Streamlit Community Cloud | ✅ Deploy แล้ว |
\| Deploy URL | ✅ https://trekking-camping-buddy.streamlit.app |
\| branch \`release/demo-day\` | ✅ สร้างและ Push แล้ว |
\| PR \`release/demo-day\` → \`main\` | ⬜ ต้องเปิด |
\| Cohort Reviewer Comment ใน PR | ⬜ ต้องมีอย่างน้อย 1 ข้อ |
\| Merge PR เข้า \`main\` | ⬜ ต้องทำหลัง Reviewer Comment |
\| PR URL | ⬜ ต้องใส่ |
\| Review PR ของเพื่อน | ⬜ ต้องทำ |
\| Peer Review Screenshot | ⬜ ต้องแนบ |
\| Reflection | ✅ Draft พร้อมใช้ |

**---**

**## Final Note**

ไฟล์นี้สะท้อนเวอร์ชันปัจจุบันของ **Trekking & Camping Buddy** ซึ่งจำกัด Scope เป็นดอยขุนตาล และ Deploy ใช้งานจริงบน Streamlit Community Cloud แล้ว

**Deploy URL**

\`\`\`text
https://trekking-camping-buddy.streamlit.app
\`\`\`

ระบบผ่านการทดสอบ Domain ใหม่ **5/5 คำถาม**

สิ่งที่ยังเหลือก่อนส่ง S4 ให้ครบ:

1\. เปิด PR \`release/demo-day → main\`
2\. ให้ Reviewer ใน Cohort Comment อย่างน้อย 1 ข้อ
3\. Merge PR เข้า \`main\`
4\. นำ PR URL มาใส่ในไฟล์นี้และ S4 Worksheet
5\. Review PR ของเพื่อน และเก็บ Screenshot Comment เป็นหลักฐาน

เมื่อครบ 5 ข้อนี้ Deliverable ของ Session 4 จะครบตามโจทย์ที่กำหนด
