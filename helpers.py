# helpers.py - نسخة كاملة مع الدوال الجديدة

import math
import pandas as pd
from datetime import datetime, timedelta
from constants import BOM, SHRINK_PALLET_CONFIG

def normalize_line_name(line):
    """تحويل اسم الخط إلى الصيغة الإنجليزية"""
    if not line:
        return ""
    if "الخط الأول" in str(line) or "line 1" in str(line).lower():
        return "Line 1"
    elif "الخط الثاني" in str(line) or "line 2" in str(line).lower():
        return "Line 2"
    return str(line)

def clean_line_name(line):
    """تنظيف اسم الخط للعرض (اسم بديل)"""
    return normalize_line_name(line)

# ============================================================================
# BOM Helper Functions
# ============================================================================

def get_bom_unit_info(product, company_id=None):
    """الحصول على معلومات BOM للمنتج"""
    info = {
        "pieces_per_unit": 1,
        "packaging_per_unit": 1.0,
        "packaging_is_weight": False,
        "preform_material": None,
    }

    # Try database BOM detail first
    if company_id:
        from database import db_manager, Product, ProductBOMDetail
        session = db_manager.get_session()
        try:
            db_product = session.query(Product).filter(
                Product.company_id == company_id,
                ((Product.name_ar == product) | (Product.name_en == product) | (Product.code == product))
            ).first()
            if db_product:
                detail = session.query(ProductBOMDetail).filter(
                    ProductBOMDetail.company_id == company_id,
                    ProductBOMDetail.product_id == db_product.id
                ).first()
                if detail:
                    info["pieces_per_unit"] = detail.preforms_per_unit
                    info["packaging_per_unit"] = float(detail.units_per_carton) if detail.packaging_type == 'carton' else float(detail.units_per_shrink)
                    info["packaging_is_weight"] = (detail.packaging_type == 'shrink')
                    return info
        except:
            pass
        finally:
            session.close()

    if product not in BOM:
        return info

    for material, qty in BOM[product].items():
        if "بريفورم" in material:
            info["pieces_per_unit"] = int(qty)
            info["preform_material"] = material
        elif "كرتون" in material:
            info["packaging_per_unit"] = float(qty)
            info["packaging_is_weight"] = False
        elif "شرنك" in material:
            info["packaging_per_unit"] = float(qty)
            info["packaging_is_weight"] = True
    return info
# helpers.py - أضف هذه الدوال

def get_shrink_roll_quantity(material_name, required_pieces):
    """
    تحويل الكمية المطلوبة من القطع إلى عدد الرولات
    material_name: اسم المادة (شرنك 200 مل / شرنك 330 مل / شرنك 1.5 لتر)
    required_pieces: عدد القطع المطلوبة
    """
    from constants import SHRINK_ROLL_CONVERSION
    
    # البحث عن اسم المادة في قاموس التحويل
    for key, pieces_per_roll in SHRINK_ROLL_CONVERSION.items():
        if key in material_name:
            # حساب عدد الرولات المطلوبة (تقريب لأعلى)
            rolls_needed = math.ceil(required_pieces / pieces_per_roll)
            actual_pieces = rolls_needed * pieces_per_roll
            print(f"   📦 {material_name}: مطلوب {required_pieces} قطعة → {rolls_needed} رول ({actual_pieces} قطعة)")
            return actual_pieces, pieces_per_roll
    
    # إذا لم يكن شرنك، أرجع نفس الكمية
    return required_pieces, 1

def normalize_material_name(name):
    """Normalize raw material names to avoid duplicates from extra spaces or case."""
    if not isinstance(name, str):
        return ""
    cleaned = name.replace("\u00A0", " ").strip()
    cleaned = " ".join(cleaned.split())
    return cleaned.lower()


def find_raw_materials(session, material_name, factory_id=None):
    """Find all raw material records matching a normalized material name."""
    from database import RawMaterial, db_manager

    if not material_name:
        return []

    normalized = normalize_material_name(material_name)
    if not normalized:
        return []

    # استخدام company_id من session إذا لم يتم تمرير factory_id
    if factory_id is None:
        import streamlit as st
        factory_id = st.session_state.get('company_id') or st.session_state.get('factory_id')

    query = session.query(RawMaterial).filter(
        (RawMaterial.name_ar == material_name) |
        (RawMaterial.name_en == material_name)
    )
    if hasattr(RawMaterial, 'company_id'):
        query = query.filter(RawMaterial.company_id == factory_id)
    elif factory_id:
        query = query.filter(RawMaterial.factory_id == factory_id)
    exact_matches = query.all()
    if exact_matches:
        return exact_matches

    matches = []
    q = session.query(RawMaterial).filter(RawMaterial.is_active == True)
    if hasattr(RawMaterial, 'company_id'):
        q = q.filter(RawMaterial.company_id == factory_id)
    elif factory_id:
        q = q.filter(RawMaterial.factory_id == factory_id)
    materials = q.all()
    for material in materials:
        if normalize_material_name(material.name_ar) == normalized or normalize_material_name(material.name_en) == normalized:
            matches.append(material)
    return matches

def get_materials_required_from_db(company_id, product_name, quantity, preforms_used=0, packaging_used=0):
    """حساب المواد المطلوبة من قاعدة البيانات (BOM المخزن في product_bom_details)"""
    import math
    from database import db_manager, Product, Material, ProductBOMDetail

    session = db_manager.get_session()
    try:
        product = session.query(Product).filter(
            Product.company_id == company_id,
            ((Product.name_ar == product_name) | (Product.name_en == product_name) | (Product.code == product_name))
        ).first()
        if not product:
            return None, "Product not found in database"

        bom_detail = session.query(ProductBOMDetail).filter(
            ProductBOMDetail.company_id == company_id,
            ProductBOMDetail.product_id == product.id
        ).first()

        if not bom_detail:
            return None, "No BOM detail found for this product in database"

        required = {}
        pieces_per_unit = bom_detail.preforms_per_unit or 1
        packaging_type = bom_detail.packaging_type or 'carton'
        actual_bottles = quantity * pieces_per_unit

        # ✅ استخدام القيم الفعلية من تقرير الإنتاج (تشمل الهالك)
        actual_preforms_used = preforms_used if preforms_used > 0 else actual_bottles
        actual_packaging_used = packaging_used if packaging_used > 0 else quantity

        print(f"   📊 Using actual values: preforms={actual_preforms_used}, packaging={actual_packaging_used}")

        # دوال مساعدة لإضافة مادة إلى المطلوب
        def add_material(mat_id, qty):
            if mat_id is None:
                return
            mat = session.query(Material).filter(
                Material.id == mat_id,
                Material.company_id == company_id
            ).first()
            if mat:
                required[mat.code] = required.get(mat.code, 0) + qty

        # ✅ المكونات الأساسية لكل عبوة
        add_material(bom_detail.preform_material_id, actual_preforms_used)  # البريفورم: عدد الزجاجات الفعلي
        add_material(bom_detail.cap_material_id, actual_bottles)  # الغطاء: عدد الزجاجات المنتجة
        add_material(bom_detail.label_material_id, actual_bottles)  # الليبل: عدد الزجاجات المنتجة

        # مواد التعبئة - استخدام القيم الفعلية
        if packaging_type == 'carton':
            add_material(bom_detail.carton_material_id, actual_packaging_used)
        else:
            # شرنك: نحسب عدد الرولات المطلوبة (التحويل من قطعة إلى رول)
            pieces_per_roll = bom_detail.shrink_pieces_per_roll or 1980
            
            # ✅ التحويل الصحيح: الشرنك في المخزون بالرول، في الإنتاج بالقطعة
            # المعادلة: (عدد رول الشرنك المطلوب) = (عدد وحدة التغليف الذي أدخله المستخدم) ÷ (عدد الشرنك في الرول)
            rolls_needed = math.ceil(actual_packaging_used / pieces_per_roll) if actual_packaging_used > 0 else 0
            
            add_material(bom_detail.shrink_material_id, rolls_needed)
            print(f"   📦 Shrink conversion: {actual_packaging_used} units ÷ {pieces_per_roll} units/roll = {rolls_needed} rolls")

        # غراء الليبل (بالكجم) - بناءً على عدد الزجاجات المنتجة
        label_glue_kg = (actual_bottles * (bom_detail.label_glue_grams_per_bottle or 0)) / 1000
        if label_glue_kg > 0:
            add_material(bom_detail.label_glue_material_id, label_glue_kg)

        # غراء الكرتون (بالكجم) - بناءً على الكمية الفعلية للكرتون
        if packaging_type == 'carton':
            carton_glue_kg = (actual_packaging_used * (bom_detail.carton_glue_grams_per_carton or 0)) / 1000
            if carton_glue_kg > 0:
                add_material(bom_detail.carton_glue_material_id, carton_glue_kg)

        # استرتش فيلم (بالكجم) - بناءً على عدد الباليتات
        if bom_detail.shrink_film_material_id and bom_detail.shrink_film_grams_per_pallet and bom_detail.units_per_pallet:
            pallets_needed = math.ceil(quantity / max(bom_detail.units_per_pallet, 1))
            shrink_film_kg = (pallets_needed * bom_detail.shrink_film_grams_per_pallet) / 1000
            add_material(bom_detail.shrink_film_material_id, shrink_film_kg)

        # فواصل الشرنك
        if bom_detail.shrink_divider_material_id and bom_detail.shrink_dividers_per_pallet and bom_detail.units_per_pallet:
            pallets_needed = math.ceil(quantity / max(bom_detail.units_per_pallet, 1))
            dividers_needed = pallets_needed * bom_detail.shrink_dividers_per_pallet
            add_material(bom_detail.shrink_divider_material_id, dividers_needed)

        print(f"📦 DB BOM for {product_name}: {required}")
        return required, None
    except Exception as e:
        print(f"❌ get_materials_required_from_db error: {e}")
        return None, str(e)
    finally:
        session.close()


def get_materials_required(product, quantity, preforms_used=0, packaging_used=0, company_id=None):
    """
    حساب المواد المطلوبة لإنتاج كمية معينة
    """
    import math

    # ✅ Try database BOM first if company_id provided
    if company_id:
        db_result, db_error = get_materials_required_from_db(company_id, product, quantity, preforms_used, packaging_used)
        if db_result is not None:
            print(f"✅ Using database BOM for {product}")
            return db_result, None
        print(f"   DB BOM not found for {product}, falling back to constants")

    from constants import (
        BOM, SHRINK_ROLL_CONVERSION, SHRINK_PALLET_CONFIG,
        LABEL_GLUE_CONSUMPTION_GRAM_PER_BOTTLE,
        CARTON_GLUE_CONSUMPTION_GRAM_PER_CARTON,
        UNITS_PER_CARTON
    )
    
    print(f"🔍 Getting materials for: {product} x{quantity}")
    print(f"   Preforms used (actual): {preforms_used}")
    print(f"   Packaging used (actual): {packaging_used}")
    
    if product not in BOM:
        print(f"   ❌ Product {product} not in BOM")
        return None, f"Product '{product}' not found in BOM"

    # ✅ الحصول على عدد القطع (العبوات) لكل وحدة
    from helpers import get_bom_unit_info
    bom_info = get_bom_unit_info(product)
    pieces_per_unit = bom_info.get("pieces_per_unit", 1)
    
    # ✅ العدد الفعلي للعبوات المنتجة
    actual_bottles = quantity * pieces_per_unit
    print(f"   📊 Actual bottles produced: {actual_bottles:,} (quantity: {quantity:,} × {pieces_per_unit} pcs/unit)")

    required = {}
    
    # ✅ تحديد إذا كان المنتج يحتوي على كرتون (باللغة العربية أو الإنجليزية)
    has_carton = False
    for material in BOM[product].keys():
        if "كرتون" in material or "carton" in material.lower():
            has_carton = True
            break
    
    # ✅ تحديد إذا كان المنتج يحتوي على شرنك
    has_shrink = False
    for material in BOM[product].keys():
        if "شرنك" in material or "shrink" in material.lower():
            has_shrink = True
            break
    
    print(f"   📦 Product contains carton: {has_carton}, contains shrink: {has_shrink}")
    
    for material, qty in BOM[product].items():
        # ==================== البريفورم ====================
        if "بريفورم" in material:
            if preforms_used > 0:
                req_qty = preforms_used
                print(f"   📦 {material}: using actual preforms used = {req_qty:,}")
            else:
                req_qty = qty * quantity
                print(f"   📦 {material}: {qty} x {quantity:,} = {req_qty:,}")

        # ==================== الكرتون ====================
        elif "كرتون" in material or "carton" in material.lower():
            if packaging_used > 0:
                req_qty = packaging_used
                print(f"   📦 {material}: using actual packaging used = {req_qty:,}")
            else:
                req_qty = qty * quantity
                print(f"   📦 {material}: {qty} x {quantity:,} = {req_qty:,}")

        # ==================== الشرنك ====================
        elif "شرنك" in material or "shrink" in material.lower():
            if "فواصل" not in material:
                if packaging_used > 0:
                    rolls_needed = qty * packaging_used
                    print(f"   📦 {material}: {qty} rolls/unit × {packaging_used:,} units = {rolls_needed} rolls required")
                else:
                    rolls_needed = qty * quantity
                    print(f"   📦 {material}: {qty} rolls/unit × {quantity:,} units = {rolls_needed} rolls required")
                
                pieces_per_roll = SHRINK_ROLL_CONVERSION.get(material, 1980)
                req_qty_pieces = rolls_needed * pieces_per_roll
                print(f"   📦 {material}: {rolls_needed} rolls × {pieces_per_roll} pieces/roll = {req_qty_pieces:,.0f} pieces")
                req_qty = rolls_needed
                print(f"   📦 {material}: REQUIRED ROLLS = {req_qty} rolls")
            else:
                # فواصل شرنك
                if packaging_used > 0:
                    actual_units = packaging_used
                else:
                    actual_units = quantity
                
                product_config = SHRINK_PALLET_CONFIG.get(product, {})
                units_per_pallet = product_config.get("units_per_pallet", 1)
                spacers_per_pallet = product_config.get("spacers_per_pallet", 0)
                
                pallets_needed = math.ceil(actual_units / units_per_pallet) if units_per_pallet > 0 else 0
                req_qty = pallets_needed * spacers_per_pallet
                print(f"   📦 {material}: {actual_units:,} units → {pallets_needed} pallets × {spacers_per_pallet} spacers = {req_qty}")

        # ==================== باقي المواد ====================
        else:
            if isinstance(qty, (int, float)):
                if qty < 1:
                    req_qty = quantity * qty
                else:
                    req_qty = qty * quantity
            else:
                req_qty = quantity
            print(f"   📦 {material}: {qty} x {quantity:,} = {req_qty:,}")

        required[material] = req_qty

    # ✅ ✅ ✅ غراء الليبل - يستخدم مع جميع المنتجات
    glue_gram_per_bottle = LABEL_GLUE_CONSUMPTION_GRAM_PER_BOTTLE.get(product, 0.135)
    label_glue_kg = (actual_bottles * glue_gram_per_bottle) / 1000
    required["غراء الليبل"] = label_glue_kg
    print(f"   📦 غراء الليبل: {actual_bottles:,} bottles × {glue_gram_per_bottle}g = {actual_bottles * glue_gram_per_bottle:,.0f}g ({label_glue_kg:.3f} kg)")

    # ✅ ✅ ✅ غراء الكرتون - يستخدم فقط مع المنتجات التي تحتوي على كرتون
    if has_carton:
        if product in CARTON_GLUE_CONSUMPTION_GRAM_PER_CARTON:
            units_per_carton = UNITS_PER_CARTON.get(product, 48)
            cartons_needed = math.ceil(actual_bottles / units_per_carton)
            glue_gram_per_carton = CARTON_GLUE_CONSUMPTION_GRAM_PER_CARTON[product]
            carton_glue_kg = (cartons_needed * glue_gram_per_carton) / 1000
            required["غراء الكرتون"] = carton_glue_kg
            print(f"   📦 غراء الكرتون: {cartons_needed:,} cartons × {glue_gram_per_carton}g = {cartons_needed * glue_gram_per_carton:,.0f}g ({carton_glue_kg:.3f} kg)")
        else:
            print(f"   ⚠️ ملاحظة: المنتج {product} يحتوي على كرتون ولكن لا توجد نسبة استهلاك محددة لغراء الكرتون")
    else:
        print(f"   ℹ️ المنتج {product} لا يحتوي على كرتون (لا يحتاج غراء كرتون)")

    print(f"   ✅ Total materials: {len(required)}")
    return required, None

def calculate_production_metrics(product, units, shift_start, shift_end, break_minutes, speed_bottles_per_hour, preforms_used=0, packaging_used=0.0, company_id=None):
    """حساب مقاييس الإنتاج"""
    bom = get_bom_unit_info(product, company_id=company_id)
    pieces_per_unit = max(1, bom["pieces_per_unit"])
    units = int(units)

    good_bottles = units * pieces_per_unit
    final_preforms = int(preforms_used) if int(preforms_used) > 0 else good_bottles
    waste_bottles = max(0, final_preforms - good_bottles)

    try:
        start_total = shift_start.hour * 60 + shift_start.minute
        end_total = shift_end.hour * 60 + shift_end.minute
        if end_total <= start_total:
            end_total += 24 * 60

        shift_minutes = end_total - start_total
        working_minutes = max(0, shift_minutes - int(break_minutes))
        working_hours = working_minutes / 60.0

        theoretical_bottles = speed_bottles_per_hour * working_hours if working_hours > 0 else 0

        if theoretical_bottles > 0:
            efficiency = min(100.0, round((final_preforms / theoretical_bottles) * 100, 1))
        else:
            efficiency = 0.0

        if speed_bottles_per_hour > 0:
            required_hours = final_preforms / speed_bottles_per_hour
            downtime_hours = max(0.0, working_hours - required_hours)
        else:
            downtime_hours = 0.0

        downtime_minutes = int(round(downtime_hours * 60))

        expected_packaging = units
        if int(packaging_used) > 0:
            final_packaging = int(packaging_used)
            packaging_waste = max(0, final_packaging - expected_packaging)
        else:
            final_packaging = expected_packaging
            packaging_waste = 0

        return {
            "pieces_per_unit": pieces_per_unit,
            "good_bottles": good_bottles,
            "bottles_produced": good_bottles,
            "final_preforms": final_preforms,
            "waste_bottles": waste_bottles,
            "working_minutes": working_minutes,
            "working_hours": round(working_hours, 2),
            "downtime_minutes": downtime_minutes,
            "downtime_hours": round(downtime_hours, 2),
            "theoretical_bottles": int(theoretical_bottles),
            "efficiency": efficiency,
            "packaging_waste": packaging_waste,
            "final_packaging": float(final_packaging),
            "line_speed": int(speed_bottles_per_hour),
            "ideal_run_rate": speed_bottles_per_hour / 60.0,
        }
    except Exception:
        return {
            "pieces_per_unit": pieces_per_unit,
            "good_bottles": good_bottles,
            "bottles_produced": good_bottles,
            "final_preforms": final_preforms,
            "waste_bottles": waste_bottles,
            "working_minutes": 0,
            "working_hours": 0.0,
            "downtime_minutes": 0,
            "downtime_hours": 0.0,
            "theoretical_bottles": 0,
            "efficiency": 0.0,
            "packaging_waste": 0,
            "final_packaging": float(units),
            "line_speed": int(speed_bottles_per_hour),
            "ideal_run_rate": speed_bottles_per_hour / 60.0,
        }


def get_shift_info():
    """الحصول على معلومات الوردية الحالية - نسخة مبسطة"""
    from datetime import datetime, timedelta
    
    now = datetime.now()
    current_hour = now.hour
    current_minute = now.minute
    
    is_working = True
    current_break = None
    
    if current_hour == 10 and current_minute < 30:
        is_working = False
        current_break = {"start": "10:00", "end": "10:30", "duration": 0.5}
    elif current_hour == 13 or (current_hour == 14 and current_minute == 0):
        is_working = False
        current_break = {"start": "13:00", "end": "14:00", "duration": 1.0}
    elif current_hour == 18 and current_minute < 30:
        is_working = False
        current_break = {"start": "18:00", "end": "18:30", "duration": 0.5}
    elif current_hour == 23 or (current_hour == 0 and current_minute < 30):
        is_working = False
        current_break = {"start": "23:00", "end": "00:30", "duration": 1.0}
    
    try:
        import streamlit as st
        current_lang = st.session_state.get('lang', 'ar')
    except:
        current_lang = 'ar'
    
    if current_lang == 'en':
        shift_name = "Single Shift (8:00 AM - 2:00 AM)"
    else:
        shift_name = "الوردية الواحدة (8 صباحاً - 2 صباحاً)"
    
    return {
        "shift_start": now.replace(hour=8, minute=0, second=0, microsecond=0),
        "shift_end": (now + timedelta(days=1)).replace(hour=2, minute=0, second=0, microsecond=0),
        "shift_duration_hours": 18,
        "break_times": [],
        "is_working": is_working,
        "current_break": current_break,
        "total_break_hours": 3,
        "working_hours": 15,
        "shift_name": shift_name
    }


def get_production_record_labels(t):
    """الحصول على تسميات أعمدة سجلات الإنتاج"""
    return {
        "id": t.get("col_id", "ID"),
        "date": t.get("col_date", "Date"),
        "line": t.get("col_line", "Line"),
        "product": t.get("col_product", "Product"),
        "output_units": t.get("col_qty_units", "Qty (units)"),
        "waste_bottles": t.get("col_waste_bottles", "Bottle Waste"),
        "packaging_waste": t.get("col_packaging_waste", "Packaging Waste"),
        "line_speed": t.get("col_line_speed_bottles", "Line speed (bottles/hr)"),
        "preforms_used": t.get("preform_actual", "Preforms used"),
        "efficiency": t.get("col_efficiency", "Efficiency %"),
        "downtime_hours": t.get("col_downtime", "Downtime (hrs)"),
        "operating_hours": t.get("col_operating_time", "Operating (hrs)"),
        "supervisor": t.get("col_supervisor", "Supervisor"),
        "oee": t.get("col_oee", "OEE %"),
    }


def load_language(lang_code='ar'):
    """تحميل الترجمة"""
    from constants import LANG
    return LANG.get(lang_code, LANG['ar'])


def get_machine_map(lang_code='ar', factory_id=None):
    """الحصول على خريطة الماكينات (مع دعم تعدد المصانع)"""
    import os
    from constants import MACHINE_LABELS, MACHINE_FILES
    
    labels = MACHINE_LABELS.get(lang_code, MACHINE_LABELS['ar'])
    
    if factory_id:
        from database import db_manager, Factory
        session = db_manager.get_session()
        try:
            factory = session.query(Factory).filter(Factory.id == factory_id).first()
            if factory:
                factory_dir = f"machines/{factory.code}"
                os.makedirs(factory_dir, exist_ok=True)
                factory_files = []
                for f in MACHINE_FILES:
                    factory_path = os.path.join(factory_dir, f)
                    if os.path.exists(factory_path) and not _is_excel_empty(factory_path):
                        factory_files.append(factory_path)
                    else:
                        # الرجوع للملف الرئيسي إذا كان ملف المصنع فارغاً أو غير موجود
                        factory_files.append(f)
                return dict(zip(labels, factory_files))
        except:
            pass
        finally:
            session.close()
    
    return dict(zip(labels, MACHINE_FILES))


def _is_excel_empty(filepath):
    """التحقق من أن ملف Excel لا يحتوي على بيانات (بعد رؤوس الأعمدة)"""
    import pandas as pd
    try:
        df = pd.read_excel(filepath, skiprows=2)
        cleaned = df.dropna(how='all')
        return cleaned.empty
    except:
        return True


# helpers.py - استبدل دالة send_telegram بهذه النسخة

def send_telegram(msg):
    """إرسال إشعار تلجرام"""
    try:
        import streamlit as st
        import requests
        import logging
        
        # ✅ استخدام التوكن الذي أعطيته مباشرة (للتجربة)
        token = "8606698058:AAHPTrzp8xCdXkx956aP5W-uH0Z_4daC0Ks"
        chat_id = "7911811172"
        
        # محاولة الحصول من secrets أولاً (إذا كان موجوداً)
        try:
            if hasattr(st, 'secrets'):
                telegram_config = st.secrets.get("telegram", {})
                if telegram_config.get("bot_token"):
                    token = telegram_config.get("bot_token")
                if telegram_config.get("chat_id"):
                    chat_id = telegram_config.get("chat_id")
        except:
            pass
        
        if not token or not chat_id:
            print("⚠️ Telegram: Missing token or chat_id")
            return False
        
        # إرسال الرسالة
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": msg,
            "parse_mode": "HTML"
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Telegram sent: {msg[:50]}...")
            return True
        else:
            print(f"❌ Telegram error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Telegram exception: {e}")
        return False


def create_machine_file(filepath):
    """إنشاء ملف صيانة جديد"""
    if "Compressor" in filepath or "AF_Compressor" in filepath:
        sample_data = pd.DataFrame({
            "Cat": ["Daily checks", "Operation check"],
            "No": [1, 1],
            "Name": ["Fill weekly performance log", "Check emergency stop button"],
            "Photo": ["", ""],
            "Tools": ["Pen", "Manual"],
            "Proc": ["Record data", "Manual test"],
            "Freq": ["Daily", "Daily"],
            "Stat": ["Active"] * 2,
            "Note": ["", ""],
            "Staff": ["", ""],
        })
        sample_data.to_excel(filepath, index=False)
    else:
        sample = pd.DataFrame({
            "Cat": ["Mechanical", "Electrical"],
            "No": [1, 2],
            "Name": ["Check bearings", "Calibrate sensors"],
            "Photo": ["", ""],
            "Tools": ["Wrench", "Calibration device"],
            "Proc": ["Check vibrations", "Calibrate per manual"],
            "Freq": ["Daily", "Weekly"],
            "Stat": ["Active"] * 2,
            "Note": ["", ""],
            "Staff": ["", ""],
        })
        sample.to_excel(filepath, index=False)


def find_image_path(photo_name, factory_id=None):
    """البحث عن مسار الصورة (مع دعم تعدد المصانع)"""
    if not photo_name or pd.isna(photo_name) or str(photo_name).strip() == "":
        return None
    import os
    possible = [
        photo_name,
        os.path.join("images", photo_name),
        os.path.join("images", os.path.basename(str(photo_name)))
    ]
    if factory_id:
        from database import db_manager, Factory
        session = db_manager.get_session()
        try:
            factory = session.query(Factory).filter(Factory.id == factory_id).first()
            if factory:
                possible.insert(0, os.path.join("images", factory.code, photo_name))
        except:
            pass
        finally:
            session.close()
    for path in possible:
        if os.path.exists(path):
            return path
    return None


def get_scheduled_tasks(df_tasks):
    """الحصول على المهام المجدولة"""
    if df_tasks is None or df_tasks.empty:
        return pd.DataFrame()

    today = datetime.now()
    day_name = today.strftime('%A')
    is_first_month = (today.day == 1)

    freq_col = next((c for c in ['Freq', 'Frequency'] if c in df_tasks.columns), None)
    if freq_col is None:
        return pd.DataFrame()

    if day_name == 'Friday':
        return pd.DataFrame()

    allowed = ['Daily']
    if day_name == 'Saturday':
        allowed.append('Weekly')
    if is_first_month:
        allowed += ['Monthly', '1000h', 'Yearly']

    df = df_tasks.copy()
    df[freq_col] = df[freq_col].astype(str).replace('4 months', 'Monthly')
    result = df[df[freq_col].isin(allowed)]
    return result.reset_index(drop=True)


# ============================================================================
# Internal helpers
# ============================================================================

def _normalize(name: str) -> str:
    """تطبيع الأسماء"""
    import re
    return re.sub(r'\s+', ' ', str(name).strip())


def _get_material_col(df: pd.DataFrame):
    """الحصول على عمود اسم المادة"""
    for col in ["Material_Name_AR", "Material_Name_EN", "Material_Name", "Name", "المادة", "material"]:
        if col in df.columns:
            return col
    return None


def _get_stock_col(df: pd.DataFrame):
    """الحصول على عمود الكمية"""
    for col in ["Current_Stock", "Stock", "الكمية", "quantity", "in_stock"]:
        if col in df.columns:
            return col
    return None


def get_factory_products(factory_id, line_name=None, lang='ar'):
    """الحصول على منتجات المصنع من قاعدة البيانات (للإنتاج)"""
    from database import db_manager, Product, ProductLineSpeed, ProductionLine
    import streamlit as st

    session = db_manager.get_session()
    try:
        # Try to get products from database
        if line_name:
            line = session.query(ProductionLine).filter(
                ProductionLine.company_id == factory_id,
                ProductionLine.code == line_name
            ).first()
            if line:
                speeds = session.query(ProductLineSpeed).filter(
                    ProductLineSpeed.company_id == factory_id,
                    ProductLineSpeed.production_line_id == line.id
                ).all()
                if speeds:
                    product_ids = [s.product_id for s in speeds]
                    products = session.query(Product).filter(
                        Product.id.in_(product_ids),
                        Product.company_id == factory_id,
                        Product.is_active == True
                    ).all()
                    if products:
                        return [p.name_en if lang == 'en' else p.name_ar for p in products]

        # Fall back: get all products for this factory
        products = session.query(Product).filter(
            Product.company_id == factory_id,
            Product.is_active == True
        ).all()
        if products:
            return [p.name_en if lang == 'en' else p.name_ar for p in products]

        return None
    except Exception as e:
        print(f"get_factory_products error: {e}")
        return None
    finally:
        session.close()


def get_effective_config(factory_id=None, line_name=None):
    """الحصول على الإعدادات الفعلية (دمج إعدادات المصنع مع الإعدادات العامة)"""
    from constants import CONFIG
    from database import db_manager
    
    result = {}
    if factory_id:
        db_config = db_manager.get_factory_config(factory_id, line_name)
    else:
        db_config = {}
    
    for line, cfg in CONFIG.items():
        if line_name and line != line_name:
            continue
        line_cfg = {
            "products": list(cfg.get("products", [])),
            "speed": dict(cfg.get("speed", {})),
            "pack_per_unit": dict(cfg.get("pack_per_unit", {})),
        }
        if db_config and line == line_name:
            if 'product' in db_config:
                for p in db_config['product']:
                    if p not in line_cfg['products']:
                        line_cfg['products'].append(p)
            if 'speed' in db_config:
                line_cfg['speed'].update(db_config['speed'])
            if 'pack_per_unit' in db_config:
                line_cfg['pack_per_unit'].update(db_config['pack_per_unit'])
        result[line] = line_cfg
    
    if line_name and line_name in result:
        return result[line_name]
    return result if not line_name else result.get(line_name, {})