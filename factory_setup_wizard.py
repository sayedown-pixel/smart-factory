import streamlit as st
import pandas as pd
from datetime import datetime, time
from database import db_manager
from helpers import load_language

PRODUCT_TYPE_OPTIONS = [
    {"key": "prod_carton_200", "ar": "كرتون 200 مل", "en": "Carton 200ml", "size": "200ml", "packaging": "كرتون"},
    {"key": "prod_carton_330", "ar": "كرتون 330 مل", "en": "Carton 330ml", "size": "330ml", "packaging": "كرتون"},
    {"key": "prod_carton_500", "ar": "كرتون 500 مل", "en": "Carton 500ml", "size": "500ml", "packaging": "كرتون"},
    {"key": "prod_carton_600", "ar": "كرتون 600 مل", "en": "Carton 600ml", "size": "600ml", "packaging": "كرتون"},
    {"key": "prod_shrink_200", "ar": "شرنك 200 مل", "en": "Shrink 200ml", "size": "200ml", "packaging": "شرنك"},
    {"key": "prod_shrink_330", "ar": "شرنك 330 مل", "en": "Shrink 330ml", "size": "330ml", "packaging": "شرنك"},
    {"key": "prod_shrink_500", "ar": "شرنك 500 مل", "en": "Shrink 500ml", "size": "500ml", "packaging": "شرنك"},
    {"key": "prod_shrink_600", "ar": "شرنك 600 مل", "en": "Shrink 600ml", "size": "600ml", "packaging": "شرنك"},
    {"key": "prod_shrink_1l", "ar": "شرنك 1 لتر", "en": "Shrink 1L", "size": "1L", "packaging": "شرنك"},
    {"key": "prod_shrink_1_5l", "ar": "شرنك 1.5 لتر", "en": "Shrink 1.5L", "size": "1.5L", "packaging": "شرنك"},
]

RAW_MATERIAL_OPTIONS = [
    {"key": "mat_preform", "ar": "بريفورم", "en": "Preform", "size_specific": True, "unit": "قطعة"},
    {"key": "mat_label", "ar": "ليبل", "en": "Label", "size_specific": True, "unit": "قطعة"},
    {"key": "mat_cap", "ar": "غطاء", "en": "Cap", "size_specific": False, "unit": "قطعة"},
    {"key": "mat_carton", "ar": "كرتون", "en": "Carton", "size_specific": True, "unit": "قطعة"},
    {"key": "mat_shrink", "ar": "شرنك", "en": "Shrink", "size_specific": True, "unit": "قطعة"},
    {"key": "mat_shrink_divider", "ar": "فواصل شرنك", "en": "Shrink Divider", "size_specific": False, "unit": "قطعة"},
    {"key": "mat_carton_glue", "ar": "غراء كرتون", "en": "Carton Glue", "size_specific": False, "unit": "وزن"},
    {"key": "mat_shrink_film", "ar": "استرتش فيلم", "en": "Shrink Film", "size_specific": False, "unit": "وزن"},
    {"key": "mat_label_glue", "ar": "غراء ليبل", "en": "Label Glue", "size_specific": False, "unit": "وزن"},
]


def current_lang():
    return st.session_state.get("lang", st.session_state.get("language", "ar"))


def localized(item, lang=None, t=None):
    lang = lang or current_lang()
    if t and item.get("key"):
        return t.get(item["key"], item.get("en" if lang == "en" else "ar", item.get("ar", "")))
    return item.get("en" if lang == "en" else "ar", item.get("ar", ""))


def find_option(options, value, default_index=0):
    for idx, item in enumerate(options):
        if value in (item.get("ar"), item.get("en")):
            return idx, item
    return default_index, options[default_index]


def product_type_map():
    return {item["ar"]: item["en"] for item in PRODUCT_TYPE_OPTIONS}


def product_type_map_rev():
    return {item["en"]: item["ar"] for item in PRODUCT_TYPE_OPTIONS}


def material_map():
    return {item["ar"]: item["en"] for item in RAW_MATERIAL_OPTIONS}


def material_map_rev():
    return {item["en"]: item["ar"] for item in RAW_MATERIAL_OPTIONS}


def display_material(material, lang=None):
    lang = lang or current_lang()
    if lang == "en":
        return material.get("name_en") or material.get("name_ar") or material.get("code", "")
    return material.get("name_ar") or material.get("name_en") or material.get("code", "")


def base_material_en(material):
    name = material.get("name_en", "")
    for size in ("200ml", "330ml", "500ml", "600ml", "1L", "1.5L"):
        suffix = f" {size}"
        if name.endswith(suffix):
            return name[:-len(suffix)]
    return name


def init_wizard_state():
    if 'wizard_step' not in st.session_state:
        st.session_state.wizard_step = 1
    if 'wizard_factory' not in st.session_state:
        st.session_state.wizard_factory = {}
    if 'wizard_lines' not in st.session_state:
        st.session_state.wizard_lines = []
    if 'wizard_products' not in st.session_state:
        st.session_state.wizard_products = []
    if 'wizard_materials' not in st.session_state:
        st.session_state.wizard_materials = []
    if 'wizard_line_products' not in st.session_state:
        st.session_state.wizard_line_products = {}
    if 'wizard_bom_details' not in st.session_state:
        st.session_state.wizard_bom_details = {}
    if 'wizard_shift' not in st.session_state:
        st.session_state.wizard_shift = {
            'start_time': time(8, 0),
            'end_time': time(2, 0),
            'break_minutes': 180,
            'breaks': [
                {'start': time(10, 0), 'end': time(10, 30)},
                {'start': time(13, 0), 'end': time(14, 0)},
                {'start': time(18, 0), 'end': time(18, 30)},
                {'start': time(23, 0), 'end': time(0, 30)},
            ]
        }
    if 'wizard_emails' not in st.session_state:
        st.session_state.wizard_emails = []
    if 'wizard_users' not in st.session_state:
        st.session_state.wizard_users = {}

def reset_wizard():
    keys = ['wizard_step', 'wizard_factory', 'wizard_lines', 'wizard_products',
            'wizard_materials', 'wizard_line_products', 'wizard_bom_details',
            'wizard_shift', 'wizard_emails', 'wizard_users']
    for k in keys:
        if k in st.session_state:
            del st.session_state[k]
    st.session_state.show_factory_wizard = False

def show_wizard_progress(t):
    steps = [
        (1, t.get("wizard_step1", "Factory Info")),
        (2, t.get("wizard_step2", "Production Lines")),
        (3, t.get("wizard_step3_materials", "Raw Materials")),
        (4, t.get("wizard_step4", "Product BOM")),
        (5, t.get("wizard_step5", "Shift Times")),
        (6, t.get("wizard_step6", "Admin Emails")),
    ]
    current = st.session_state.wizard_step
    cols = st.columns(len(steps))
    for i, (num, label) in enumerate(steps):
        step_num = i + 1
        with cols[i]:
            if step_num < current:
                st.success(f"✅ {label}")
            elif step_num == current:
                st.info(f"🔵 {label}")
            else:
                st.markdown(f"⬜ {label}")

def step1_factory_info(t):
    st.markdown(f"### {t.get('wizard_step1_title', 'Step 1: Factory Information')}")
    f = st.session_state.wizard_factory
    users = st.session_state.wizard_users

    col1, col2 = st.columns(2)
    with col1:
        f['name_ar'] = st.text_input(t.get("wizard_name_ar", "اسم المصنع (عربي)"),
                                      value=f.get('name_ar', ''),
                                      placeholder=t.get("wizard_name_ar_ph", "مثال: مصنع النخبة للمياه"))
        f['code'] = st.text_input(t.get("wizard_code", "كود المصنع (فريد)"),
                                   value=f.get('code', ''),
                                   placeholder=t.get("wizard_code_ph", "nakhba_factory"),
                                   help=t.get("wizard_code_help", "كود فريد بالحروف والأرقام فقط"))
        f['phone'] = st.text_input(t.get("wizard_phone", "رقم الهاتف"),
                                    value=f.get('phone', ''),
                                    placeholder=t.get("wizard_phone_ph", "+966 5X XXX XXXX"))
    with col2:
        f['name_en'] = st.text_input(t.get("wizard_name_en", "Factory Name (English)"),
                                      value=f.get('name_en', ''),
                                      placeholder=t.get("wizard_name_en_ph", "Example: Nakhba Water Factory"))
        f['email'] = st.text_input(t.get("wizard_email", "البريد الإلكتروني"),
                                    value=f.get('email', ''),
                                    placeholder=t.get("wizard_email_ph", "info@factory.com"))
        f['address'] = st.text_input(t.get("wizard_address", "العنوان"),
                                      value=f.get('address', ''),
                                      placeholder=t.get("wizard_address_ph", "المدينة - المنطقة"))

    st.markdown("---")
    st.markdown(f"### {t.get('wizard_admin_section', 'Factory Admin Account')}")
    col1, col2 = st.columns(2)
    with col1:
        f['admin_username'] = st.text_input(t.get("wizard_admin_username", "اسم المستخدم للمدير"),
                                             value=f.get('admin_username', ''),
                                             placeholder=t.get("wizard_admin_username_ph", "factory_admin"))
        f['admin_name'] = st.text_input(t.get("wizard_admin_name", "اسم المدير"),
                                         value=f.get('admin_name', ''),
                                         placeholder=t.get("wizard_admin_name_ph", "أحمد محمد"))
    with col2:
        f['admin_password'] = st.text_input(t.get("wizard_admin_password", "كلمة المرور"),
                                             type="password",
                                             value=f.get('admin_password', ''),
                                             help=t.get("wizard_admin_password_help", "على الأقل 6 أحرف"))
        f['admin_password_confirm'] = st.text_input(t.get("wizard_admin_confirm", "تأكيد كلمة المرور"),
                                                     type="password",
                                                     value=f.get('admin_password_confirm', ''))

    st.markdown("---")
    st.markdown(f"### {t.get('wizard_users_section', 'Department Users (Passwords)')}")
    st.caption(t.get("wizard_user_pass_help", "Users will be created automatically. Leave empty for default password."))
    col1, col2 = st.columns(2)
    with col1:
        users['supervisor_pass'] = st.text_input(t.get("wizard_user_supervisor", "👔 Supervisor (pro)"),
                                                  type="password",
                                                  value=users.get('supervisor_pass', ''),
                                                  key="wiz_sup_pass")
        users['technician_pass'] = st.text_input(t.get("wizard_user_technician", "🔧 Technician (tec)"),
                                                  type="password",
                                                  value=users.get('technician_pass', ''),
                                                  key="wiz_tec_pass")
    with col2:
        users['storekeeper_pass'] = st.text_input(t.get("wizard_user_storekeeper", "📦 Storekeeper (sto)"),
                                                   type="password",
                                                   value=users.get('storekeeper_pass', ''),
                                                   key="wiz_sto_pass")
        users['quality_pass'] = st.text_input(t.get("wizard_user_quality", "🔍 Quality (quality)"),
                                               type="password",
                                               value=users.get('quality_pass', ''),
                                               key="wiz_qua_pass")

    st.session_state.wizard_factory = f
    st.session_state.wizard_users = users

    if st.button(t.get("wizard_next_lines", "Next → Production Lines"), type="primary", use_container_width=True):
        errors = []
        if not f.get('name_ar'):
            errors.append(t.get("wizard_name_ar", "اسم المصنع (عربي)"))
        if not f.get('name_en'):
            errors.append(t.get("wizard_name_en", "Factory Name (English)"))
        if not f.get('code'):
            errors.append(t.get("wizard_code", "كود المصنع"))
        if not f.get('admin_username'):
            errors.append(t.get("wizard_admin_username", "اسم مستخدم المدير"))
        if not f.get('admin_password') or len(f.get('admin_password', '')) < 6:
            errors.append(t.get("wizard_admin_password", "كلمة المرور (6 أحرف على الأقل)"))
        if f.get('admin_password') != f.get('admin_password_confirm'):
            errors.append(t.get("passwords_not_match", "كلمتا المرور غير متطابقتين"))
        if not f.get('admin_name'):
            errors.append(t.get("wizard_admin_name", "اسم المدير"))

        if errors:
            st.error(t.get("wizard_errors_prefix", "⚠️ Please fix: ") + "، ".join(errors))
        else:
            st.session_state.wizard_step = 2
            st.rerun()

def step2_lines_and_products(t):
    st.markdown(f"### {t.get('wizard_step2_title', 'Step 2: Production Lines & Products')}")
    st.caption(t.get('wizard_step2_caption', 'Add lines, then assign products and speeds'))

    lines = st.session_state.wizard_lines
    products = st.session_state.wizard_products

    col1, col2 = st.columns(2)
    with col1:
        if st.button(t.get("wizard_add_line", "➕ Add Production Line"), use_container_width=True):
            lines.append({"name_ar": "", "name_en": "", "code": ""})
            st.rerun()
    with col2:
        if st.button(t.get("wizard_add_product", "➕ Add Product"), use_container_width=True):
            products.append({"name_ar": "", "name_en": "", "code": "", "packaging": "كرتون"})
            st.rerun()

    st.markdown("---")

    if lines:
        st.subheader(f"📋 {t.get('wizard_lines_header', 'Production Lines')}")
        for idx, line in enumerate(lines):
            col1, col2, col3, col4 = st.columns([3, 3, 2, 1])
            with col1:
                lines[idx]['name_ar'] = st.text_input(t.get("wizard_line_ar", "Name (Arabic)").replace("{n}", str(idx+1)),
                                                       value=line.get('name_ar', ''), key=f"wl_ar_{idx}")
            with col2:
                lines[idx]['name_en'] = st.text_input(t.get("wizard_line_en", "Name (EN)").replace("{n}", str(idx+1)),
                                                       value=line.get('name_en', ''), key=f"wl_en_{idx}")
            with col3:
                lines[idx]['code'] = st.text_input(t.get("wizard_line_code", "Code").replace("{n}", str(idx+1)),
                                                    value=line.get('code', ''), key=f"wl_code_{idx}")
            with col4:
                if st.button("🗑️", key=f"wl_del_{idx}"):
                    lines.pop(idx)
                    st.rerun()
    else:
        st.info(t.get("wizard_no_lines", "No lines added yet."))

    st.markdown("---")

    if products:
        st.subheader(f"📦 {t.get('wizard_products_header', 'Products')}")
        
        # قائمة الأصناف الجديدة
        product_types = [(item["ar"], item["en"]) for item in PRODUCT_TYPE_OPTIONS]
        
        # ربط الأسماء العربية بالإنجليزية
        product_mapping = product_type_map()
        
        # ربط الأسماء الإنجليزية بالعربية
        product_mapping_rev = {v: k for k, v in product_mapping.items()}
        
        for idx, prod in enumerate(products):
            col1, col2, col3, col4, col5 = st.columns([2.5, 2.5, 2, 1.5, 1])
            with col1:
                # قائمة منسدلة للصنف - تعرض حسب اللغة
                lang = current_lang()
                current_type = prod.get('product_type', 'كرتون 200 مل')
                # تحويل النوع الحالي إلى اللغة الحالية
                if lang == 'en' and current_type in product_mapping:
                    current_type = product_mapping[current_type]
                elif lang == 'ar' and current_type in product_mapping_rev:
                    current_type = product_mapping_rev[current_type]
                
                type_idx, _ = find_option(PRODUCT_TYPE_OPTIONS, current_type)
                selected_product_option = st.selectbox(
                    t.get("wizard_product_type", "نوع الصنف"),
                    options=PRODUCT_TYPE_OPTIONS,
                    format_func=lambda item: localized(item, lang, t),
                    index=type_idx,
                    key=f"wp_type_{idx}"
                )
                product_type_changed = prod.get('_product_type_key') != selected_product_option['key']
                products[idx]['_product_type_key'] = selected_product_option['key']
                products[idx]['product_type'] = selected_product_option['ar']
                products[idx]['size'] = selected_product_option['size']
                products[idx]['packaging'] = selected_product_option['packaging']
                
            with col2:
                # الاسم العربي يتم تحديثه تلقائياً بناءً على النوع المختار
                selected_type_ar = selected_product_option['ar']
                standard_names_ar = [ar for ar, _ in product_types]
                stored_ar = prod.get('name_ar', '')
                current_ar = selected_type_ar if product_type_changed or not stored_ar or stored_ar in standard_names_ar else stored_ar
                products[idx]['name_ar'] = st.text_input(t.get("wizard_product_ar", "اسم الصنف (عربي)"),
                                                          value=current_ar, key=f"wp_ar_{idx}_{selected_product_option['key']}")
            with col3:
                # الاسم الإنجليزي يتم تحديثه تلقائياً بناءً على النوع المختار
                auto_en = selected_product_option['en']
                stored_en = prod.get('name_en', '')
                standard_names = [en for _, en in product_types]
                if product_type_changed or not stored_en or stored_en in standard_names:
                    current_en = auto_en
                else:
                    current_en = stored_en
                products[idx]['name_en'] = st.text_input(t.get("wizard_product_en", "اسم الصنف (إنجليزي)"),
                                                           value=current_en, key=f"wp_en_{idx}_{selected_product_option['key']}")
            with col4:
                products[idx]['code'] = st.text_input(t.get("wizard_product_code", "كود الصنف"),
                                                       value=prod.get('code', ''), key=f"wp_code_{idx}")
            with col5:
                if st.button("🗑️", key=f"wp_del_{idx}"):
                    products.pop(idx)
                    st.rerun()
    else:
        st.info(t.get("wizard_no_products", "No products added yet."))

    st.markdown("---")

    if lines and products:
        st.subheader(f"⚡ {t.get('wizard_line_products_link', 'Link Products to Lines')}")
        st.caption(t.get('wizard_line_products_caption', 'Set speed per line/product'))

        line_products = st.session_state.wizard_line_products

        for line_idx, line in enumerate(lines):
            line_code = line.get('code', f'line_{line_idx}')
            if line_code not in line_products:
                line_products[line_code] = {}

            lang = current_lang()
            default_line_name = t.get("wizard_line_default", "Line {n}" if lang == "en" else "خط {n}").replace("{n}", str(line_idx + 1))
            line_name = line.get('name_en') if lang == 'en' else line.get('name_ar')
            line_name = line_name or line.get('name_ar') or line.get('name_en') or default_line_name
            st.markdown(f"**{line_name}**")

            prod_codes = [p.get('code', '') for p in products if p.get('code')]
            current_prods = list(line_products[line_code].keys())

            selected = st.multiselect(
                f"",
                options=prod_codes,
                default=[p for p in current_prods if p in prod_codes],
                format_func=lambda c: next((p.get('name_en', p.get('name_ar', c)) if lang == 'en' else p.get('name_ar', c) for p in products if p.get('code') == c), c),
                key=f"line_prods_{line_idx}"
            )

            new_line_products = {}
            for prod_code in selected:
                speed = line_products[line_code].get(prod_code, 0)
                prod_name = next((p.get('name_en', p.get('name_ar', prod_code)) if lang == 'en' else p.get('name_ar', prod_code) for p in products if p.get('code') == prod_code), prod_code)
                speed_label = t.get("wizard_speed_label", "Speed - {product} (units/hr)").replace("{product}", prod_name)
                speed = st.number_input(
                    speed_label,
                    min_value=0, step=100, value=speed,
                    key=f"speed_{line_code}_{prod_code}"
                )
                new_line_products[prod_code] = speed

            line_products[line_code] = new_line_products

        st.session_state.wizard_line_products = line_products

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button(t.get("wizard_prev", "← Back"), use_container_width=True):
            st.session_state.wizard_step = 1
            st.rerun()
    with col2:
        if st.button(t.get("wizard_next_materials", "Next → Raw Materials"), type="primary", use_container_width=True):
            if not lines:
                st.error(t.get("wizard_lines_missing", "⚠️ At least one line is required"))
            elif not products:
                st.error(t.get("wizard_products_missing", "⚠️ At least one product is required"))
            else:
                st.session_state.wizard_lines = lines
                st.session_state.wizard_products = products
                st.session_state.wizard_step = 3
                st.rerun()

def step3_raw_materials(t):
    st.markdown(f"### 🧪 {t.get('wizard_step3_title', 'Step 3: Raw Materials')}")
    st.caption(t.get('wizard_step3_caption', 'Define the raw materials used in production'))
    
    st.info(t.get("raw_materials_info", """
    **Raw Material Types:**
    - **Preform:** Size-specific (200ml, 330ml, 500ml, 600ml, 1L, 1.5L)
    - **Label:** Size-specific
    - **Cap:** General - shared across all products
    - **Carton:** Size-specific
    - **Shrink:** Size-specific - counted in rolls for inventory, pieces for production
    - **Shrink Divider:** General
    - **Label Glue:** By weight (kg in inventory, grams in BOM)
    - **Carton Glue:** By weight (kg in inventory, grams in BOM)
    - **Shrink Film:** General - by weight per pallet
    """))

    products = st.session_state.wizard_products
    materials = st.session_state.wizard_materials

    # قوائم المواد والمقاسات
    material_names_en = [item["en"] for item in RAW_MATERIAL_OPTIONS]
    
    # ربط الأسماء العربية بالإنجليزية
    material_mapping = material_map()
    
    # ربط الأسماء الإنجليزية بالعربية
    material_mapping_rev = {v: k for k, v in material_mapping.items()}
    
    # المواد التي يجب أن تكون مقاسها عام تلقائياً
    general_size_materials = [item["en"] for item in RAW_MATERIAL_OPTIONS if not item["size_specific"]]
    
    sizes = [
        ("200ml", "200ml"),
        ("330ml", "330ml"),
        ("500ml", "500ml"),
        ("600ml", "600ml"),
        ("1L", "1L"),
        ("1.5L", "1.5L"),
        ("general", "general")
    ]
    
    units = [
        ("قطعة", "Piece"),
        ("وزن", "Weight")
    ]

    if st.button(t.get("wizard_add_material", "➕ Add Raw Material"), use_container_width=True):
        # أول مادة تضاف تلقائياً تكون بريفورم مع مقاس 200 مل
        first_size = sizes[0][0]  # 200ml
        first_size_label = sizes[0][1]  # 200 مل
        materials.append({
            "name_ar": f"بريفورم {first_size_label}", 
            "name_en": f"Preform {first_size}", 
            "code": "", 
            "unit": "قطعة", 
            "min_stock": 0,
            "size": first_size
        })
        st.rerun()

    st.markdown("---")

    size_label_map = {k: v for k, v in sizes}
    size_label_map_rev = {v: k for k, v in sizes}
    size_ar_name_map = {
        "200ml": "200",
        "330ml": "330",
        "500ml": "500",
        "600ml": "600",
        "1L": "1 لتر",
        "1.5L": "1.5 لتر",
    }

    if materials:
        st.subheader(f"🧪 {t.get('wizard_materials_header', 'Raw Materials')}")
        for idx, mat in enumerate(materials):
            col1, col2 = st.columns([2, 2])
            with col1:
                # قائمة منسدلة للإنجليزي - تعرض الأسماء الإنجليزية
                current_name_en = mat.get('name_en', 'Preform')
                # استخراج اسم المادة الأساسي (بدون المقاس)
                base_name_en = current_name_en
                for s_label in ['200ml', '330ml', '500ml', '600ml', '1L', '1.5L']:
                    if base_name_en.endswith(f" {s_label}"):
                        base_name_en = base_name_en[:-(len(s_label)+1)]
                        break
                name_en_idx = material_names_en.index(base_name_en) if base_name_en in material_names_en else 0
                selected_base_en = st.selectbox(
                    t.get("wizard_mat_name_en", "Material Name"),
                    options=material_names_en,
                    index=name_en_idx,
                    key=f"wm_en_{idx}"
                )
                # تخزين الاسم الأساسي مؤقتاً لحين تحديث المقاس
                materials[idx]['_base_en'] = selected_base_en
                materials[idx]['_base_ar'] = material_mapping_rev.get(selected_base_en, selected_base_en)
                # تحويل المقاس إلى عام تلقائياً للمواد العامة
                if selected_base_en in general_size_materials:
                    materials[idx]['size'] = 'general'
            with col2:
                materials[idx]['code'] = st.text_input(t.get("wizard_mat_code", "Code"),
                                                        value=mat.get('code', ''), key=f"wm_code_{idx}")
            
            # صف إضافي للكود والمقاس
            col_a, col_b, col_c = st.columns([2, 2, 1])
            with col_a:
                current_unit = mat.get('unit', next((item["unit"] for item in RAW_MATERIAL_OPTIONS if item["en"] == selected_base_en), 'قطعة'))
                unit_idx = next((i for i, (k, v) in enumerate(units) if k == current_unit), 0)
                materials[idx]['unit'] = st.selectbox(
                    t.get("wizard_mat_unit", "الوحدة"),
                    options=[k for k, v in units],
                    format_func=lambda x: next(v if current_lang() == 'en' else k for k, v in units if k == x),
                    index=unit_idx,
                    key=f"wm_unit_{idx}"
                )
            with col_b:
                current_size = mat.get('size', 'general')
                size_idx = next((i for i, (k, v) in enumerate(sizes) if k == current_size), 0)
                selected_size = st.selectbox(
                    t.get("wizard_mat_size", "المقاس"),
                    options=[k for k, v in sizes],
                    format_func=lambda x: t.get("wizard_size_general", "General") if x == "general" and current_lang() == "en" else (t.get("wizard_size_general_ar", "عام") if x == "general" else next(v for k, v in sizes if k == x)),
                    index=size_idx,
                    key=f"wm_size_{idx}"
                )
                materials[idx]['size'] = selected_size
            with col_c:
                if st.button("🗑️", key=f"wm_del_{idx}"):
                    materials.pop(idx)
                    st.rerun()

            # تحديث الاسم تلقائياً: اسم المادة + المقاس
            base_ar = materials[idx].get('_base_ar', 'بريفورم')
            base_en = materials[idx].get('_base_en', 'Preform')
            sz = selected_size
            sz_label = size_label_map.get(sz, '')
            if sz_label and sz != 'general':
                materials[idx]['name_ar'] = f"{base_ar} {size_ar_name_map.get(sz, sz_label)}"
                materials[idx]['name_en'] = f"{base_en} {sz}"
            else:
                materials[idx]['name_ar'] = base_ar
                materials[idx]['name_en'] = base_en
            
            col_d, col_e = st.columns([1.5, 1.5])
            with col_d:
                materials[idx]['name_ar'] = st.text_input(
                    t.get("wizard_mat_name_ar", "اسم المادة"),
                    value=materials[idx]['name_ar'],
                    key=f"wm_ar_{idx}_{selected_base_en}_{selected_size}"
                )
            with col_e:
                materials[idx]['min_stock'] = st.number_input(t.get("wizard_mat_min_stock", "الحد الأدنى"),
                                                              min_value=0, value=int(mat.get('min_stock', 0)),
                                                              key=f"wm_min_{idx}")
            
            st.markdown("---")
    else:
        st.info(t.get("wizard_no_materials", "No materials added yet. Add at least one material."))

    st.session_state.wizard_materials = materials

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button(t.get("wizard_prev", "← Back"), use_container_width=True):
            st.session_state.wizard_step = 2
            st.rerun()
    with col2:
        if st.button(t.get("wizard_next_bom", "Next → Product BOM"), type="primary", use_container_width=True):
            if not materials:
                st.error(t.get("wizard_materials_required", "⚠️ At least one material is required"))
            else:
                st.session_state.wizard_step = 4
                st.rerun()


def step4_product_bom(t):
    st.markdown(f"### 🔧 {t.get('wizard_step4_title', 'Step 4: Product BOM')}")
    st.caption(t.get('wizard_step4_caption', 'Define Bill of Materials for each product'))
    
    st.info(t.get("bom_info_structure", """
    **Product BOM Structure:**
    - Production unit (Carton or Shrink)
    - Bottles per unit
    - Per bottle: Preform, Cap, Label, Label Glue
    - If Carton: Carton + Carton Glue
    - If Shrink: Shrink + Shrink Dividers
    - Shrink Film (general): Weight per pallet for all types
    - ⚠️ **Required:** All components must be filled before proceeding
    """))

    products = st.session_state.wizard_products
    materials = st.session_state.wizard_materials
    bom_details = st.session_state.wizard_bom_details

    if not materials:
        st.warning(t.get("wizard_no_materials_bom", "⚠️ No materials defined. Go back to Step 3."))
        return

    if not products:
        st.warning(t.get("wizard_products_missing", "⚠️ No products defined."))
        return

    # تصنيف المواد حسب الاسم الأساسي لتجنب خلط Carton مع Carton Glue مثلاً.
    preform_materials = [m for m in materials if base_material_en(m) == 'Preform']
    label_materials = [m for m in materials if base_material_en(m) == 'Label']
    cap_materials = [m for m in materials if base_material_en(m) == 'Cap']
    carton_materials = [m for m in materials if base_material_en(m) == 'Carton']
    shrink_materials = [m for m in materials if base_material_en(m) == 'Shrink']
    shrink_divider_materials = [m for m in materials if base_material_en(m) == 'Shrink Divider']
    carton_glue_materials = [m for m in materials if base_material_en(m) == 'Carton Glue']
    label_glue_materials = [m for m in materials if base_material_en(m) == 'Label Glue']
    shrink_film_materials = [m for m in materials if base_material_en(m) == 'Shrink Film']

    for prod in products:
        prod_code = prod.get('code', '')
        lang = current_lang()
        prod_name = prod.get('name_en', prod.get('name_ar', prod_code)) if lang == 'en' else prod.get('name_ar', prod_code)
        prod_size = prod.get('size', '')
        if not prod_code:
            continue

        if prod_code not in bom_details:
            bom_details[prod_code] = {}

        bd = bom_details[prod_code]
        packaging = prod.get('packaging', 'كرتون')
        lang = current_lang()
        unit_label = t.get("carton", "كرتون") if packaging == "كرتون" else t.get("shrink", "شرنك")
        packaging_label = t.get("carton", "كرتون") if packaging == "كرتون" else t.get("shrink", "شرنك")

        with st.expander(f"📦 {prod_name} ({prod_size}) - {packaging_label}", expanded=True):
            st.markdown(t.get("bom_production_unit", "**Production unit: {unit}**").format(unit=unit_label))
            
            # عدد العبوات داخل الوحدة
            pkg_label = t.get("wizard_units_per_pkg", "عدد العبوات في {pkg}").replace("{pkg}", unit_label)
            if packaging == "كرتون":
                bd['units_per_carton'] = st.number_input(pkg_label,
                    min_value=1, value=int(bd.get('units_per_carton', 48)),
                    key=f"bd_upkg_{prod_code}")
            else:
                bd['units_per_shrink'] = st.number_input(pkg_label,
                    min_value=1, value=int(bd.get('units_per_shrink', 20)),
                    key=f"bd_upkg_{prod_code}")

            # تعيين تلقائي: عدد البريفورم = عدد الليبل = عدد الغطاء = عدد العبوات في الوحدة
            if packaging == "كرتون":
                units_per = bd.get('units_per_carton', 48)
            else:
                units_per = bd.get('units_per_shrink', 20)
            bd['preforms_per_unit'] = units_per
            bd['caps_per_unit'] = units_per
            bd['labels_per_unit'] = units_per

            st.markdown("---")
            st.markdown(t.get("bom_components_auto_title", "### Components per Unit (auto count = {count})").format(count=units_per))

            # المكونات الأساسية لكل عبوة
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(t.get("bom_preform_label", "**Preform (size-specific)**"))
                st.caption(t.get("bom_count_per_unit", "Count: {count}").format(count=units_per))
                matching_preforms = [m for m in preform_materials if m.get('size') == prod_size or m.get('size') == 'general']
                if matching_preforms:
                    preform_codes = [m['code'] for m in matching_preforms]
                    current_preform = bd.get('preform_material_id')
                    preform_idx = next((i for i, m in enumerate(matching_preforms) if m['code'] == current_preform), 0)
                    selected_preform = st.selectbox(
                        t.get("bom_select_preform", "Select Preform"),
                        options=preform_codes,
                        format_func=lambda x: next((display_material(m, lang) for m in matching_preforms if m['code'] == x), x),
                        index=preform_idx if preform_idx < len(matching_preforms) else 0,
                        key=f"preform_{prod_code}"
                    )
                    bd['preform_material_id'] = selected_preform
                else:
                    st.warning(t.get("bom_no_preform", "⚠️ No preform available for this size"))
                    bd['preform_material_id'] = None

            with col2:
                st.markdown(t.get("bom_cap_label", "**Cap (general)**"))
                st.caption(t.get("bom_count_per_unit", "Count: {count}").format(count=units_per))
                if cap_materials:
                    cap_codes = [m['code'] for m in cap_materials]
                    current_cap = bd.get('cap_material_id')
                    cap_idx = next((i for i, m in enumerate(cap_materials) if m['code'] == current_cap), 0)
                    selected_cap = st.selectbox(
                        t.get("bom_select_cap", "Select Cap"),
                        options=cap_codes,
                        format_func=lambda x: next((display_material(m, lang) for m in cap_materials if m['code'] == x), x),
                        index=cap_idx if cap_idx < len(cap_materials) else 0,
                        key=f"cap_{prod_code}"
                    )
                    bd['cap_material_id'] = selected_cap
                else:
                    st.warning(t.get("bom_no_cap", "⚠️ No cap available"))
                    bd['cap_material_id'] = None

            with col3:
                st.markdown(t.get("bom_label_label", "**Label (size-specific)**"))
                st.caption(t.get("bom_count_per_unit", "Count: {count}").format(count=units_per))
                matching_labels = [m for m in label_materials if m.get('size') == prod_size or m.get('size') == 'general']
                if matching_labels:
                    label_codes = [m['code'] for m in matching_labels]
                    current_label = bd.get('label_material_id')
                    label_idx = next((i for i, m in enumerate(matching_labels) if m['code'] == current_label), 0)
                    selected_label = st.selectbox(
                        t.get("bom_select_label", "Select Label"),
                        options=label_codes,
                        format_func=lambda x: next((display_material(m, lang) for m in matching_labels if m['code'] == x), x),
                        index=label_idx if label_idx < len(matching_labels) else 0,
                        key=f"label_{prod_code}"
                    )
                    bd['label_material_id'] = selected_label
                else:
                    st.warning(t.get("bom_no_label", "⚠️ No label available for this size"))
                    bd['label_material_id'] = None

            st.markdown("---")
            st.markdown(t.get("bom_label_glue_section", "### Label Glue (by weight)"))

            if label_glue_materials:
                glue_codes = [m['code'] for m in label_glue_materials]
                current_glue = bd.get('label_glue_material_id')
                glue_idx = next((i for i, m in enumerate(label_glue_materials) if m['code'] == current_glue), 0)
                selected_glue = st.selectbox(
                    t.get("bom_select_label_glue", "Select Label Glue"),
                    options=glue_codes,
                    format_func=lambda x: next((display_material(m, lang) for m in label_glue_materials if m['code'] == x), x),
                    index=glue_idx if glue_idx < len(label_glue_materials) else 0,
                    key=f"label_glue_{prod_code}"
                )
                bd['label_glue_material_id'] = selected_glue
                bd['label_glue_grams_per_bottle'] = st.number_input(
                    t.get("bom_weight_per_bottle", "Weight per Bottle (grams)"),
                    min_value=0.0, step=0.001, format="%.3f",
                    value=float(bd.get('label_glue_grams_per_bottle', 0.135)),
                    key=f"label_glue_qty_{prod_code}",
                    help=t.get("bom_weight_help", "Weight in grams per bottle")
                )
            else:
                st.warning(t.get("bom_no_label_glue", "⚠️ No label glue available"))
                bd['label_glue_material_id'] = None

            st.markdown("---")
            
            # مواد التعبئة حسب النوع
            if packaging == "كرتون":
                st.markdown(t.get("bom_carton_packaging", "### Packaging Materials (Carton)"))
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(t.get("bom_carton_label", "**Carton (size-specific)**"))
                    matching_cartons = [m for m in carton_materials if m.get('size') == prod_size or m.get('size') == 'general']
                    if matching_cartons:
                        carton_codes = [m['code'] for m in matching_cartons]
                        current_carton = bd.get('carton_material_id')
                        carton_idx = next((i for i, m in enumerate(matching_cartons) if m['code'] == current_carton), 0)
                        selected_carton = st.selectbox(
                            t.get("bom_select_carton", "Select Carton"),
                            options=carton_codes,
                            format_func=lambda x: next((display_material(m, lang) for m in matching_cartons if m['code'] == x), x),
                            index=carton_idx if carton_idx < len(matching_cartons) else 0,
                            key=f"carton_{prod_code}"
                        )
                        bd['carton_material_id'] = selected_carton
                    else:
                        st.warning(t.get("bom_no_carton", "⚠️ No carton available for this size"))
                        bd['carton_material_id'] = None
                
                with col2:
                    st.markdown(t.get("bom_carton_glue_section", "**Carton Glue (by weight)**"))
                    if carton_glue_materials:
                        glue_codes = [m['code'] for m in carton_glue_materials]
                        current_glue = bd.get('carton_glue_material_id')
                        glue_idx = next((i for i, m in enumerate(carton_glue_materials) if m['code'] == current_glue), 0)
                        selected_glue = st.selectbox(
                            t.get("bom_select_carton_glue", "Select Carton Glue"),
                            options=glue_codes,
                            format_func=lambda x: next((display_material(m, lang) for m in carton_glue_materials if m['code'] == x), x),
                            index=glue_idx if glue_idx < len(carton_glue_materials) else 0,
                            key=f"carton_glue_{prod_code}"
                        )
                        bd['carton_glue_material_id'] = selected_glue
                        bd['carton_glue_grams_per_carton'] = st.number_input(
                            t.get("bom_weight_per_carton", "Weight per Carton (grams)"),
                            min_value=0.0, step=0.001, format="%.3f",
                            value=float(bd.get('carton_glue_grams_per_carton', 0.5)),
                            key=f"carton_glue_qty_{prod_code}",
                            help=t.get("bom_weight_carton_help", "Weight in grams per carton")
                        )
                    else:
                        st.warning(t.get("bom_no_carton_glue", "⚠️ No carton glue available"))
                        bd['carton_glue_material_id'] = None
                
                bd['shrink_material_id'] = None
                bd['shrink_divider_material_id'] = None
                bd['shrink_dividers_per_pallet'] = None
                bd['shrink_pieces_per_roll'] = None

            else:
                st.markdown(t.get("bom_shrink_packaging", "### Packaging Materials (Shrink)"))
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(t.get("bom_shrink_label", "**Shrink (size-specific)**"))
                    matching_shrinks = [m for m in shrink_materials if m.get('size') == prod_size or m.get('size') == 'general']
                    if matching_shrinks:
                        shrink_codes = [m['code'] for m in matching_shrinks]
                        current_shrink = bd.get('shrink_material_id')
                        shrink_idx = next((i for i, m in enumerate(matching_shrinks) if m['code'] == current_shrink), 0)
                        selected_shrink = st.selectbox(
                            t.get("bom_select_shrink", "Select Shrink"),
                            options=shrink_codes,
                            format_func=lambda x: next((display_material(m, lang) for m in matching_shrinks if m['code'] == x), x),
                            index=shrink_idx if shrink_idx < len(matching_shrinks) else 0,
                            key=f"shrink_{prod_code}"
                        )
                        bd['shrink_material_id'] = selected_shrink
                        
                        selected_shrink_mat = next((m for m in matching_shrinks if m['code'] == selected_shrink), None)
                        if selected_shrink_mat:
                            default_pieces = selected_shrink_mat.get('pieces_per_roll') or 1980
                            bd['shrink_pieces_per_roll'] = st.number_input(
                                t.get("bom_shrink_pieces_per_roll", "Shrink Pieces per Roll"),
                                min_value=1, value=int(bd.get('shrink_pieces_per_roll', default_pieces)),
                                key=f"shrink_pieces_{prod_code}",
                                help=t.get("bom_shrink_roll_help", "Used to convert from pieces to rolls for inventory deduction")
                            )
                            st.info(t.get("bom_shrink_roll_note", "⚠️ Note: Shrink is calculated in rolls for inventory and in pieces for production. The system will auto-convert: required pieces ÷ {pieces} = number of rolls").format(pieces=bd['shrink_pieces_per_roll']))
                    else:
                        st.warning(t.get("bom_no_shrink", "⚠️ No shrink available for this size"))
                        bd['shrink_material_id'] = None
                
                with col2:
                    st.markdown(t.get("bom_shrink_divider_label", "**Shrink Dividers (general)**"))
                    if shrink_divider_materials:
                        divider_codes = [m['code'] for m in shrink_divider_materials]
                        current_divider = bd.get('shrink_divider_material_id')
                        divider_idx = next((i for i, m in enumerate(shrink_divider_materials) if m['code'] == current_divider), 0)
                        selected_divider = st.selectbox(
                            t.get("bom_select_divider", "Select Shrink Divider"),
                            options=divider_codes,
                            format_func=lambda x: next((display_material(m, lang) for m in shrink_divider_materials if m['code'] == x), x),
                            index=divider_idx if divider_idx < len(shrink_divider_materials) else 0,
                            key=f"divider_{prod_code}"
                        )
                        bd['shrink_divider_material_id'] = selected_divider
                        bd['shrink_dividers_per_pallet'] = st.number_input(
                            t.get("bom_dividers_per_pallet", "Dividers per Pallet"),
                            min_value=1, value=int(bd.get('shrink_dividers_per_pallet', 7)),
                            key=f"dividers_per_pallet_{prod_code}",
                            help=t.get("bom_dividers_help", "Number of dividers used per pallet (varies per factory)")
                        )
                    else:
                        st.warning(t.get("bom_no_divider", "⚠️ No shrink divider available"))
                        bd['shrink_divider_material_id'] = None
                
                bd['carton_material_id'] = None
                bd['carton_glue_material_id'] = None
                bd['carton_glue_grams_per_carton'] = None

            st.markdown("---")
            
            st.markdown(t.get("bom_shrink_film_section", "### Shrink Film (general - by weight per pallet)"))
            
            if shrink_film_materials:
                film_codes = [m['code'] for m in shrink_film_materials]
                current_film = bd.get('shrink_film_material_id')
                film_idx = next((i for i, m in enumerate(shrink_film_materials) if m['code'] == current_film), 0)
                selected_film = st.selectbox(
                    t.get("bom_select_film", "Select Shrink Film"),
                    options=film_codes,
                    format_func=lambda x: next((display_material(m, lang) for m in shrink_film_materials if m['code'] == x), x),
                    index=film_idx if film_idx < len(shrink_film_materials) else 0,
                    key=f"shrink_film_{prod_code}"
                )
                bd['shrink_film_material_id'] = selected_film
                
                col_a, col_b = st.columns(2)
                with col_a:
                    bd['units_per_pallet'] = st.number_input(
                        t.get("bom_units_per_pallet", "Units per Pallet"),
                        min_value=1, value=int(bd.get('units_per_pallet', 48)),
                        key=f"units_per_pallet_{prod_code}",
                        help=t.get("bom_units_per_pallet_help", "Number of cartons or shrink packs per pallet")
                    )
                with col_b:
                    bd['shrink_film_grams_per_pallet'] = st.number_input(
                        t.get("bom_film_grams_per_pallet", "Shrink Film Weight per Pallet (grams)"),
                        min_value=0.0, step=0.001, format="%.3f",
                        value=float(bd.get('shrink_film_grams_per_pallet', 500)),
                        key=f"shrink_film_qty_{prod_code}",
                        help=t.get("bom_film_grams_help", "Weight in grams per pallet")
                    )
            else:
                st.warning(t.get("bom_no_film", "⚠️ No shrink film available"))
                bd['shrink_film_material_id'] = None

            st.markdown("---")

        bom_details[prod_code] = bd
        st.session_state.wizard_bom_details = bom_details

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button(t.get("wizard_prev", "← Back"), use_container_width=True):
            st.session_state.wizard_step = 3
            st.rerun()
    with col2:
        if st.button(t.get("wizard_next_shift", "Next → Shift Times"), type="primary", use_container_width=True):
            # التحقق الإلزامي من جميع المكونات
            errors = []
            for prod in products:
                prod_code = prod.get('code', '')
                prod_name = prod.get('name_ar', prod_code)
                if not prod_code:
                    continue
                
                bd = bom_details.get(prod_code, {})
                packaging = prod.get('packaging', 'كرتون')
                
                if not bd.get('preform_material_id'):
                    errors.append(t.get("bom_missing_preform", "{product}: Preform").format(product=prod_name))
                if not bd.get('cap_material_id'):
                    errors.append(t.get("bom_missing_cap", "{product}: Cap").format(product=prod_name))
                if not bd.get('label_material_id'):
                    errors.append(t.get("bom_missing_label", "{product}: Label").format(product=prod_name))
                if not bd.get('label_glue_material_id'):
                    errors.append(t.get("bom_missing_label_glue", "{product}: Label Glue").format(product=prod_name))
                
                if packaging == "كرتون":
                    if not bd.get('carton_material_id'):
                        errors.append(t.get("bom_missing_carton", "{product}: Carton").format(product=prod_name))
                    if not bd.get('carton_glue_material_id'):
                        errors.append(t.get("bom_missing_carton_glue", "{product}: Carton Glue").format(product=prod_name))
                else:
                    if not bd.get('shrink_material_id'):
                        errors.append(t.get("bom_missing_shrink", "{product}: Shrink").format(product=prod_name))
                    if not bd.get('shrink_divider_material_id'):
                        errors.append(t.get("bom_missing_divider", "{product}: Shrink Divider").format(product=prod_name))
                    if not bd.get('shrink_dividers_per_pallet'):
                        errors.append(t.get("bom_missing_dividers_count", "{product}: Dividers per Pallet").format(product=prod_name))
                
                if not bd.get('shrink_film_material_id'):
                    errors.append(t.get("bom_missing_film", "{product}: Shrink Film").format(product=prod_name))
                if not bd.get('units_per_pallet'):
                    errors.append(t.get("bom_missing_units_per_pallet", "{product}: Units per Pallet").format(product=prod_name))
                if not bd.get('shrink_film_grams_per_pallet'):
                    errors.append(t.get("bom_missing_film_grams", "{product}: Shrink Film Weight per Pallet").format(product=prod_name))
            
            if errors:
                st.error(t.get("bom_required_error", "⚠️ All required components must be filled:\n{errors}").format(errors="\n".join(f"- {e}" for e in errors)))
            else:
                st.session_state.wizard_step = 5
                st.rerun()

def step5_shift_settings(t):
    st.markdown(f"### 🕐 {t.get('wizard_step5_title', 'Step 5: Shift Settings')}")
    st.caption(t.get('wizard_step4_caption', 'Set shift start/end and breaks'))

    shift = st.session_state.wizard_shift

    col1, col2, col3 = st.columns(3)
    with col1:
        shift['start_time'] = st.time_input(t.get("wizard_shift_start", "Shift start"),
                                             value=shift.get('start_time', time(8, 0)))
    with col2:
        shift['end_time'] = st.time_input(t.get("wizard_shift_end", "Shift end"),
                                           value=shift.get('end_time', time(2, 0)))
    with col3:
        shift['break_minutes'] = st.number_input(t.get("wizard_break_total", "Total break (min)"),
                                                   min_value=0, max_value=480,
                                                   value=shift.get('break_minutes', 180), step=15)

    st.markdown("---")
    st.markdown(f"#### {t.get('wizard_breaks_header', 'Detailed Breaks')}")

    breaks = shift.get('breaks', [])
    for i, br in enumerate(breaks):
        col1, col2, col3 = st.columns([3, 3, 1])
        with col1:
            breaks[i]['start'] = st.time_input(t.get("wizard_break_start", "Break {n} start").replace("{n}", str(i+1)),
                                                value=br.get('start', time(10, 0)),
                                                key=f"br_start_{i}")
        with col2:
            breaks[i]['end'] = st.time_input(t.get("wizard_break_end", "Break {n} end").replace("{n}", str(i+1)),
                                              value=br.get('end', time(10, 30)),
                                              key=f"br_end_{i}")
        with col3:
            if st.button("🗑️", key=f"br_del_{i}"):
                breaks.pop(i)
                st.rerun()

    if st.button(t.get("wizard_add_break", "➕ Add Break")):
        breaks.append({'start': time(12, 0), 'end': time(13, 0)})
        st.rerun()

    shift['breaks'] = breaks
    st.session_state.wizard_shift = shift

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button(t.get("wizard_prev", "← Back"), use_container_width=True):
            st.session_state.wizard_step = 4
            st.rerun()
    with col2:
        if st.button(t.get("wizard_next_emails", "Next → Admin Emails"), type="primary", use_container_width=True):
            st.session_state.wizard_step = 6
            st.rerun()

def step6_admin_emails(t):
    st.markdown(f"### 📧 {t.get('wizard_step6_title', 'Step 6: Admin Emails')}")
    st.caption(t.get('wizard_step5_caption', 'Add emails for weekly reports'))

    emails = st.session_state.wizard_emails

    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
    with col1:
        new_email = st.text_input(t.get("wizard_email_input", "Email"), key="new_email_input",
                                   placeholder="email@example.com")
    with col2:
        new_name = st.text_input(t.get("wizard_name_input", "Name"), key="new_name_input",
                                  placeholder="Ahmed")
    with col3:
        new_role = st.text_input(t.get("wizard_role_input", "Role"), key="new_role_input",
                                  placeholder="Factory Manager")
    with col4:
        if st.button(t.get("wizard_email_add", "➕ Add"), use_container_width=True):
            if new_email and '@' in new_email:
                emails.append({"email": new_email, "name": new_name, "role": new_role})
                st.rerun()
            else:
                st.error(t.get("wizard_email_invalid", "Please enter a valid email"))

    st.markdown("---")

    if emails:
        st.subheader(f"📋 {t.get('wizard_emails_header', 'Email List')}")
        for idx, em in enumerate(emails):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            with col1:
                st.text(em.get('email', ''))
            with col2:
                st.text(em.get('name', ''))
            with col3:
                st.text(em.get('role', ''))
            with col4:
                if st.button("🗑️", key=f"em_del_{idx}"):
                    emails.pop(idx)
                    st.rerun()
    else:
        st.info(t.get("wizard_no_emails", "No emails yet."))

    st.markdown("---")
    col1, col2, col3 = st.columns([2, 2, 2])
    with col1:
        if st.button(t.get("wizard_prev", "← Back"), use_container_width=True):
            st.session_state.wizard_step = 5
            st.rerun()
    with col2:
        if st.button(t.get("wizard_finish", "🚀 Finish & Review"), type="primary", use_container_width=True):
            st.session_state.wizard_emails = emails
            st.session_state.wizard_step = 7
            st.rerun()
    with col3:
        if st.button(t.get("wizard_skip", "⏭️ Skip"), use_container_width=True):
            st.session_state.wizard_emails = emails
            st.session_state.wizard_step = 7
            st.rerun()

def step7_summary_and_create(t):
    st.markdown(f"### ✅ {t.get('wizard_step7_title', 'Final Review & Create')}")
    st.caption(t.get('wizard_step6_caption', 'Review data before creating the factory'))

    f = st.session_state.wizard_factory
    lines = st.session_state.wizard_lines
    products = st.session_state.wizard_products
    materials = st.session_state.wizard_materials
    line_products = st.session_state.wizard_line_products
    bom_details = st.session_state.wizard_bom_details
    shift = st.session_state.wizard_shift
    emails = st.session_state.wizard_emails

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"#### 🏭 {t.get('wizard_factory_data', 'Factory Details')}")
        st.markdown(f"- **{t.get('wizard_name_ar', 'Name (AR)')}:** {f.get('name_ar', '')}")
        st.markdown(f"- **{t.get('wizard_code', 'Code')}:** {f.get('code', '')}")
        st.markdown(f"- **{t.get('wizard_admin_name', 'Admin')}:** {f.get('admin_name', '')}")
        st.markdown(f"- **{t.get('wizard_admin_username', 'Admin User')}:** {f.get('admin_username', '')}")

    with col2:
        st.markdown(f"#### 📊 {t.get('wizard_summary', 'Summary')}")
        st.markdown(f"- **{t.get('wizard_summary_lines', 'Lines').replace('{n}', str(len(lines)))}:** {len(lines)}")
        st.markdown(f"- **{t.get('wizard_summary_products', 'Products').replace('{n}', str(len(products)))}:** {len(products)}")
        mat_count = len(materials) if materials else 0
        st.markdown(f"- **{t.get('wizard_summary_materials', 'Materials').replace('{n}', str(mat_count))}:** {mat_count}")
        st.markdown(f"- **{t.get('wizard_summary_emails', 'Emails').replace('{n}', str(len(emails)))}:** {len(emails)}")

    if lines:
        st.markdown(f"#### 🏭 {t.get('wizard_lines_and_products', 'Lines & Products')}")
        for line in lines:
            line_code = line.get('code', '')
            line_name = line.get('name_ar', line_code)
            assigned = line_products.get(line_code, {})
            prod_names = []
            for pc, sp in assigned.items():
                pname = next((p.get('name_ar', pc) for p in products if p.get('code') == pc), pc)
                prod_names.append(f"{pname} ({sp}/hr)")
            st.markdown(f"- **{line_name}**: {', '.join(prod_names) if prod_names else t.get('wizard_no_products_assigned', 'No products')}")

    st.markdown("---")
    st.warning(t.get("wizard_warning", "⚠️ Verify data before creating. Cannot undo."))

    col1, col2 = st.columns(2)
    with col1:
        if st.button(t.get("wizard_back_edit", "← Back to Edit"), use_container_width=True):
            st.session_state.wizard_step = 6
            st.rerun()

    with col2:
        if st.button(t.get("wizard_confirm_create", "🚀 Confirm Factory Creation"), type="primary", use_container_width=True):
            create_factory()

def create_factory():
    f = st.session_state.wizard_factory
    lines = st.session_state.wizard_lines
    products = st.session_state.wizard_products
    materials = st.session_state.wizard_materials
    line_products = st.session_state.wizard_line_products
    bom_details = st.session_state.wizard_bom_details
    shift = st.session_state.wizard_shift
    emails = st.session_state.wizard_emails
    users = st.session_state.get('wizard_users', {})
    t = load_language(st.session_state.get('lang', 'ar'))

    try:
        company_id = db_manager.create_company(
            name_ar=f.get('name_ar', ''),
            name_en=f.get('name_en', ''),
            code=f.get('code', ''),
            email=f.get('email', ''),
            phone=f.get('phone', ''),
            address=f.get('address', '')
        )

        if not company_id:
            st.error(t.get("wizard_duplicate_code", "❌ Failed to create factory. Code may be duplicated."))
            return

        # إنشاء سجل factories
        try:
            session = db_manager.get_session()
            from database import Factory
            existing = session.query(Factory).filter(Factory.id == company_id).first()
            if not existing:
                factory = Factory(
                    id=company_id,
                    name_ar=f.get('name_ar', f'Factory {company_id}'),
                    name_en=f.get('name_en', f'Factory {company_id}'),
                    code=f.get('code', f'F{company_id}'),
                    status='active',
                    created_at=datetime.now()
                )
                session.add(factory)
                session.commit()
            session.close()
        except Exception as e:
            print(f"Factory record skipped: {e}")

        # إنشاء خطوط الإنتاج
        line_id_map = {}
        for line in lines:
            if line.get('name_ar') and line.get('code'):
                lid = db_manager.create_production_line(
                    company_id=company_id,
                    name_ar=line['name_ar'],
                    name_en=line.get('name_en', line['name_ar']),
                    code=line['code']
                )
                if lid:
                    line_id_map[line['code']] = lid

        # إنشاء المواد الخام (من المستخدم فقط - بدون افتراضية)
        material_id_map = {}
        for mat in materials:
            if mat.get('name_ar') and mat.get('code'):
                mid = db_manager.create_material(
                    company_id=company_id,
                    name_ar=mat['name_ar'],
                    name_en=mat.get('name_en', mat['name_ar']),
                    code=mat['code'],
                    unit=mat.get('unit', 'قطعة'),
                    min_stock=mat.get('min_stock', 0),
                    size=mat.get('size', 'general')
                )
                if mid:
                    material_id_map[mat['code']] = mid

        # إنشاء الأصناف
        product_id_map = {}
        for prod in products:
            if prod.get('name_ar') and prod.get('code'):
                pid = db_manager.create_product(
                    company_id=company_id,
                    name_ar=prod['name_ar'],
                    name_en=prod.get('name_en', prod['name_ar']),
                    code=prod['code'],
                    pieces_per_unit=1
                )
                if pid:
                    product_id_map[prod['code']] = pid

        # إنشاء BOM (ربط المنتجات بالمواد الخام حسب إدخال المستخدم + تفاصيل BOM)
        for prod in products:
            prod_code = prod.get('code', '')
            prod_id = product_id_map.get(prod_code)
            if not prod_id:
                continue

            bd = bom_details.get(prod_code, {})
            packaging = prod.get('packaging', 'كرتون')

            # إنشاء تفاصيل BOM مع المواد المرتبطة
            packaging_type = 'carton' if packaging == 'كرتون' else 'shrink'
            
            # تحويل معرفات المواد من كود إلى ID
            preform_material_id = material_id_map.get(bd.get('preform_material_id')) if bd.get('preform_material_id') else None
            cap_material_id = material_id_map.get(bd.get('cap_material_id')) if bd.get('cap_material_id') else None
            label_material_id = material_id_map.get(bd.get('label_material_id')) if bd.get('label_material_id') else None
            carton_material_id = material_id_map.get(bd.get('carton_material_id')) if bd.get('carton_material_id') else None
            shrink_material_id = material_id_map.get(bd.get('shrink_material_id')) if bd.get('shrink_material_id') else None
            shrink_divider_material_id = material_id_map.get(bd.get('shrink_divider_material_id')) if bd.get('shrink_divider_material_id') else None
            label_glue_material_id = material_id_map.get(bd.get('label_glue_material_id')) if bd.get('label_glue_material_id') else None
            carton_glue_material_id = material_id_map.get(bd.get('carton_glue_material_id')) if bd.get('carton_glue_material_id') else None
            shrink_film_material_id = material_id_map.get(bd.get('shrink_film_material_id')) if bd.get('shrink_film_material_id') else None
            
            db_manager.create_product_bom_detail(
                company_id=company_id,
                product_id=prod_id,
                preforms_per_unit=bd.get('preforms_per_unit', 1),
                caps_per_unit=bd.get('caps_per_unit', 1),
                labels_per_unit=bd.get('labels_per_unit', 1),
                packaging_type=packaging_type,
                units_per_carton=bd.get('units_per_carton', 48),
                units_per_shrink=bd.get('units_per_shrink', 20),
                shrink_pieces_per_roll=bd.get('shrink_pieces_per_roll', 1980),
                label_glue_grams_per_bottle=bd.get('label_glue_grams_per_bottle', 0.135),
                carton_glue_grams_per_carton=bd.get('carton_glue_grams_per_carton', 0.5),
                min_stock_units=bd.get('min_stock_units', 0),
                preform_material_id=preform_material_id,
                cap_material_id=cap_material_id,
                label_material_id=label_material_id,
                carton_material_id=carton_material_id,
                shrink_material_id=shrink_material_id,
                shrink_divider_material_id=shrink_divider_material_id,
                shrink_dividers_per_pallet=bd.get('shrink_dividers_per_pallet'),
                label_glue_material_id=label_glue_material_id,
                carton_glue_material_id=carton_glue_material_id,
                shrink_film_material_id=shrink_film_material_id,
                shrink_film_grams_per_pallet=bd.get('shrink_film_grams_per_pallet'),
                units_per_pallet=bd.get('units_per_pallet')
            )

        # إنشاء سرعات الإنتاج
        for line_code, prods in line_products.items():
            line_id = line_id_map.get(line_code)
            if not line_id:
                continue
            for prod_code, speed in prods.items():
                prod_id = product_id_map.get(prod_code)
                if prod_id and speed > 0:
                    db_manager.create_line_product_speed(company_id, line_id, prod_id, speed)

        # إنشاء الوردية
        start_str = shift.get('start_time', time(8, 0)).strftime("%H:%M")
        end_str = shift.get('end_time', time(2, 0)).strftime("%H:%M")
        db_manager.create_shift(
            company_id=company_id,
            name_ar="الوردية الرئيسية",
            name_en="Main Shift",
            start_time=start_str,
            end_time=end_str,
            break_duration=shift.get('break_minutes', 180)
        )

        # إنشاء مستخدمي المصنع (admin + pro + tec + sto + quality)
        import bcrypt
        session = db_manager.get_session()
        from database import User

        user_defs = [
            ('admin', f.get('admin_username', 'admin'), f.get('admin_password', '100'), 'admin', f.get('admin_name', 'مدير المصنع'), '👑'),
            ('pro', 'pro', users.get('supervisor_pass', '400'), 'supervisor', 'مشرف إنتاج', '👔'),
            ('tec', 'tec', users.get('technician_pass', '300'), 'technician', 'فني صيانة', '🔧'),
            ('sto', 'sto', users.get('storekeeper_pass', '200'), 'storekeeper', 'أمين مخزن', '📦'),
            ('quality', 'quality', users.get('quality_pass', 'quality123'), 'quality', 'مراقب جودة', '🔍'),
        ]

        for default_user, username, password, role, name, icon in user_defs:
            existing = session.query(User).filter(
                User.username == username,
                User.company_id == company_id
            ).first()
            if not existing:
                password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                new_user = User(
                    username=username,
                    password_hash=password_hash,
                    role=role,
                    name=name,
                    icon=icon,
                    is_active=True,
                    created_at=datetime.now(),
                    must_change_password=(default_user != 'admin'),
                    is_super_admin=False,
                    company_id=company_id
                )
                session.add(new_user)
        session.commit()
        session.close()

        # إضافة إيميلات المسئولين
        for em in emails:
            db_manager.create_factory_email(
                company_id=company_id,
                email=em.get('email', ''),
                name=em.get('name', ''),
                role=em.get('role', '')
            )

        # تهيئة المخزون الأولي
        _init_factory_inventory(company_id, products, materials, material_id_map)

        st.balloons()
        st.success(t.get("wizard_success", "✅ Factory **{name}** created!").replace("{name}", f.get('name_ar', '')))
        st.info(t.get("wizard_login_info", "🔑 Login with user: **{user}**").replace("{user}", f.get('admin_username', '')))
        st.info(t.get("wizard_password_info", "🔐 Password: **{password}**").replace("{password}", f.get('admin_password', '')))
        st.info(t.get("wizard_factory_id_info", "🏭 Factory ID: **{factory_id}**").replace("{factory_id}", str(company_id)))

        try:
            db_manager.add_info_log('factory_created',
                f"Factory '{f.get('name_ar', '')}' (code: {f.get('code', '')}) created",
                f"Lines: {len(lines)}, Products: {len(products)}")
        except:
            pass

        if st.button(t.get("wizard_back_login", "🏠 Back to Login"), use_container_width=True):
            reset_wizard()
            st.rerun()

    except Exception as e:
        st.error(t.get("wizard_create_error", "❌ Error: {error}").replace("{error}", str(e)))
        import traceback
        st.code(traceback.format_exc())


def _init_factory_inventory(company_id, products, materials, material_id_map):
    """تهيئة سجلات المخزون للمصنع الجديد"""
    try:
        session = db_manager.get_session()
        from database import RawMaterial, FinishedGood

        for code, mid in material_id_map.items():
            existing = session.query(RawMaterial).filter(
                RawMaterial.material_id == code,
                RawMaterial.factory_id == company_id
            ).first()
            if not existing:
                mat_data = {
                    'material_id': code,
                    'name_ar': code,
                    'name_en': code,
                    'current_stock': 0,
                    'min_stock': 0,
                    'max_stock': 0,
                    'unit': 'قطعة',
                    'company_id': company_id,
                    'factory_id': company_id
                }
                for mat in materials:
                    if mat.get('code') == code:
                        mat_data['name_ar'] = mat.get('name_ar', code)
                        mat_data['name_en'] = mat.get('name_en', code)
                        mat_data['min_stock'] = mat.get('min_stock', 0)
                        mat_data['unit'] = mat.get('unit', 'قطعة')
                        break
                if not hasattr(RawMaterial, 'company_id'):
                    mat_data.pop('company_id', None)
                if not hasattr(RawMaterial, 'factory_id'):
                    mat_data.pop('factory_id', None)
                rm = RawMaterial(**mat_data)
                session.add(rm)

        for prod in products:
            prod_code = prod.get('code', '')
            prod_name = prod.get('name_en', prod.get('name_ar', prod_code))
            existing = session.query(FinishedGood).filter(
                FinishedGood.name == prod_name,
                FinishedGood.factory_id == company_id
            ).first()
            if not existing:
                fg_kwargs = dict(
                    name=prod_name,
                    opening_balance=0,
                    stock_in=0,
                    stock_out=0,
                    balance=0,
                    unit='وحدة',
                    month_key=datetime.now().strftime('%Y-%m'),
                    company_id=company_id,
                    factory_id=company_id
                )
                if not hasattr(FinishedGood, 'company_id'):
                    fg_kwargs.pop('company_id', None)
                if not hasattr(FinishedGood, 'factory_id'):
                    fg_kwargs.pop('factory_id', None)
                fg = FinishedGood(**fg_kwargs)
                session.add(fg)

        session.commit()
        session.close()
    except Exception as e:
        print(f"⚠️ Inventory init warning: {e}")


def show_factory_setup_wizard(t):
    init_wizard_state()

    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <h1 style="color: #1e3a5f;">{t.get('wizard_title', '🏭 New Factory Setup Wizard')}</h1>
        <p style="color: #64748b;">{t.get('wizard_subtitle', 'New Factory Setup Wizard')}</p>
    </div>
    """, unsafe_allow_html=True)

    show_wizard_progress(t)
    st.markdown("---")

    step = st.session_state.wizard_step

    if step == 1:
        step1_factory_info(t)
    elif step == 2:
        step2_lines_and_products(t)
    elif step == 3:
        step3_raw_materials(t)
    elif step == 4:
        step4_product_bom(t)
    elif step == 5:
        step5_shift_settings(t)
    elif step == 6:
        step6_admin_emails(t)
    elif step == 7:
        step7_summary_and_create(t)
    else:
        st.error("خطأ: خطوة غير معروفة")
