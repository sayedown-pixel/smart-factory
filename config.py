# ============================================================
#  BIRMA SaaS - ملف إعداد المصنع
#  ده الملف الوحيد اللي بيتغير من عميل لعميل
#  Designed by: م/ السيد عون
# ============================================================

FACTORY_CONFIG = {"factory_name":  "اسم مصنعك الحقيقي",
"factory_city":  "مدينتك",
"db_name":       "اسم_فريد",        # مثال: birma_factory

"telegram_token": "توكن البوت بتاعك",
"telegram_chat":  "ID المجموعة",

"admin_password": "كلمة سر قوية",

"lines": {
    "الخط الأول(smi)": {
        "products": ["200 ml Carton", "600 ml Carton", "1.5 L Shrink"],
        "bottles_per_unit": {
            "200 ml Carton": 48,
            "600 ml Carton": 30,
            "1.5 L Shrink":  6,
        },
        "speed_per_shift": {
            "200 ml Carton": 35000,
            "600 ml Carton": 20000,
            "1.5 L Shrink":  12000,
        },
    },
    "الخط الثاني(welbing)": {
        "products": ["200 ml Carton", "330 ml Carton"],
        "bottles_per_unit": {
            "200 ml Carton": 48,
            "330 ml Carton": 40,
        },
        "speed_per_shift": {
            "200 ml Carton": 40000,
            "330 ml Carton": 40000,
        },
    },
},

    # -------- ماكينات الصيانة --------
    "machines": {
        "النفخ (Blowing)":        "blowing_machine.xlsx",
        "الليبل (Labeling)":      "labeling_machine.xlsx",
        "السيور (Conveyor)":      "Conveyor_machine.xlsx",
        "الكرتون (Packing)":      "packing_machine.xlsx",
        "البالتايزر (Paletizer)": "paletizer_machine.xlsx",
        "الشرنك (Shrink)":        "shrink_machine.xlsx",
        "التعبئة (Filling)":      "Filling_machine.xlsx",
    },

    # -------- كلمة سر المشرف --------
    "admin_password": "admin123",         # ← غيّرها لكل عميل
}
