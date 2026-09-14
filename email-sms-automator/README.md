# email-sms-automator: Automated Communications with Python

โปรเจค Python สำหรับสาธิตและใช้งานระบบสื่อสารอัตโนมัติ (Automated Communication System) ครอบคลุมการส่งอีเมล (SMTP พร้อม TLS, Plain Text/HTML และไฟล์แนบ), การส่ง SMS ผ่าน Carrier Email-to-SMS Gateway และการรับ/ค้นหา/ประมวลผลอีเมลที่เข้ามา (IMAP พร้อมการดาวน์โหลดไฟล์แนบอัตโนมัติ) โดยเน้นความปลอดภัยระดับสูงสุดด้วยการจัดการ Credential ผ่าน Environment Variables

---

## สารบัญ (Table of Contents)
1. [ภาพรวมโปรเจค (Project Overview)](#ภาพรวมโปรเจค-project-overview)
2. [แนวคิดหลักที่สาธิต (Key Concepts Demonstrated)](#แนวคิดหลักที่สาธิต-key-concepts-demonstrated)
3. [โครงสร้างโปรเจค (Project Structure)](#โครงสร้างโปรเจค-project-structure)
4. [ข้อกำหนดระบบ (Prerequisites)](#ข้อกำหนดระบบ-prerequisites)
5. [การติดตั้งและตั้งค่า Environment (Installation & Setup)](#การติดตั้งและตั้งค่า-environment-installation--setup)
6. [ขั้นตอนการสร้าง Gmail App Password (สำคัญมาก)](#ขั้นตอนการสร้าง-gmail-app-password-สำคัญมาก)
7. [การตั้งค่าไฟล์ `.env` (Configuration)](#การตั้งค่าไฟล์-env-configuration)
8. [การรันโปรแกรม (How to Run)](#การรันโปรแกรม-how-to-run)
9. [การทดสอบด้วย Unit Tests (Automated Testing)](#การทดสอบด้วย-unit-tests-automated-testing)
10. [ตารางการแก้ไขปัญหา (Troubleshooting Guide)](#ตารางการแก้ไขปัญหา-troubleshooting-guide)
11. [แนวคิดการพัฒนาต่อยอด (Extension Ideas & Future Work)](#แนวคิดการพัฒนาต่อยอด-extension-ideas--future-work)

---

## ภาพรวมโปรเจค (Project Overview)
ในยุคปัจจุบัน การสื่อสารแบบอัตโนมัติมีความสำคัญอย่างยิ่งสำหรับระบบแจ้งเตือน (Notifications), ระบบส่งรายงานสรุปยอดประจำวัน (Daily Digest / Reports), ระบบตรวจสอบสถานะเซิร์ฟเวอร์ (Alerts) และระบบบริการลูกค้า (Customer Communications)

โปรเจคนี้ถูกออกแบบตามหลักการ **Clean Architecture** และ **Separation of Concerns (SoC)** โดยแยกส่วนประกอบหลักออกเป็นโมดูลอิสระ ใช้ Standard Library ของ Python (ได้แก่ `smtplib`, `imaplib`, `email`) ร่วมกับ `python-dotenv` สำหรับโหลดตัวแปรสภาพแวดล้อม ทำให้ไม่มี dependency ภายนอกที่ไม่จำเป็นและมีความปลอดภัยสูง

---

## แนวคิดหลักที่สาธิต (Key Concepts Demonstrated)

1. **Email Sending (SMTP Protocol)**:
   - เชื่อมต่อไปยัง SMTP Server (เช่น Gmail SMTP: `smtp.gmail.com:587`)
   - เข้ารหัสช่องทางการสื่อสารด้วย STARTTLS เพื่อความปลอดภัยของข้อมูล
   - พิสูจน์ตัวตน (Authentication) ผ่าน App Password
   - สร้างข้อความแบบหลายส่วน (`email.mime.multipart.MIMEMultipart`) รองรับทั้งเนื้อหา Plain Text, HTML และไฟล์แนบ (`MIMEApplication`)
   - ระบบ Error Handling ที่ชาญฉลาด: หากไฟล์แนบไม่พบ โปรแกรมจะแจ้งเตือน (Warning/Error) และยังคงส่งเนื้อหาอีเมลต่อไปได้โดยไม่หยุดชะงัก

2. **Email Receiving & Parsing (IMAP Protocol)**:
   - เชื่อมต่อไปยัง IMAP Server ผ่านพอร์ต SSL ปลอดภัย (`imaplib.IMAP4_SSL`)
   - ค้นหาอีเมลตามเงื่อนไข (Search Criteria) เช่น `UNSEEN` (ยังไม่ได้อ่าน), กรองตามอีเมลผู้ส่ง (`FROM`) และหัวข้ออีเมล (`SUBJECT`)
   - ถอดรหัสหัวข้ออีเมลและชื่อผู้ส่งด้วย `email.header.decode_header` รองรับมาตรฐาน MIME Encoded-Word (เช่น UTF-8, Base64, ISO-8859-1)
   - เดินท่องโครงสร้าง MIME (`msg.walk()`) เพื่อแยกชิ้นส่วนข้อความ (Text Body) และไฟล์แนบ (Attachments)
   - บันทึกไฟล์แนบลงไดเรกทอรีที่กำหนดโดยอัตโนมัติ
   - ทำเครื่องหมายว่าอ่านแล้ว (`\Seen`) หลังประมวลผลสำเร็จ

3. **SMS via Email-to-SMS Gateway**:
   - หลักการทำงาน: ผู้ให้บริการเครือข่ายโทรศัพท์มือถือ (โดยเฉพาะในสหรัฐฯ และบางประเทศ) มักจะมีเกตเวย์แปลงอีเมลเป็น SMS เช่น `1234567890@txt.att.net`
   - คลาส `SMSGateway` รองรับการจับคู่เครือข่ายอัตโนมัติ (AT&T, Verizon, T-Mobile, Sprint, Boost Mobile, Cricket, US Cellular) หรือระบุอีเมลเกตเวย์โดยตรง
   - ส่ง SMS โดยไม่ระบุ Subject เพื่อป้องกันการแสดงผลผิดพลาดบนโทรศัพท์มือถือ

4. **Secure Credential Handling**:
   - ป้องกันการรั่วไหลของรหัสผ่าน โดยห้าม Hardcode ข้อมูลสำคัญลงในซอร์สโค้ดเด็ดขาด
   - จัดเก็บข้อมูลผ่าน Environment Variables ในไฟล์ `.env` (และถูกละเว้นใน `.gitignore`)
   - มีไฟล์ตัวอย่าง `.env.example` กำกับทุกตัวแปรพร้อมคำอธิบาย

5. **Production-grade Logging**:
   - ใช้โมดูลมาตรฐาน `logging` แสดงผลพร้อม Timestamp, Logger Name, Log Level และรายละเอียดเหตุการณ์ แทนการใช้ `print()`

---

## โครงสร้างโปรเจค (Project Structure)

```
email-sms-automator/
├── src/
│   ├── __init__.py          # เครื่องหมายระบุ Python Package
│   ├── email_sender.py      # คลาส EmailSender จัดการส่งอีเมลผ่าน SMTP
│   ├── email_receiver.py    # คลาส EmailReceiver จัดการรับ/ค้นหา/อ่านอีเมลผ่าน IMAP
│   ├── sms_gateway.py       # คลาส SMSGateway จัดการส่งข้อความ SMS ผ่าน Email Gateway
│   └── utils.py             # ฟังก์ชันช่วย: ระบบ Logging, อ่านค่า Environment, จัดการโฟลเดอร์
├── data/
│   ├── attachments/         # โฟลเดอร์สำหรับเก็บไฟล์แนบที่ดาวน์โหลดจากอีเมล
│   │   └── .gitkeep
│   └── dummy_report.pdf     # ไฟล์ตัวอย่าง PDF สำหรับทดสอบการแนบไฟล์
├── tests/
│   └── test_automator.py    # Unit Test Suite จำลองการทำงานทุกโมดูลแบบ Offline
├── .env.example             # ไฟล์ตัวอย่างสำหรับตั้งค่า Environment Variables
├── .gitignore               # กำหนดรายการไฟล์ที่ไม่ต้องการ commit ขึ้น Git
├── main.py                  # สคริปต์หลักรัน Workflow อัตโนมัติทั้ง 4 Tasks
├── requirements.txt         # รายการแพ็กเกจภายนอก (python-dotenv)
└── README.md                # คู่มือการใช้งานอย่างละเอียด
```

---

## ข้อกำหนดระบบ (Prerequisites)
- Python 3.9 หรือเวอร์ชันที่ใหม่กว่า (รองรับได้ถึง Python 3.14+)
- บัญชีอีเมล (แนะนำ Gmail) ที่เปิดใช้งาน 2-Step Verification (2FA) แล้ว

---

## การติดตั้งและตั้งค่า Environment (Installation & Setup)

### 1. เข้าสู่โฟลเดอร์โปรเจค
```bash
cd email-sms-automator
```

### 2. สร้าง Virtual Environment และเปิดใช้งาน
- **บน Windows (PowerShell / Command Prompt):**
  ```powershell
  python -m venv venv
  .\venv\Scripts\activate
  ```
- **บน macOS / Linux:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 3. ติดตั้ง Dependencies
```bash
pip install -r requirements.txt
```
*(หรือ `pip install python-dotenv`)*

---

## ขั้นตอนการสร้าง Gmail App Password (สำคัญมาก)

> ⚠️ **คำเตือน**: Google ไม่อนุญาตให้ใช้รหัสผ่านบัญชี Google ทั่วไปในการล็อกอินผ่านโปรแกรมภายนอก ต้องสร้าง **"App Password" (รหัสผ่านสำหรับแอป)** ขนาด 16 หลักเท่านั้น

1. ล็อกอินเข้าสู่บัญชี Google แล้วไปที่: [https://myaccount.google.com/](https://myaccount.google.com/)
2. เลือกเมนูด้านซ้าย **"Security" (ความปลอดภัย)**
3. ในส่วน "How you sign in to Google" (วิธีลงชื่อเข้าใช้ Google) ตรวจสอบให้แน่ใจว่า **2-Step Verification (การยืนยันแบบ 2 ขั้นตอน)** ถูกเปิดใช้งานแล้ว
4. ค้นหาคำว่า **"App passwords"** หรือคลิกเข้าไปที่เมนูรหัสผ่านสำหรับแอป
5. ตั้งชื่อแอป เช่น `Python Automator` แล้วกด **Create (สร้าง)**
6. ระบบจะแสดงรหัสผ่าน 16 ตัวอักษร (เช่น `abcd efgh ijkl mnop`)
7. คัดลอกรหัสผ่านนี้ไปใช้ในตัวแปร `SENDER_APP_PASSWORD` ในไฟล์ `.env` (สามารถใส่ติดกัน 16 ตัวโดยไม่ต้องเว้นวรรค)

---

## การตั้งค่าไฟล์ `.env` (Configuration)

คัดลอกไฟล์ `.env.example` ไปเป็น `.env`:
- **Windows:**
  ```cmd
  copy .env.example .env
  ```
- **macOS / Linux:**
  ```bash
  cp .env.example .env
  ```

จากนั้นเปิดไฟล์ `.env` แล้วกรอกข้อมูลจริง:

```ini
# ข้อมูลผู้ส่ง (Sender Credentials)
SENDER_EMAIL=your_email@gmail.com
SENDER_APP_PASSWORD=abcdefghijklmnop
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
IMAP_SERVER=imap.gmail.com

# ผู้รับสำหรับทดสอบส่งอีเมล (Recipient for test emails)
TEST_RECIPIENT_EMAIL=another_email@example.com

# ผู้รับสำหรับทดสอบส่ง SMS (Phone number & carrier key)
TEST_SMS_PHONE_NUMBER=1234567890
TEST_SMS_CARRIER=att
```

> 🔒 **Security Notice**: ไฟล์ `.env` มีข้อมูลรหัสผ่านจริง ห้าม commit ไฟล์นี้ขึ้น Git หรือ Public Repository เด็ดขาด (โปรเจคได้ใส่ `.env` ไว้ใน `.gitignore` เรียบร้อยแล้ว)

---

## การรันโปรแกรม (How to Run)

รันสคริปต์หลัก:
```bash
python main.py
```

### ลำดับขั้นตอนการทำงานของสคริปต์ (Workflow 4 Tasks):
1. **Task 1**: ส่งอีเมลแบบ Plain Text ธรรมดาไปยัง `TEST_RECIPIENT_EMAIL`
2. **Task 2**: ส่งอีเมลพร้อมไฟล์แนบ `data/dummy_report.pdf` ไปยัง `TEST_RECIPIENT_EMAIL`
3. **Task 3**: ส่ง SMS ไปยังหมายเลข `TEST_SMS_PHONE_NUMBER` ผ่าน Gateway ของเครือข่ายที่ระบุ
4. **Task 4**: ส่งอีเมลทดสอบเข้าหาตนเอง (`SENDER_EMAIL`) พร้อมไฟล์แนบ จากนั้นรอเวลา 10 วินาที แล้วเชื่อมต่อ IMAP เพื่อค้นหาอีเมลใหม่ที่ยังไม่ได้อ่าน (`UNSEEN`) ตามหัวข้อที่กำหนด เมื่อพบจะแสดงข้อมูล:
   - ผู้ส่ง (Sender)
   - หัวข้ออีเมล (Subject)
   - ข้อความตัวอย่าง (Body Snippet ตัดที่ 200 ตัวอักษร)
   - ดาวน์โหลดไฟล์แนบเก็บลงใน `data/attachments/`
   - ปรับสถานะอีเมลเป็น "อ่านแล้ว" (`\Seen`)

---

## การทดสอบด้วย Unit Tests (Automated Testing)

โปรเจคมี Unit Test Suite ที่ใช้ `unittest.mock` เพื่อจำลองการทำงานของ SMTP และ IMAP Servers โดยไม่ต้องต่ออินเทอร์เน็ตจริงและไม่ต้องกรอกรหัสผ่านจริง:

```bash
python -m unittest tests/test_automator.py
```

ผลการทดสอบครอบคลุม:
- การป้องกันการโหลด handler ซ้ำซ้อนของ Logging
- การแจ้งเตือนข้อผิดพลาดเมื่อ Environment Variable หายไป
- การสร้าง Header, การแนบไฟล์ และการรับมือข้อผิดพลาดเมื่อไฟล์แนบไม่มีอยู่จริง
- การเข้ารหัส/ถอดรหัส MIME Header ภาษาไทยและภาษาต่างประเทศ
- การค้นหาและดึงข้อมูลอีเมลผ่านคำสั่ง IMAP
- การแมป Gateway สำหรับเครือข่ายผู้ให้บริการมือถือ

---

## ตารางการแก้ไขปัญหา (Troubleshooting Guide)

| ปัญหา / ข้อผิดพลาด | สาเหตุที่เป็นไปได้ | แนวทางแก้ไข |
| :--- | :--- | :--- |
| `ValueError: Environment variable '...' not set` | ยังไม่ได้สร้างไฟล์ `.env` หรือพิมพ์ชื่อตัวแปรผิด | คัดลอก `.env.example` ไปเป็น `.env` และตรวจสอบชื่อตัวแปรให้ตรงตามที่กำหนด |
| `SMTPAuthenticationError` (535) | รหัสผ่านไม่ถูกต้อง หรือใช้รหัสผ่านบัญชีหลักแทน App Password | ต้องสร้าง **Gmail App Password** 16 หลักจากเมนูความปลอดภัย และนำมากรอกแทนรหัสผ่านปกติ |
| `SMTPConnectError` / Connection Timed Out | โฮสต์หรือพอร์ต SMTP ไม่ถูกต้อง หรือ Firewall บล็อกพอร์ต 587 | ตรวจสอบว่าใช้ `smtp.gmail.com` พอร์ต `587` และตรวจสอบไฟร์วอลล์/พร็อกซีในเครือข่าย |
| `imaplib.IMAP4.error: b'AUTHENTICATIONFAILED'` | รหัสผ่าน IMAP ผิด หรือยังไม่ได้เปิดการเข้าถึง IMAP ในการตั้งค่า Gmail | ไปที่ Gmail Settings -> Forwarding and POP/IMAP -> ตรวจสอบว่าเปิด **Enable IMAP** เรียบร้อยแล้ว |
| อีเมลส่งสำเร็จแต่ปลายทางไม่ได้รับ | อีเมลอาจตกไปอยู่ในโฟลเดอร์ Spam / Junk | ตรวจสอบในโฟลเดอร์ Spam ของผู้รับ หรือตั้งค่า Filter ให้อนุญาตอีเมลจากผู้ส่ง |
| SMS ส่งแล้วไม่ได้รับข้อความ | เครือข่ายโทรศัพท์ของผู้รับไม่รองรับ Email Gateway หรือถูกกรองเป็น Spam | ตรวจสอบหมายเลขโทรศัพท์และ Carrier Key ให้ถูกต้อง (เครือข่ายในประเทศไทยส่วนใหญ่ไม่เปิด Public Email-to-SMS Gateway จึงแนะนำให้ใช้ API เฉพาะทาง เช่น Twilio สำหรับใช้งานจริง) |
| ตัวอักษรภาษาไทยในหัวข้ออีเมลอ่านไม่รู้เรื่อง (Garbled text) | Header มีการเข้ารหัสตามมาตรฐาน RFC 2047 | คลาส `EmailReceiver` มีเมธอด `_decode_header_part` ถอดรหัสให้อัตโนมัติ หากยังพบปัญหาให้ตรวจสอบ charset ของอีเมลต้นทาง |

---

## แนวคิดการพัฒนาต่อยอด (Extension Ideas & Future Work)

1. **ระบบตั้งเวลาทำงานอัตโนมัติ (Task Scheduling)**:
   - ผสานรวมกับไลบรารี `APScheduler` หรือ `schedule` หรือตั้งค่าระบบผ่าน Cron Job (Linux) / Windows Task Scheduler เพื่อส่งรายงานสรุปทุกเช้า 08:00 น.
2. **แม่แบบอีเมลแบบ Dynamic (Templating Engine)**:
   - นำ `Jinja2` มาใช้สร้าง HTML Email Template สวยงาม พร้อมแทรกข้อมูลผู้รับ ยอดขาย หรือตารางข้อมูลจากฐานข้อมูล (PostgreSQL / MySQL)
3. **ระบบตอบกลับและโต้ตอบอัตโนมัติ (Email Bot / Auto-responder)**:
   - ตรวจจับคีย์เวิร์ดใน Subject หรือ Body เช่น คำว่า `STATUS`, `REPORT-2026` แล้วสั่งให้ระบบดึงข้อมูลจากระบบภายในและส่งอีเมลตอบกลับผู้ส่งโดยอัตโนมัติ
4. **การส่ง SMS ระดับ Enterprise (SMS Gateway API)**:
   - เปลี่ยนจากการส่งผ่าน Email Gateway มาเป็นการเชื่อมต่อกับ REST API ชั้นนำ เช่น [Twilio](https://www.twilio.com/sms) หรือ [Vonage/Nexmo](https://www.vonage.com/) เพื่อให้ส่ง SMS ถึงเบอร์มือถือทั่วโลก (รวมทั้งเบอร์ไทย) ได้อย่างแม่นยำ พร้อมระบบตรวจสอบสถานะการส่ง (Delivery Receipts)
5. **แจ้งเตือนข้อผิดพลาดทันที (Error Alerting)**:
   - สร้างฟังก์ชันแจ้งเตือนผ่าน Telegram Bot หรือ LINE Notify เมื่อพบ Exception ร้ายแรงในระบบเซิร์ฟเวอร์
