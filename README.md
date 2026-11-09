# Laura AI Hub

แอป Flask พร้อมแชตกับ Laura ผู้ช่วย AI ที่ใช้ Claude API

Laura เป็นผู้ประสานงาน: อ่านข้อความแล้วตัดสินใจเองว่าจะตอบเลย หรือส่งงานให้ทีม

| Agent | ทำอะไร |
|---|---|
| 💡 idea | เปลี่ยนความคิดยุ่งๆ ให้เป็นการ์ดไอเดีย พร้อมสมมติฐานและคำถามที่ต้องหาข้อมูล |
| 🔎 research | ค้นเว็บแล้วเขียนรายงานพร้อมแหล่งอ้างอิง (ใช้เวลา 1–3 นาที) |

```
หน้าเว็บ ─▶ /api/chat ─▶ Laura (Claude + tools)
                            ├─ ask_idea      ─▶ Claude (system prompt ของ idea)
                            └─ ask_research  ─▶ Claude + web search
```

ผลงานของ agent แสดงใต้ข้อความของ Laura และถูกส่งกลับไปในประวัติแชต
จึงพูดต่อได้ เช่น "ส่งการ์ดนี้ให้ research ต่อ"

> ในเซสชัน Claude Code ของ repo นี้ ไฟล์ `CLAUDE.md` ทำให้ Claude รับบท Laura
> และใช้ทีม agent จากปลั๊กอิน `personal-assistant-team` ด้วย

## เริ่มต้นใช้งาน

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env             # Windows: copy .env.example .env
# แก้ไฟล์ .env ใส่ ANTHROPIC_API_KEY ของคุณ (สร้างได้ที่ https://platform.claude.com/)
python run.py
```

เปิดเบราว์เซอร์ที่ http://127.0.0.1:5000/

## โครงสร้าง

```
app/
  __init__.py      # create_app() – application factory
  ai.py            # Laura: system prompt + วงจรส่งงานให้ agent
  agents.py        # agent idea และ research
  ai_client.py     # Claude client, ชื่อรุ่น, การจัดการ error
  routes.py        # หน้าเว็บและ API
  templates/       # Jinja2 templates
  static/          # CSS / JS
tests/             # pytest
run.py             # จุดเริ่มรันเซิร์ฟเวอร์
```

## Endpoints

| Method | Path          | คำอธิบาย                          |
|--------|---------------|-----------------------------------|
| GET    | `/`           | หน้าแรก                            |
| GET    | `/api/health` | ตรวจสถานะเซิร์ฟเวอร์ และบอกว่าตั้ง API key แล้วหรือยัง |
| POST   | `/api/chat`   | รับ `{"message": "...", "history": [...]}` ตอบ `{"reply": "...", "handoffs": [{"agent", "label", "output"}]}` |

## ค่าใช้จ่าย

ข้อความที่ Laura ตอบเองเรียก Claude 1 ครั้ง ถ้าส่งให้ agent จะเรียก 3 ครั้งขึ้นไป
research แพงที่สุดเพราะค้นเว็บหลายรอบและคิดลึก (effort `high`)
ปรับระดับได้ใน `app/agents.py`

## ทดสอบ

```bash
pytest
```

เทสต์ใช้ Claude ปลอม จึงไม่ต้องมี API key และไม่เสียค่าใช้จ่าย

## ตั้งค่า (ตัวแปรสภาพแวดล้อม หรือไฟล์ `.env`)

- `ANTHROPIC_API_KEY` **(จำเป็น)** คีย์สำหรับเรียก Claude API
- `CLAUDE_MODEL` (ค่าเริ่มต้น `claude-opus-5-5`)
- `APP_PASSWORD` ถ้าตั้งไว้ เบราว์เซอร์จะถามรหัสผ่านก่อนเข้าแอป (ชื่อผู้ใช้ใส่อะไรก็ได้)
  ต้องตั้งทุกครั้งที่เปิดให้คนอื่นเข้าถึงได้ และควรใช้ผ่าน HTTPS เพราะรหัสผ่านถูกส่งแบบไม่เข้ารหัส
  `/api/health` ไม่ต้องใช้รหัสผ่าน

- `PORT` (ค่าเริ่มต้น 5000), `HOST` (ค่าเริ่มต้น 127.0.0.1)
- `FLASK_DEBUG=1` เพื่อเปิดโหมด debug (ปิดเป็นค่าเริ่มต้น ห้ามเปิดเมื่อตั้ง `HOST=0.0.0.0`)
- `SECRET_KEY` ควรตั้งค่าเองเมื่อนำไปใช้งานจริง
