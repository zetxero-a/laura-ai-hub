# Laura AI Hub

แอป Flask ตั้งต้น

## เริ่มต้นใช้งาน

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python run.py
```

เปิดเบราว์เซอร์ที่ http://127.0.0.1:5000/

## โครงสร้าง

```
app/
  __init__.py      # create_app() – application factory
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
| GET    | `/api/health` | ตรวจสถานะเซิร์ฟเวอร์                 |
| POST   | `/api/echo`   | รับ `{"message": "..."}` แล้วตอบกลับ (ตัวอย่าง รอเปลี่ยนเป็น AI จริง) |

## ทดสอบ

```bash
pytest
```

## ตั้งค่า (ตัวแปรสภาพแวดล้อม)

- `PORT` (ค่าเริ่มต้น 5000), `HOST` (ค่าเริ่มต้น 127.0.0.1)
- `FLASK_DEBUG=0` เพื่อปิดโหมด debug
- `SECRET_KEY` ควรตั้งค่าเองเมื่อนำไปใช้งานจริง
