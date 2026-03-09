# AI Network ChatRoom 🤖💬

โปรเจกต์แชทรูมผ่าน Network ที่รองรับการพูดคุยแบบกลุ่ม, กระซิบ (DM) และมี AI Assistant คอยช่วยเหลือ

## 🚀 การติดตั้ง (Installation)

1. **สร้าง Virtual Environment (แนะนำ)**

   ```bash
   python -m venv venv
   ```

2. **Activate Virtual Environment**
   - **Mac/Linux:**
     ```bash
     source venv/bin/activate
     ```
   - **Windows:**
     ```bash
     venv\Scripts\activate
     ```

3. **ติดตั้ง Library ที่จำเป็น**
   ```bash
   pip install -r requirements.txt
   ```

## 🛠️ วิธีการใช้งาน (Usage)

### 1. รันฝั่ง Server

เปิด Terminal ใหม่แล้วรันคำสั่ง:

```bash
python run_server.py
```

_Server จะเริ่มทำงานที่ Port 5000 (ค่าเริ่มต้น)_

### 2. รันฝั่ง Client

เปิดอีก Terminal หนึ่งแล้วรันคำสั่ง:

```bash
python run_client.py
```

_คุณสามารถเปิด Client หลายหน้าต่างเพื่อทดสอบการคุยระหว่างกันได้_

## ✨ ฟีเจอร์หลัก

- **Group Chat:** คุยรวมในห้องแชทหลัก
- **Direct Message:** คลิกที่ชื่อเพื่อนเพื่อเริ่มคุยส่วนตัว
- **AI Integration:** พิมพ์ `@ai` ตามด้วยข้อความเพื่อคุยกับ AI
- **Custom Groups:** สร้างห้องแชทเฉพาะกลุ่มเองได้
