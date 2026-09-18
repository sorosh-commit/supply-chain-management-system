# Enterprise Supply Chain and Warehouse Management System

An advanced, enterprise-grade web application built with Python (Flask) and SQLAlchemy for real-time inventory tracking, multi-warehouse operations management, and secure role-based access control.

---

## Features and Modules
- **Role-Based Access Control (RBAC):** Secure management for Administrators, Warehouse Managers, Logistics Operators, and Suppliers.
- **Real-Time Inventory Tracking:** Automated stock adjustments coupled with immutable transaction auditing logs.
- **Multi-Warehouse Management:** Spatial capacity monitoring, threshold warnings, and location-based stock allocation.
- **Advanced Audit Trails:** Comprehensive database logging for every inbound and outbound supply chain movement.

---

## Tech Stack
- **Backend:** Python, Flask, Flask-SQLAlchemy
- **Database:** SQLite (Relational Enterprise Schema)
- **Documentation:** PlantUML (Architecture and Use Case Modeling)

---

## System Architecture and Diagrams

### 1. Entity-Relationship Diagram (ERD)
The database schema handles relational integrity across Users, Suppliers, Warehouses, Products, Stocks, and Transactions:

![ERD Diagram](diagrams/erd.png)

### 2. Use Case Diagram
System interaction mapping across different administrative and operational actors:

![Use Case Diagram](diagrams/use_case.png)

---

## Installation and Setup

**1. Clone the repository:**
   ```bash
   git clone [https://github.com/soroshTypeG/supply-chain-management-system.git](https://github.com/soroshTypeG/supply-chain-management-system.git)
   cd supply-chain-management-system
```

**Install dependencies:**

```bash
pip install -r requirements.txt
```

**Run the application:**

Before running the app.py first you got to run the seed.py script:
```bash
python seed.py
```

Then:
```bash
python app.py
```

## Testing

The project includes an automated test suite using Python's built-in `unittest` framework to verify database integrity, model relationships, and HTTP route responses.

To run the test suite, execute:
```bash
python test_app.py
```




---

## راهنمای فارسی (Persian Overview)

سامانه سازمانی مدیریت انبار و زنجیره تأمین یک برنامه تحت وب پیشرفته است که با پایتون (Flask) و SQLAlcسامانه سازمانی مدیریت انبار و زنجیره تأمین

یک برنامه وب پیشرفته و در سطح سازمانی که با پایتون (Flask) و SQLAlchemy برای ردیابی لحظه‌ای موجودی، مدیریت عملیات چندانبار و کنترل دسترسی امن نقش‌محور ساخته شده است.

**ویژگی ها و ماژول ها:**

کنترل دسترسی نقش‌محور (RBAC): مدیریت امن برای مدیران، مدیران انبار، اپراتورهای لجستیک و تأمین‌کنندگان.

ردیابی موجودی در زمان واقعی: تنظیمات خودکار موجودی همراه با لاگ‌های حسابرسی تراکنش تغییرناپذیر.

مدیریت چند انبار: پایش ظرفیت فضایی، هشدارهای آستانه و تخصیص موجودی مبتنی بر موقعیت مکانی.

مسیرهای حسابرسی پیشرفته: ثبت جامع پایگاه داده برای هرگونه جابجایی ورودی و خروجی در زنجیره تأمین.

**فناوری های استفاده شده:**

بخش پشتی (Backend): پایتون، Flask، Flask-SQLAlchemy

پایگاه داده: SQLite (طرحواره رابطه‌ای سازمانی)

مستندات: PlantUML (مدل‌سازی معماری و موارد استفاده).

### نصب و راه‌اندازی سریع
۱. کلون کردن مخزن:
   ```bash
   git clone [https://github.com/soroshTypeG/supply-chain-management-system.git](https://github.com/soroshTypeG/supply-chain-management-system.git)
   cd supply-chain-management-system
```

**۲. نصب پکیج‌های مورد نیاز:**
```bash
pip install -r requirements.txt
```
**۳. اجرای برنامه:**

قبل از اجرای برنامه باید اول اسکریپت seed.py را اجرا کنید:
```bash
python seed.py
```

بعد:
```bash
python app.py
```

پروژه شامل یک مجموعه تست خودکار با استفاده از فریم‌ورک داخلی unittest در پایتون است تا یکپارچگی پایگاه داده، روابط مدل‌ها و پاسخ‌های مسیرهای HTTP را بررسی کند.
برای اجرای مجموعه تست، این دستور را اجرا کنید:
```bash
python test_app.py
```
