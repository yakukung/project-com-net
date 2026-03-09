# AI Network ChatRoom 🤖💬

โปรเจกต์แชทรูมผ่าน Network ที่รองรับการพูดคุยแบบกลุ่ม, กระซิบ (DM) และมี AI Assistant คอยช่วยเหลือ

## 🚀 การติดตั้ง (Installation)

1. **สร้าง Virtual Environment**

   ```bash
   python -m venv venv
   ```

   - **หรือ**
     ```bash
     python3 -m venv venv
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

4. **ตั้งค่า Environment Variables**
   - เปลี่ยนชื่อไฟล์จาก `exam.env` เป็น `.env`
   - เปิดไฟล์ `.env` และเอา API Key มาใส่ให้ถูกต้อง:
     ```env
     GEMINI_API_KEY=ใส่_GEMINI_API_KEY_ที่นี่
     GROQ_API_KEY=ใส่_GROQ_API_KEY_ที่นี่
     ```
   - **แหล่งข้อมูล:**
     - Gemini API Key: [Google AI Studio](https://aistudio.google.com/)
     - Groq API Key: [Groq Console](https://console.groq.com/keys)

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
