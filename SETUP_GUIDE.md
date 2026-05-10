# ============================================================
#  BIRMA SaaS — دليل إعداد عميل جديد (Railway / Render)
#  Designed by: م/ السيد عون
# ============================================================

## هيكل الملفات
```
birma-factory/
│
├── app.py              ← النظام الكامل (لا تلمسه)
├── database.py         ← مدير قاعدة البيانات (لا تلمسه)
├── config.py           ← ← ← هنا بس بتعدل
├── requirements.txt    ← المكتبات
│
├── data/               ← بيتنشأ تلقائياً
│   └── factory_name.db ← قاعدة بيانات المصنع
│
├── images/             ← صور ماكينات الصيانة
└── *.xlsx              ← ملفات جداول الصيانة
```

---

## الخطوات (10 دقايق لكل عميل جديد)

### 1️⃣ انسخ الـ repo
```bash
git clone YOUR_REPO birma-FACTORY_NAME
cd birma-FACTORY_NAME
```

### 2️⃣ عدّل config.py بس
```python
"factory_name":  "مصنع النور",      # اسم العميل
"factory_city":  "جدة",
"db_name":       "nour_water",       # اسم فريد → data/nour_water.db
"telegram_token": "...",
"telegram_chat":  "...",
"admin_password": "كلمة سر قوية",
"lines": { ... }                     # خطوط المصنع
```

### 3️⃣ ارفع على GitHub
```bash
git add .
git commit -m "Add factory: مصنع النور"
git push
```

### 4️⃣ Deploy على Railway
- افتح railway.app
- New Project → Deploy from GitHub
- اختار الـ repo
- Add Variable:
  ```
  PORT = 8501
  ```
- Start Command:
  ```
  streamlit run app.py --server.port $PORT --server.address 0.0.0.0
  ```
- ✅ الرابط جاهز في دقيقتين!

### 4️⃣ (بديل) Deploy على Render
- افتح render.com
- New → Web Service → Connect GitHub repo
- Build Command: `pip install -r requirements.txt`
- Start Command: `streamlit run app.py --server.port 10000 --server.address 0.0.0.0`
- ✅ مجاني بالكامل!

---

## العزل بين العملاء ✅

```
مصنع النور  → nour_water.db   → birma-nour.railway.app
مصنع الصفاء → safaa_water.db  → birma-safaa.railway.app
مصنع الربوة → rabwa_water.db  → birma-rabwa.railway.app
```

كل مصنع:
- قاعدة بيانات منفصلة ✅
- رابط مختلف ✅
- بوت تيليجرام خاص ✅
- كلمة سر مختلفة ✅

---

## الأسعار المقترحة

| الباكدج   | السعر الشهري | المحتوى                        |
|-----------|-------------|-------------------------------|
| أساسي     | 800 ريال    | إنتاج + صيانة + تيليجرام      |
| متقدم     | 1,500 ريال  | + تقارير PDF + KPIs متقدمة    |
| إعداد أولي| 2,000 ريال  | مرة واحدة عند التفعيل         |

**10 عملاء × 1,000 = 10,000 ريال/شهر** 🎯
