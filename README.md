# Laura AI Hub

แอป Flask พร้อมแชตกับ Laura ผู้ช่วย AI ที่ใช้ Claude API

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
  ai.py            # เรียก Claude API
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
| POST   | `/api/chat`   | รับ `{"message": "...", "history": [...]}` แล้วตอบ `{"reply": "..."}` จาก Claude |

## ทดสอบ

```bash
pytest
```

เทสต์ใช้ Claude ปลอม จึงไม่ต้องมี API key และไม่เสียค่าใช้จ่าย

## ตั้งค่า (ตัวแปรสภาพแวดล้อม หรือไฟล์ `.env`)

- `ANTHROPIC_API_KEY` **(จำเป็น)** คีย์สำหรับเรียก Claude API
- `CLAUDE_MODEL` (ค่าเริ่มต้น `claude-opus-5-5`)

- `PORT` (ค่าเริ่มต้น 5000), `HOST` (ค่าเริ่มต้น 127.0.0.1)
- `FLASK_DEBUG=1` เพื่อเปิดโหมด debug (ปิดเป็นค่าเริ่มต้น ห้ามเปิดเมื่อตั้ง `HOST=0.0.0.0`)
- `SECRET_KEY` ควรตั้งค่าเองเมื่อนำไปใช้งานจริง
