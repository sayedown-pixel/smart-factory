# database.py - النسخة الكاملة والمستقرة

import os
import logging
import bcrypt
from datetime import datetime, timedelta, date
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, Index, text, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from dotenv import load_dotenv
import pandas as pd

# تحميل متغيرات البيئة
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

SQLITE_DB_PATH = "birma_data.db"


# ============================================================================
# Database Models
# ============================================================================

class Factory(Base):
    """نموذج المصنع - للنسخة متعددة المصانع (Multi-Tenant)"""
    __tablename__ = 'factories'

    id = Column(Integer, primary_key=True)
    name_ar = Column(String(200), nullable=False)
    name_en = Column(String(200), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    subdomain = Column(String(100), unique=True, nullable=True)
    logo_url = Column(String(500), nullable=True)
    timezone = Column(String(50), default='Asia/Riyadh')
    subscription_plan = Column(String(50), default='basic')
    subscription_start = Column(DateTime, nullable=True)
    subscription_end = Column(DateTime, nullable=True)
    status = Column(String(20), default='pending')
    max_users = Column(Integer, default=5)
    storage_limit_mb = Column(Integer, default=1024)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        Index('idx_factory_code', 'code'),
        Index('idx_factory_status', 'status'),
        Index('idx_factory_subdomain', 'subdomain'),
    )


# database.py - تحديث نموذج User

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    icon = Column(String(10), default="👤")
    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)
    must_change_password = Column(Boolean, default=False)
    last_password_change = Column(DateTime, default=datetime.now)
    
    # Multi-Tenant columns
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=True)  # تغيير من factory_id إلى company_id
    is_super_admin = Column(Boolean, default=False)
    email = Column(String(200), unique=True, nullable=True)
    email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String(255), nullable=True)
    reset_password_token = Column(String(255), nullable=True)
    reset_password_expires = Column(DateTime, nullable=True)
    failed_attempts = Column(Integer, default=0)
    
    company = relationship("Company", backref="users")
    
    __table_args__ = (
        Index('idx_user_username', 'username'),
        Index('idx_user_company_id', 'company_id'),
        Index('idx_user_email', 'email'),
    )

class Alert(Base):
    """نموذج التنبيهات"""
    __tablename__ = 'alerts'

    id = Column(Integer, primary_key=True)
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), default='warning')
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    related_id = Column(Integer, nullable=True)
    related_name = Column(String(200), nullable=True)
    is_read = Column(Boolean, default=False)
    is_dismissed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    dismissed_at = Column(DateTime, nullable=True)
    dismissed_by = Column(String(100), nullable=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=True, index=True)
    factory_id = Column(Integer, nullable=True)
    
    __table_args__ = (
        Index('idx_alert_type', 'alert_type'),
        Index('idx_alert_is_read', 'is_read'),
        Index('idx_alert_created_at', 'created_at'),
        Index('idx_alert_factory_id', 'factory_id'),
    )


class Production(Base):
    __tablename__ = 'production'

    id = Column(Integer, primary_key=True)
    type = Column(String(50), default='Production')
    date = Column(DateTime, nullable=False)
    line = Column(String(100), nullable=False)
    supervisor = Column(String(100))
    product = Column(String(100), nullable=False)
    output_units = Column(Integer, nullable=False)
    preforms_used = Column(Integer, default=0)
    waste_bottles = Column(Integer, default=0)
    packaging_waste = Column(Float, default=0)
    line_speed = Column(Integer, default=0)
    efficiency = Column(Float, default=0)
    oee = Column(Float, default=0)
    availability = Column(Float, default=0)
    performance = Column(Float, default=0)
    quality = Column(Float, default=0)
    planned_production_time = Column(Integer, default=0)
    operating_time = Column(Integer, default=0)
    downtime_minutes = Column(Integer, default=0)
    ideal_run_rate = Column(Float, default=0)
    shift = Column(String(500))
    timestamp = Column(DateTime, default=datetime.now)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=True, index=True)
    factory_id = Column(Integer, nullable=True)
    
    __table_args__ = (
        Index('idx_production_date', 'date'),
        Index('idx_production_line', 'line'),
    )


class Maintenance(Base):
    __tablename__ = 'maintenance'

    id = Column(Integer, primary_key=True)
    type = Column(String(50))
    date = Column(DateTime, nullable=False)
    line = Column(String(100))
    machine = Column(String(100))
    technician = Column(String(100))
    issue = Column(Text)
    task = Column(String(200))
    start_time = Column(String(20), nullable=True)
    end_time = Column(String(20), nullable=True)
    downtime_minutes = Column(Integer, default=0)
    downtime_category = Column(String(50))
    spare_parts = Column(Text)
    notes = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=True, index=True)
    factory_id = Column(Integer, nullable=True)
    
    __table_args__ = (
        Index('idx_maintenance_date', 'date'),
        Index('idx_maintenance_machine', 'machine'),
    )


class Delivery(Base):
    __tablename__ = 'delivery'

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    product = Column(String(100))
    quantity = Column(Integer)
    customer = Column(String(200))
    delivery_note = Column(String(100))
    notes = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=True, index=True)
    factory_id = Column(Integer, nullable=True)


class RawReceipt(Base):
    __tablename__ = 'raw_receipt'

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    material = Column(String(100))
    quantity = Column(Integer)
    invoice = Column(String(100))
    notes = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=True, index=True)
    factory_id = Column(Integer, nullable=True)


class DowntimeRecord(Base):
    __tablename__ = 'downtime_records'

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    line = Column(String(100), nullable=False)
    machine = Column(String(100))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    duration_minutes = Column(Integer, default=0)
    category = Column(String(50))
    sub_category = Column(String(100))
    description = Column(Text)
    reported_by = Column(String(100))
    shift = Column(String(20))
    is_resolved = Column(Boolean, default=False)
    resolution_notes = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=True, index=True)
    factory_id = Column(Integer, nullable=True)
    
    __table_args__ = (
        Index('idx_downtime_date', 'date'),
        Index('idx_downtime_line', 'line'),
        Index('idx_downtime_category', 'category'),
    )


class OEESummary(Base):
    __tablename__ = 'oee_summary'

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    line = Column(String(100), nullable=False)
    shift = Column(String(20))
    oee = Column(Float)
    availability = Column(Float)
    performance = Column(Float)
    quality = Column(Float)
    total_downtime_minutes = Column(Integer)
    total_units_produced = Column(Integer)
    total_good_units = Column(Integer)
    total_defect_units = Column(Integer)
    planned_production_time = Column(Integer)
    operating_time = Column(Integer)
    timestamp = Column(DateTime, default=datetime.now)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=True, index=True)
    factory_id = Column(Integer, nullable=True)
    
    __table_args__ = (
        Index('idx_oee_date', 'date'),
        Index('idx_oee_line', 'line'),
    )


class RawMaterial(Base):
    __tablename__ = 'raw_materials'

    id = Column(Integer, primary_key=True)
    material_id = Column(String(50), nullable=True)
    name_ar = Column(String(200), nullable=False)
    name_en = Column(String(200), nullable=False)
    current_stock = Column(Float, default=0)
    min_stock = Column(Float, default=0)
    max_stock = Column(Float, default=0)
    unit = Column(String(50), default="قطعة")
    unit_cost = Column(Float, default=0)
    daily_consumption = Column(Float, default=0)
    last_updated = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=True, index=True)
    factory_id = Column(Integer, nullable=True)
    
    __table_args__ = (
        Index('idx_raw_material_id', 'material_id'),
        Index('idx_raw_name_ar', 'name_ar'),
        Index('idx_raw_name_en', 'name_en'),
        Index('idx_raw_factory_id', 'factory_id'),
        UniqueConstraint('material_id', 'factory_id', name='uq_raw_material_id_factory'),
    )


class FinishedGood(Base):
    __tablename__ = 'finished_goods'

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    opening_balance = Column(Float, default=0)
    stock_in = Column(Float, default=0)
    stock_out = Column(Float, default=0)
    balance = Column(Float, default=0)
    unit = Column(String(50), default="قطعة")
    month_key = Column(String(10), default="")
    last_updated = Column(DateTime, default=datetime.now)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=True, index=True)
    factory_id = Column(Integer, nullable=True)
    
    __table_args__ = (
        Index('idx_fg_name', 'name'),
        Index('idx_fg_month_key', 'month_key'),
        Index('idx_fg_factory_id', 'factory_id'),
        UniqueConstraint('name', 'factory_id', name='uq_fg_name_factory'),
    )
class FactoryEmail(Base):
    """إيميلات المسئولين للمصنع (للإرسال الأسبوعي)"""
    __tablename__ = 'factory_emails'

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    email = Column(String(200), nullable=False)
    name = Column(String(100), nullable=True)
    role = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    
    company = relationship("Company", backref="notification_emails")
    
    __table_args__ = (
        Index('idx_fe_company', 'company_id'),
        UniqueConstraint('company_id', 'email', name='uq_fe_email_per_company'),
    )


class ProductBOMDetail(Base):
    """تفاصيل BOM الكاملة للمنتج (عدد بريفورم, غطاء, ليبل, كرتون/شرنك, غراء)"""
    __tablename__ = 'product_bom_details'

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    
    # المكونات الأساسية (مراجع للمواد الخام)
    preform_material_id = Column(Integer, ForeignKey('materials.id'), nullable=True)
    cap_material_id = Column(Integer, ForeignKey('materials.id'), nullable=True)
    label_material_id = Column(Integer, ForeignKey('materials.id'), nullable=True)
    
    # كميات المكونات الأساسية
    preforms_per_unit = Column(Integer, default=1)
    caps_per_unit = Column(Integer, default=1)
    labels_per_unit = Column(Integer, default=1)
    
    # التعبئة
    packaging_type = Column(String(50), default='carton')  # 'carton' or 'shrink'
    units_per_carton = Column(Integer, default=48)
    units_per_shrink = Column(Integer, default=20)
    
    # مواد التعبئة
    carton_material_id = Column(Integer, ForeignKey('materials.id'), nullable=True)
    shrink_material_id = Column(Integer, ForeignKey('materials.id'), nullable=True)
    
    # للشرنك: عدد القطع في الرول (للتحويل من قطعة إلى رول)
    shrink_pieces_per_roll = Column(Integer, default=1980)
    
    # فواصل الشرنك (للكرتون أو الشرنك)
    shrink_divider_material_id = Column(Integer, ForeignKey('materials.id'), nullable=True)
    shrink_dividers_per_pallet = Column(Integer, nullable=True)  # عدد الفواصل لكل باليت
    
    # الغراء
    label_glue_material_id = Column(Integer, ForeignKey('materials.id'), nullable=True)
    label_glue_grams_per_bottle = Column(Float, default=0.135)
    
    carton_glue_material_id = Column(Integer, ForeignKey('materials.id'), nullable=True)
    carton_glue_grams_per_carton = Column(Float, default=0.5)
    
    # الاسترتش فيلم (مادة عامة تستخدم مع كل الأنواع)
    shrink_film_material_id = Column(Integer, ForeignKey('materials.id'), nullable=True)
    shrink_film_grams_per_pallet = Column(Float, nullable=True)  # وزن الاسترتش فيلم لكل باليت (جم)
    units_per_pallet = Column(Integer, nullable=True)  # عدد الوحدات في الباليت
    
    # الحد الأدنى
    min_stock_units = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    company = relationship("Company", backref="bom_details")
    product = relationship("Product", backref="bom_details")
    
    # Relationships for materials
    preform_material = relationship("Material", foreign_keys=[preform_material_id])
    cap_material = relationship("Material", foreign_keys=[cap_material_id])
    label_material = relationship("Material", foreign_keys=[label_material_id])
    carton_material = relationship("Material", foreign_keys=[carton_material_id])
    shrink_material = relationship("Material", foreign_keys=[shrink_material_id])
    shrink_divider_material = relationship("Material", foreign_keys=[shrink_divider_material_id])
    label_glue_material = relationship("Material", foreign_keys=[label_glue_material_id])
    carton_glue_material = relationship("Material", foreign_keys=[carton_glue_material_id])
    shrink_film_material = relationship("Material", foreign_keys=[shrink_film_material_id])
    
    __table_args__ = (
        UniqueConstraint('company_id', 'product_id', name='uq_bom_detail_per_company'),
        Index('idx_bd_company', 'company_id'),
        Index('idx_bd_product', 'product_id'),
    )


# database.py - أضف هذه النماذج الجديدة بعد نموذج FinishedGood

class Company(Base):
    """نموذج الشركة/المصنع - Multi-Tenant"""
    __tablename__ = 'companies'

    id = Column(Integer, primary_key=True)
    name_ar = Column(String(200), nullable=False)
    name_en = Column(String(200), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    subdomain = Column(String(100), unique=True, nullable=True)
    logo_url = Column(String(500), nullable=True)
    timezone = Column(String(50), default='Asia/Riyadh')
    subscription_plan = Column(String(50), default='basic')
    subscription_start = Column(DateTime, nullable=True)
    subscription_end = Column(DateTime, nullable=True)
    status = Column(String(20), default='pending')
    max_users = Column(Integer, default=10)
    storage_limit_mb = Column(Integer, default=1024)
    address_ar = Column(String(500), nullable=True)
    address_en = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(200), nullable=True)
    tax_number = Column(String(100), nullable=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        Index('idx_company_code', 'code'),
        Index('idx_company_status', 'status'),
        Index('idx_company_subdomain', 'subdomain'),
    )


class ProductionLine(Base):
    """نموذج خطوط الإنتاج"""
    __tablename__ = 'production_lines'

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    name_ar = Column(String(100), nullable=False)
    name_en = Column(String(100), nullable=False)
    code = Column(String(50), nullable=False)
    status = Column(String(20), default='active')
    shift_start = Column(String(10), default='08:00')
    shift_end = Column(String(10), default='02:00')
    break_minutes = Column(Integer, default=180)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    company = relationship("Company", backref="production_lines")
    
    __table_args__ = (
        UniqueConstraint('company_id', 'code', name='uq_line_code_per_company'),
        Index('idx_line_company', 'company_id'),
        Index('idx_line_status', 'status'),
    )


class Product(Base):
    """نموذج المنتجات"""
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    name_ar = Column(String(200), nullable=False)
    name_en = Column(String(200), nullable=False)
    code = Column(String(50), nullable=False)
    category = Column(String(100), nullable=True)
    unit = Column(String(50), default='كرتون')
    pieces_per_unit = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    company = relationship("Company", backref="products")
    
    __table_args__ = (
        UniqueConstraint('company_id', 'code', name='uq_product_code_per_company'),
        Index('idx_product_company', 'company_id'),
    )


class Material(Base):
    """نموذج المواد الخام"""
    __tablename__ = 'materials'

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    name_ar = Column(String(200), nullable=False)
    name_en = Column(String(200), nullable=False)
    code = Column(String(50), nullable=False)
    category = Column(String(100), nullable=True)
    unit = Column(String(50), default='قطعة')
    unit_cost = Column(Float, default=0)
    min_stock = Column(Float, default=0)
    max_stock = Column(Float, default=0)
    current_stock = Column(Float, default=0)
    daily_consumption = Column(Float, default=0)
    is_active = Column(Boolean, default=True)
    
    # المقاس: '200ml', '330ml', '500ml', '600ml', '1L', '1.5L', 'general'
    size = Column(String(50), nullable=True)
    
    # للشرنك: عدد القطع في الرول (يستخدم في التحويل من قطعة إلى رول)
    pieces_per_roll = Column(Integer, nullable=True)
    
    # عدد الوحدات في الباليت (لحساب استهلاك الاسترتش فيلم)
    units_per_pallet = Column(Integer, nullable=True)
    
    # للبريفورم/الليبل/الغطاء: عدد القطع في الوحدة (كرتون أو شرنك)
    pieces_per_unit = Column(Integer, nullable=True)
    
    # للفواصل: عدد الفواصل في الباليت
    dividers_per_pallet = Column(Integer, nullable=True)
    
    # للاسترتش فيلم: وزن الاسترتش بالجم في الباليت
    shrink_film_grams_per_pallet = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    company = relationship("Company", backref="materials")
    
    __table_args__ = (
        UniqueConstraint('company_id', 'code', name='uq_material_code_per_company'),
        Index('idx_material_company', 'company_id'),
        Index('idx_material_size', 'size'),
    )


class ProductBOM(Base):
    """نموذج مكونات المنتج (Bill of Materials)"""
    __tablename__ = 'product_bom'

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(50), default='قطعة')
    is_critical = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    company = relationship("Company", backref="bom_items")
    product = relationship("Product", backref="bom_items")
    material = relationship("Material", backref="bom_items")
    
    __table_args__ = (
        UniqueConstraint('company_id', 'product_id', 'material_id', name='uq_bom_item'),
        Index('idx_bom_product', 'product_id'),
        Index('idx_bom_material', 'material_id'),
    )


class ProductLineSpeed(Base):
    """نموذج سرعات خطوط الإنتاج للمنتجات"""
    __tablename__ = 'product_line_speed'

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    production_line_id = Column(Integer, ForeignKey('production_lines.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    speed_bottles_per_hour = Column(Integer, default=0)
    target_output_per_shift = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    company = relationship("Company", backref="product_line_speeds")
    production_line = relationship("ProductionLine", backref="product_speeds")
    product = relationship("Product", backref="line_speeds")
    
    __table_args__ = (
        UniqueConstraint('company_id', 'production_line_id', 'product_id', name='uq_line_product_speed'),
        Index('idx_speed_line', 'production_line_id'),
        Index('idx_speed_product', 'product_id'),
    )


class Shift(Base):
    """نموذج الورديات"""
    __tablename__ = 'shifts'

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    name_ar = Column(String(100), nullable=False)
    name_en = Column(String(100), nullable=False)
    start_time = Column(String(10), nullable=False)
    end_time = Column(String(10), nullable=False)
    break_start = Column(String(10), nullable=True)
    break_end = Column(String(10), nullable=True)
    break_duration_minutes = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    company = relationship("Company", backref="shifts")
    
    __table_args__ = (
        Index('idx_shift_company', 'company_id'),
    )


class InventoryTransaction(Base):
    """نموذج حركات المخزون الموحد"""
    __tablename__ = 'inventory_transactions'

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    transaction_type = Column(String(20), nullable=False)
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=True)
    quantity = Column(Float, nullable=False)
    reference = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    company = relationship("Company", backref="inventory_transactions")
    material = relationship("Material", backref="transactions")
    product = relationship("Product", backref="transactions")
    
    __table_args__ = (
        Index('idx_inv_transaction_type', 'transaction_type'),
        Index('idx_inv_material', 'material_id'),
        Index('idx_inv_product', 'product_id'),
        Index('idx_inv_created_at', 'created_at'),
    )


class MaintenanceLog(Base):
    """نموذج سجلات الصيانة"""
    __tablename__ = 'maintenance_logs'

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    production_line_id = Column(Integer, ForeignKey('production_lines.id'), nullable=True)
    machine = Column(String(100), nullable=False)
    maintenance_type = Column(String(50), nullable=False)
    technician = Column(String(100), nullable=False)
    issue = Column(Text, nullable=True)
    task = Column(String(200), nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    downtime_minutes = Column(Integer, default=0)
    downtime_category = Column(String(50), nullable=True)
    spare_parts = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    company = relationship("Company", backref="maintenance_logs")
    production_line = relationship("ProductionLine", backref="maintenance_logs")
    
    __table_args__ = (
        Index('idx_maint_company', 'company_id'),
        Index('idx_maint_line', 'production_line_id'),
        Index('idx_maint_machine', 'machine'),
        Index('idx_maint_date', 'created_at'),
    )    


class RawMaterialTransaction(Base):
    __tablename__ = 'raw_material_transactions'

    id = Column(Integer, primary_key=True)
    material_id = Column(Integer, ForeignKey('raw_materials.id'), nullable=False)
    transaction_type = Column(String(20), nullable=False)
    quantity = Column(Float, nullable=False)
    reference = Column(String(100))
    notes = Column(Text)
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.now)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=True, index=True)
    factory_id = Column(Integer, nullable=True)
    
    __table_args__ = (
        Index('idx_transaction_material', 'material_id'),
        Index('idx_transaction_type', 'transaction_type'),
        Index('idx_transaction_date', 'created_at'),
        Index('idx_transaction_factory_id', 'factory_id'),
    )


class FinishedGoodTransaction(Base):
    __tablename__ = 'finished_good_transactions'

    id = Column(Integer, primary_key=True)
    finished_good_id = Column(Integer, ForeignKey('finished_goods.id'), nullable=False)
    transaction_type = Column(String(20), nullable=False)
    quantity = Column(Float, nullable=False)
    reference = Column(String(100))
    customer = Column(String(200))
    notes = Column(Text)
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.now)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=True, index=True)
    factory_id = Column(Integer, nullable=True)
    
    __table_args__ = (
        Index('idx_fg_transaction_fg', 'finished_good_id'),
        Index('idx_fg_transaction_type', 'transaction_type'),
        Index('idx_fg_transaction_date', 'created_at'),
        Index('idx_fg_transaction_factory_id', 'factory_id'),
    )


class SystemLog(Base):
    __tablename__ = 'system_logs'

    id = Column(Integer, primary_key=True)
    event_type = Column(String(50), nullable=False)
    event_level = Column(String(20), default='INFO')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    username = Column(String(100), nullable=True)
    action = Column(String(500), nullable=False)
    details = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=True, index=True)
    factory_id = Column(Integer, nullable=True)
    
    __table_args__ = (
        Index('idx_log_event_type', 'event_type'),
        Index('idx_log_user_id', 'user_id'),
        Index('idx_log_created_at', 'created_at'),
        Index('idx_log_event_level', 'event_level'),
        Index('idx_log_factory_id', 'factory_id'),
    )


class FactoryConfig(Base):
    """إعدادات المصنع (المنتجات، السرعات، BOM) - لكل مصنع"""
    __tablename__ = 'factory_config'

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=True, index=True)
    factory_id = Column(Integer, nullable=False)
    line_name = Column(String(100), nullable=True)
    config_type = Column(String(50), nullable=False)  # 'product', 'speed', 'pack_per_unit', 'bom'
    config_key = Column(String(200), nullable=False)  # product name or line name
    config_value = Column(Text, nullable=False)       # JSON value
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index('idx_fc_factory_line', 'factory_id', 'line_name'),
        UniqueConstraint('factory_id', 'line_name', 'config_type', 'config_key', name='uq_fc_key'),
    )


# ============================================================================
# Database Manager
# ============================================================================

class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._connected = False
        self._init_error = None
        self._use_sqlite = False
        self._init_connection()

    def _init_connection(self):
        DATABASE_URL = ""

        try:
            import streamlit as st
            if "DATABASE_URL" in st.secrets:
                val = st.secrets["DATABASE_URL"]
                if isinstance(val, str) and val.strip():
                    DATABASE_URL = val.strip()
                    logger.info("✅ DATABASE_URL loaded from st.secrets")
            if not DATABASE_URL and "database" in st.secrets:
                sec = st.secrets["database"]
                if isinstance(sec, str) and sec.strip():
                    DATABASE_URL = sec.strip()
                elif hasattr(sec, "get"):
                    for k in ("url", "DATABASE_URL", "connection_string", "postgres_url"):
                        v = sec.get(k, "")
                        if isinstance(v, str) and v.strip():
                            DATABASE_URL = v.strip()
                            break
        except Exception as e:
            logger.warning(f"Could not read st.secrets: {e}")

        if not DATABASE_URL:
            DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
            if DATABASE_URL:
                logger.info("✅ DATABASE_URL loaded from environment variable")

        if DATABASE_URL:
            db_url = DATABASE_URL
            if db_url.startswith("postgresql://") and "+psycopg2" not in db_url:
                db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
            elif db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)

            try:
                self.engine = create_engine(
                    db_url,
                    echo=False,
                    pool_pre_ping=True,
                    pool_size=5,
                    max_overflow=10,
                    connect_args={"connect_timeout": 10},
                )
                with self.engine.connect() as conn:
                    result = conn.execute(text("SELECT version()"))
                    version = result.fetchone()
                    logger.info(f"PostgreSQL connected: {version[0][:60]}...")

                self.SessionLocal = sessionmaker(
                    autocommit=False, autoflush=False, bind=self.engine
                )
                Base.metadata.create_all(bind=self.engine)
                self._migrate_schema()
                self._connected = True
                self._use_sqlite = False
                self._create_default_admin()
                self._create_default_factory()
                self._fix_missing_data()
                logger.info("✅ Database initialized with PostgreSQL")
                return
            except Exception as e:
                logger.error(f"❌ PostgreSQL connection failed: {e}")
                self._init_error = str(e)

        else:
            logger.warning("⚠️ DATABASE_URL not found — falling back to SQLite")
            self._init_error = "DATABASE_URL not configured"

        logger.info("🔄 Initializing SQLite as fallback...")
        self._init_sqlite()
    
    def _init_sqlite(self):
        try:
            sqlite_url = f'sqlite:///{SQLITE_DB_PATH}'
            self.engine = create_engine(sqlite_url, echo=False, connect_args={"check_same_thread": False})
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            self._use_sqlite = True
            Base.metadata.create_all(bind=self.engine)
            self._migrate_schema()
            self._connected = True
            self._init_error = None
            logger.info(f"SQLite database initialized at {SQLITE_DB_PATH}")
            self._create_default_admin()
            self._create_default_factory()
            self._fix_missing_data()
        except Exception as e:
            self._init_error = str(e)
            self._connected = False
            logger.error(f"SQLite initialization failed: {e}")

    def is_connected(self):
        return self._connected

    def get_init_error(self):
        return self._init_error
    
    def is_using_sqlite(self):
        return self._use_sqlite

    def get_session(self):
        if not self.SessionLocal:
            raise Exception("قاعدة البيانات غير متصلة")
        return self.SessionLocal()

    def _migrate_schema(self):
        """ترحيل المخطط - إضافة الأعمدة الجديدة"""
        new_cols = [
            ("production", "packaging_waste", "FLOAT", "0"),
            ("production", "line_speed", "INTEGER", "0"),
            ("delivery", "delivery_note", "VARCHAR(100)", "''"),
            ("maintenance", "spare_parts", "TEXT", "''"),
            ("users", "must_change_password", "BOOLEAN", "FALSE"),
            ("users", "last_password_change", "TIMESTAMP", "CURRENT_TIMESTAMP"),
            ("users", "company_id", "INTEGER", "NULL"),
            ("users", "is_super_admin", "BOOLEAN", "FALSE"),
            ("users", "email", "VARCHAR(200)", "NULL"),
            ("users", "email_verified", "BOOLEAN", "FALSE"),
            ("users", "email_verification_token", "VARCHAR(255)", "NULL"),
            ("users", "reset_password_token", "VARCHAR(255)", "NULL"),
            ("users", "reset_password_expires", "TIMESTAMP", "NULL"),
            ("users", "failed_attempts", "INTEGER", "0"),
        ]
        # إزالة UNIQUE constraint عن عمود username للسماح بتكرار أسماء المستخدمين عبر المصانع
        self._drop_username_unique_constraint()
        # إضافة الأعمدة المفقودة لجدول materials
        self._migrate_materials_table()
        # إضافة factory_id لبقية الجداول
        tables = ['production', 'maintenance', 'delivery', 'raw_receipt', 'raw_materials', 'finished_goods', 'downtime_records', 'oee_summary']
        for table in tables:
            new_cols.append((table, "factory_id", "INTEGER", "NULL"))
        
        # إضافة company_id لجميع الجداول القديمة (للتوحيد)
        company_id_tables = [
            'production', 'maintenance', 'delivery', 'raw_receipt',
            'raw_materials', 'finished_goods', 'downtime_records',
            'oee_summary', 'alerts', 'system_logs', 'factory_config',
            'raw_material_transactions', 'finished_good_transactions'
        ]
        for table in company_id_tables:
            new_cols.append((table, "company_id", "INTEGER", "NULL"))
        
        for table, column, col_type, default in new_cols:
            self._ensure_column(table, column, col_type, default)
        
        # حذف قيود المفاتيح الخارجية لـ factory_id (لم نعد نستخدم factories.id)
        fk_tables = ['production', 'maintenance', 'delivery', 'raw_receipt',
                     'raw_materials', 'finished_goods', 'downtime_records',
                     'oee_summary', 'alerts', 'system_logs', 'factory_config',
                     'raw_material_transactions', 'finished_good_transactions']
        for table in fk_tables:
            self._drop_fk_if_exists(table)

    def _drop_username_unique_constraint(self):
        """إزالة UNIQUE constraint عن عمود username للسماح بتكرار أسماء المستخدمين عبر المصانع"""
        if not self.engine:
            return
        try:
            with self.engine.connect() as conn:
                if self._use_sqlite:
                    # SQLite لا يدعم DROP CONSTRAINT مباشرة، نتحقق فقط
                    rows = conn.execute(text("PRAGMA index_list(users)")).fetchall()
                    for row in rows:
                        if row[1] == 'sqlite_autoindex_users_1':
                            logger.info("ℹ️ SQLite UNIQUE constraint on users.username exists (cannot drop easily)")
                            break
                else:
                    # PostgreSQL
                    conn.execute(text("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_username_key"))
                    logger.info("✅ Dropped UNIQUE constraint on users.username")
                conn.commit()
        except Exception as e:
            logger.warning(f"Could not drop UNIQUE constraint on users.username: {e}")

    def _migrate_materials_table(self):
        """إضافة الأعمدة المفقودة لجدول materials و product_bom_details"""
        material_cols = [
            ("size", "VARCHAR(50)", "NULL"),
            ("pieces_per_roll", "INTEGER", "NULL"),
            ("units_per_pallet", "INTEGER", "NULL"),
            ("pieces_per_unit", "INTEGER", "NULL"),
            ("dividers_per_pallet", "INTEGER", "NULL"),
            ("shrink_film_grams_per_pallet", "FLOAT", "NULL"),
            ("category", "VARCHAR(100)", "NULL"),
            ("current_stock", "FLOAT", "0"),
            ("daily_consumption", "FLOAT", "0"),
            ("created_at", "TIMESTAMP", "CURRENT_TIMESTAMP"),
            ("updated_at", "TIMESTAMP", "CURRENT_TIMESTAMP"),
        ]
        for col, col_type, default in material_cols:
            self._ensure_column("materials", col, col_type, default)

        # أعمدة product_bom_details المفقودة
        bom_detail_cols = [
            ("preform_material_id", "INTEGER", "NULL"),
            ("cap_material_id", "INTEGER", "NULL"),
            ("label_material_id", "INTEGER", "NULL"),
            ("carton_material_id", "INTEGER", "NULL"),
            ("shrink_material_id", "INTEGER", "NULL"),
            ("shrink_divider_material_id", "INTEGER", "NULL"),
            ("shrink_dividers_per_pallet", "INTEGER", "NULL"),
            ("label_glue_material_id", "INTEGER", "NULL"),
            ("carton_glue_material_id", "INTEGER", "NULL"),
            ("shrink_film_material_id", "INTEGER", "NULL"),
            ("shrink_film_grams_per_pallet", "FLOAT", "NULL"),
            ("units_per_pallet", "INTEGER", "NULL"),
        ]
        for col, col_type, default in bom_detail_cols:
            self._ensure_column("product_bom_details", col, col_type, default)

    def _drop_fk_if_exists(self, table: str, column: str = 'factory_id'):
        """حذف المفتاح الخارجي من عمود factory_id إذا كان موجوداً (PostgreSQL فقط)"""
        if not self.engine or self._use_sqlite:
            return
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT con.conname
                    FROM pg_catalog.pg_constraint con
                    JOIN pg_catalog.pg_class rel ON rel.oid = con.conrelid
                    JOIN pg_catalog.pg_attribute att ON att.attrelid = con.conrelid AND att.attnum = ANY(con.conkey)
                    WHERE rel.relname = :table
                    AND att.attname = :column
                    AND con.contype = 'f'
                """), {"table": table, "column": column})
                for row in result:
                    constraint_name = row[0]
                    conn.execute(text(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {constraint_name}"))
                    logger.info(f"✅ Dropped FK constraint {constraint_name} on {table}")
                conn.commit()
        except Exception as e:
            logger.warning(f"Could not drop FK on {table}.{column}: {e}")

    def _ensure_column(self, table: str, column: str, col_type: str, default: str):
        """إضافة عمود إذا لم يكن موجوداً"""
        if not self.engine:
            return
        try:
            with self.engine.connect() as conn:
                if self._use_sqlite:
                    rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
                    if any(r[1] == column for r in rows):
                        return
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type} DEFAULT {default}"))
                else:
                    pg_col_type = col_type
                    if col_type.upper() == 'DATETIME':
                        pg_col_type = 'TIMESTAMP'
                    
                    conn.execute(text(f"""
                        ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {pg_col_type} DEFAULT {default}
                    """))
                conn.commit()
        except Exception as e:
            logger.warning(f"Schema migration skipped for {table}.{column}: {e}")

# database.py - استبدل دالة _create_default_admin

    def _create_default_admin(self):
        session = None
        try:
            session = self.get_session()
            
            # التحقق من وجود المستخدم admin
            existing = session.query(User).filter(User.username == "admin").first()
            
            if not existing:
                import bcrypt
                new_hash = bcrypt.hashpw("100".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                
                new_user = User(
                    username="admin",
                    password_hash=new_hash,
                    role="admin",
                    name="مدير النظام",
                    icon="👑",
                    is_active=True,
                    created_at=datetime.now(),
                    must_change_password=False,
                    last_password_change=datetime.now(),
                    is_super_admin=True,
                    company_id=None  # ✅ مهم جداً: super_admin ليس له company_id
                )
                session.add(new_user)
                session.commit()
                logger.info("✅ Created default super admin user (admin/100)")
            else:
                # التأكد من أن company_id = None للمشرف العام
                if existing.company_id is not None:
                    existing.company_id = None
                    session.commit()
                    logger.info("✅ Fixed admin company_id to None")
                
                if not existing.is_super_admin:
                    existing.is_super_admin = True
                    session.commit()
                    logger.info("✅ Updated existing admin to super_admin")
            
                # إنشاء المستخدمين الافتراضيين الآخرين
            default_users = [
                {"username": "pro", "password": "400", "role": "supervisor", "name": "مشرف إنتاج", "icon": "👔", "is_super_admin": False},
                {"username": "tec", "password": "300", "role": "technician", "name": "فني صيانة", "icon": "🔧", "is_super_admin": False},
                {"username": "sto", "password": "200", "role": "storekeeper", "name": "أمين مخزن", "icon": "📦", "is_super_admin": False},
                {"username": "quality", "password": "quality123", "role": "quality", "name": "مراقب جودة", "icon": "🔍", "is_super_admin": False},
            ]
            
            for user_data in default_users:
                existing_user = session.query(User).filter(User.username == user_data["username"]).first()
                if not existing_user:
                    import bcrypt
                    new_hash = bcrypt.hashpw(user_data["password"].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    new_user = User(
                        username=user_data["username"],
                        password_hash=new_hash,
                        role=user_data["role"],
                        name=user_data["name"],
                        icon=user_data["icon"],
                        is_active=True,
                        created_at=datetime.now(),
                        must_change_password=False,
                        is_super_admin=False
                    )
                    session.add(new_user)
            
            session.commit()
            logger.info("Default users created/verified.")
            
        except Exception as e:
            logger.warning(f"Could not create default users: {e}")
            if session:
                session.rollback()
        finally:
            if session:
                session.close()
# database.py - داخل class DatabaseManager

    def create_user(self, username: str, password: str, role: str, name: str, icon: str = "👤", must_change_password: bool = True) -> bool:
        """إنشاء مستخدم جديد"""
        session = None
        try:
            session = self.get_session()
            existing = session.query(User).filter(User.username == username).first()
            if existing:
                return False
            
            # الحصول على company_id من session state
            import streamlit as st
            company_id = st.session_state.get('company_id') or st.session_state.get('factory_id')
            
            new_user = User(
                username=username,
                password_hash=self.hash_password(password),
                role=role,
                name=name,
                icon=icon,
                is_active=True,
                created_at=datetime.now(),
                must_change_password=must_change_password,
                last_password_change=datetime.now(),
                company_id=company_id
            )
            session.add(new_user)
            session.commit()
            logger.info(f"User created: {username} with company_id={company_id}")
            return True
        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"create_user error: {e}")
            return False
        finally:
            if session:
                session.close()

    def unlock_user(self, user_id: int) -> bool:
        """إلغاء قفل حساب مستخدم"""
        session = None
        try:
            session = self.get_session()
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                # إعادة تعيين محاولات الفشل
                # إذا كان لديك حقل failed_attempts, قم بتعيينه إلى 0
                # وإلا قم بتعيين is_active = True
                if hasattr(user, 'failed_attempts'):
                    user.failed_attempts = 0
                user.is_active = True
                session.commit()
                return True
            return False
        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"unlock_user error: {e}")
            return False
        finally:
            if session:
                session.close()

    def _create_default_factory(self):
        """إنشاء شركة/مصنع افتراضي للمستخدمين الحاليين"""
        session = None
        try:
            session = self.get_session()
            
            # التحقق من وجود شركة افتراضية
            default_company = session.query(Company).filter(Company.code == 'default').first()
            
            if not default_company:
                default_company = Company(
                    name_ar='الشركة الرئيسية',
                    name_en='Main Company',
                    code='default',
                    status='active',
                    subscription_plan='enterprise',
                    created_at=datetime.now()
                )
                session.add(default_company)
                session.flush()
                logger.info("✅ Created default company")
            
            # تحديث المستخدمين الذين ليس لديهم company_id
            session.query(User).filter(User.company_id.is_(None)).update(
                {User.company_id: default_company.id},
                synchronize_session=False
            )
            
            # التأكد من وجود سجل factories للمستخدمين القدامى
            existing_factory = session.query(Factory).filter(Factory.id == default_company.id).first()
            if not existing_factory:
                existing_factory = Factory(
                    id=default_company.id,
                    name_ar=default_company.name_ar,
                    name_en=default_company.name_en,
                    code=f'F{default_company.id}',
                    status='active',
                    created_at=datetime.now()
                )
                session.add(existing_factory)
                session.flush()
            
            # تحديث جميع السجلات القديمة (بدون company_id) لتنتمي للشركة الافتراضية
            self._migrate_null_company_ids(default_company.id)
            
            session.commit()
            logger.info("✅ Default company setup completed")
            
        except Exception as e:
            logger.warning(f"Could not create default company: {e}")
            if session:
                session.rollback()
        finally:
            if session:
                session.close()

    def _migrate_null_company_ids(self, target_company_id: int):
        """ترحيل جميع السجلات التي company_id=NULL إلى شركة محددة (لعزل البيانات)"""
        session = None
        try:
            session = self.get_session()
            tables_with_company = [
                "raw_materials", "finished_goods", "production", "maintenance",
                "deliveries", "raw_receipts", "alerts", "maintenance_logs",
                "downtime_records", "oee_summaries", "factory_emails",
                "inventory_transactions", "raw_material_transactions",
                "finished_good_transactions", "factory_config", "products",
                "materials", "product_bom", "product_bom_detail",
                "production_lines", "product_line_speeds", "shifts",
                "system_logs",
            ]
            for table in tables_with_company:
                try:
                    session.execute(
                        text(f"UPDATE {table} SET company_id = :cid, factory_id = :cid WHERE company_id IS NULL"),
                        {"cid": target_company_id}
                    )
                except Exception:
                    pass  # بعض الجداول قد لا تحتوي على company_id
            session.commit()
            logger.info(f"✅ Migrated NULL company_ids to company {target_company_id}")
        except Exception as e:
            if session:
                session.rollback()
            logger.warning(f"_migrate_null_company_ids warning: {e}")
        finally:
            if session:
                session.close()

    def _fix_missing_data(self):
        """إصلاح البيانات المفقودة بعد الترحيل: إنشاء raw_materials و users للمصانع الجديدة"""
        session = None
        try:
            session = self.get_session()
            
            # 1️⃣ إنشاء سجلات RawMaterial للمواد الخام الموجودة في جدول materials
            materials_created = 0
            for mat in session.query(Material).all():
                existing = session.query(RawMaterial).filter(
                    RawMaterial.material_id == mat.code,
                    RawMaterial.factory_id == mat.company_id
                ).first()
                if not existing:
                    rm = RawMaterial(
                        material_id=mat.code,
                        name_ar=mat.name_ar,
                        name_en=mat.name_en,
                        current_stock=0,
                        min_stock=mat.min_stock or 0,
                        max_stock=mat.max_stock or 0,
                        unit=mat.unit or 'قطعة',
                        company_id=mat.company_id,
                        factory_id=mat.company_id,
                        is_active=True
                    )
                    session.add(rm)
                    materials_created += 1
            
            if materials_created > 0:
                logger.info(f"✅ Created {materials_created} missing RawMaterial records")

            session.commit()
        except Exception as e:
            logger.warning(f"_fix_missing_data warning: {e}")
            if session:
                session.rollback()
        finally:
            if session:
                session.close()

    def hash_password(self, password: str) -> str:
        try:
            salt = bcrypt.gensalt()
            return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        except Exception:
            import hashlib
            import secrets
            salt = secrets.token_hex(16)
            return f"{salt}:{hashlib.sha256((password + salt).encode()).hexdigest()}"

# database.py - استبدل دالة verify_password بهذه النسخة

    def verify_password(self, plain: str, hashed: str) -> bool:
        """التحقق من صحة كلمة المرور - دعم bcrypt والتجزئة القديمة"""
        try:
            # محاولة التحقق باستخدام bcrypt أولاً
            return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
        except Exception as e:
            print(f"   bcrypt check failed: {e}")
            try:
                # محاولة التحقق باستخدام التجزئة القديمة (SHA256 مع salt)
                if ':' in hashed:
                    import hashlib
                    salt, hash_value = hashed.split(':')
                    computed = hashlib.sha256((plain + salt).encode()).hexdigest()
                    return computed == hash_value
            except:
                pass
            
            # محاولة مقارنة مباشرة (للكلمات المرور غير المشفرة)
            if plain == hashed:
                print(f"   ⚠️ Plain text password match (should be migrated)")
                return True
            
            return False

    def get_current_factory_id(self):
        """الحصول على ID المصنع الحالي للمستخدم"""
        try:
            import streamlit as st
            return st.session_state.get('factory_id')
        except:
            return None
# database.py - داخل class DatabaseManager

    def get_factory_stats(self, company_id):
        """الحصول على إحصائيات شركة/مصنع معين"""
        session = self.get_session()
        try:
            from sqlalchemy import text
            users_count = session.execute(text("SELECT COUNT(*) FROM users WHERE company_id = :cid AND is_active = 1"), {'cid': company_id}).fetchone()[0]
            production_count = session.execute(text("SELECT COUNT(*) FROM production WHERE factory_id = :cid"), {'cid': company_id}).fetchone()[0]
            maintenance_count = session.execute(text("SELECT COUNT(*) FROM maintenance WHERE factory_id = :cid"), {'cid': company_id}).fetchone()[0]
            
            return {
                'users_count': users_count,
                'total_production': production_count,
                'total_maintenance': maintenance_count
            }
        except Exception as e:
            print(f"get_factory_stats error: {e}")
            return {'users_count': 0, 'total_production': 0, 'total_maintenance': 0}
        finally:
            session.close()

    def switch_factory(self, company_id):
        """تبديل الشركة/المصنع الحالي"""
        import streamlit as st
        st.session_state.company_id = company_id
        st.session_state.factory_id = company_id
        session = self.get_session()
        try:
            from sqlalchemy import text
            company = session.execute(text("SELECT name_ar FROM companies WHERE id = :cid"), {'cid': company_id}).fetchone()
            if company:
                st.session_state.factory_name = company[0]
        except Exception as e:
            print(f"switch_factory error: {e}")
        finally:
            session.close()
        st.cache_data.clear()
        return True        

    def get_factory_config(self, factory_id, line_name):
        """الحصول على إعدادات خط إنتاج معين لمصنع معين"""
        session = None
        try:
            session = self.get_session()
            configs = session.query(FactoryConfig).filter(
                FactoryConfig.factory_id == factory_id,
                FactoryConfig.line_name == line_name
            ).all()
            result = {}
            for c in configs:
                if c.config_type not in result:
                    result[c.config_type] = {}
                import json
                result[c.config_type][c.config_key] = json.loads(c.config_value)
            return result
        except Exception as e:
            logger.error(f"get_factory_config error: {e}")
            return {}
        finally:
            if session:
                session.close()

    def set_factory_config(self, factory_id, line_name, config_type, config_key, config_value):
        """تعيين إعدادات خط إنتاج لمصنع"""
        session = None
        try:
            session = self.get_session()
            import json
            existing = session.query(FactoryConfig).filter(
                FactoryConfig.factory_id == factory_id,
                FactoryConfig.line_name == line_name,
                FactoryConfig.config_type == config_type,
                FactoryConfig.config_key == config_key
            ).first()
            if existing:
                existing.config_value = json.dumps(config_value)
                existing.updated_at = datetime.now()
            else:
                cfg = FactoryConfig(
                    company_id=factory_id,
                    factory_id=factory_id,
                    line_name=line_name,
                    config_type=config_type,
                    config_key=config_key,
                    config_value=json.dumps(config_value)
                )
                session.add(cfg)
            session.commit()
            return True
        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"set_factory_config error: {e}")
            return False
        finally:
            if session:
                session.close()

    def migrate_config_to_db(self, factory_id):
        """ترحيل CONFIG الثابت إلى قاعدة البيانات لمصنع معين"""
        from constants import CONFIG, BOM
        import json
        for line_name, line_config in CONFIG.items():
            for product in line_config.get('products', []):
                self.set_factory_config(factory_id, line_name, 'product', product, True)
            for product, speed in line_config.get('speed', {}).items():
                self.set_factory_config(factory_id, line_name, 'speed', product, speed)
            for product, ppu in line_config.get('pack_per_unit', {}).items():
                self.set_factory_config(factory_id, line_name, 'pack_per_unit', product, ppu)
        for product, bom_data in BOM.items():
            self.set_factory_config(factory_id, '__bom__', 'bom', product, bom_data)
        return True
    def _apply_factory_filter(self, query, model):
        """إضافة فلتر المصنع - للمستخدمين العاديين فقط"""
        try:
            import streamlit as st
            
            # المشرف العام يرى كل شيء
            if st.session_state.get('is_super_admin', False):
                return query
            
            # الحصول على company_id من session
            company_id = st.session_state.get('company_id') or st.session_state.get('factory_id')
            
            if not company_id:
                # إذا كان المستخدم ليس super_admin وليس لديه company_id، لا نعرض بيانات
                return query.filter(text('1=0'))
            
            # تطبيق الفلتر حسب الجدول
            # نعرض سجلات الشركة فقط - بدون السجلات العامة (company_id = NULL) لعزل البيانات
            if hasattr(model, 'company_id'):
                return query.filter(model.company_id == company_id)
            elif hasattr(model, 'factory_id'):
                return query.filter(model.factory_id == company_id)
            else:
                return query.filter(text('1=0'))
            
        except Exception as e:
            logger.error(f"_apply_factory_filter error: {e}")
            return query

    def _get_current_factory_id_for_save(self):
        """الحصول على ID الشركة/المصنع الحالي للحفظ - موحد"""
        try:
            import streamlit as st
            
            # إذا كان المستخدم super_admin، يمكنه اختيار company_id يدوياً
            if st.session_state.get('is_super_admin', False):
                # جرب استخدام company_id من session
                company_id = st.session_state.get('company_id') or st.session_state.get('factory_id')
                if company_id:
                    return company_id
                # إذا لم يكن هناك company_id، أرجع None (لن يحفظ بيانات لمصنع معين)
                return None
            
            # للمستخدمين العاديين
            company_id = st.session_state.get('company_id') or st.session_state.get('factory_id')
            return company_id
        except:
            return None

    def authenticate_user(self, username: str, password: str, company_id: int = None):
        """مصادقة المستخدم مع إمكانية تحديد المصنع"""
        session = None
        try:
            session = self.get_session()
            
            user = None
            # إذا تم تحديد مصنع، ابحث أولاً عن مستخدم خاص بهذا المصنع
            if company_id:
                user = session.query(User).filter(
                    User.username == username,
                    User.company_id == company_id
                ).first()
            
            # إذا لم يتم العثور على مستخدم خاص بالمصنع، ابحث عن مشرف عام
            if not user:
                user = session.query(User).filter(
                    User.username == username,
                    User.is_super_admin == True
                ).first()
            
            if not user:
                print(f"❌ User not found: {username} (company_id={company_id})")
                return None
            
            print(f"🔐 Authenticating: {username} (company_id={user.company_id})")
            
            # التحقق من كلمة المرور
            try:
                password_valid = bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8'))
            except:
                password_valid = (password == user.password_hash)
            
            if not password_valid:
                print(f"❌ Wrong password for: {username}")
                return None
            
            # تحديث آخر تسجيل دخول
            user.last_login = datetime.now()
            session.commit()
            
            return {
                'id': user.id,
                'username': user.username,
                'role': user.role,
                'name': user.name,
                'icon': user.icon,
                'is_active': user.is_active,
                'must_change_password': user.must_change_password,
                'company_id': user.company_id,
                'is_super_admin': user.is_super_admin
            }
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
        finally:
            if session:
                session.close()
    def update_user_password(self, username: str, new_password: str) -> bool:
        session = None
        try:
            session = self.get_session()
            user = session.query(User).filter(User.username == username).first()
            if user:
                new_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                user.password_hash = new_hash
                user.must_change_password = False
                user.last_password_change = datetime.now()
                session.commit()
                logger.info(f"Password updated for user: {username}")
                return True
            return False
        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"update_user_password error: {e}")
            return False
        finally:
            if session:
                session.close()
                

    def get_all_users(self):
        session = None
        try:
            session = self.get_session()
            query = session.query(User)
            query = self._apply_factory_filter(query, User)
            users = query.all()
            return [{'id': u.id, 'username': u.username, 'role': u.role, 'name': u.name, 'icon': u.icon, 'is_active': u.is_active, 'created_at': u.created_at, 'last_login': u.last_login, 'company_id': getattr(u, 'company_id', None), 'is_super_admin': getattr(u, 'is_super_admin', False)} for u in users]
        except Exception as e:
            logger.error(f"get_all_users error: {e}")
            return []
        finally:
            if session:
                session.close()

    def calculate_oee(self, data: dict) -> dict:
        working_minutes = int(data.get('working_minutes', 0) or 0)
        
        if working_minutes == 0:
            shift_start = data.get('shift_start', '08:00')
            shift_end = data.get('shift_end', '02:00')
            break_minutes = int(data.get('break_minutes', 180) or 180)
            
            try:
                start_parts = shift_start.split(':')
                end_parts = shift_end.split(':')
                start_total = int(start_parts[0]) * 60 + int(start_parts[1])
                end_total = int(end_parts[0]) * 60 + int(end_parts[1])
                
                if end_total <= start_total:
                    end_total += 24 * 60
                
                shift_minutes = end_total - start_total
                working_minutes = max(0, shift_minutes - break_minutes)
            except:
                working_minutes = 900
        
        planned_time = working_minutes
        downtime = max(0, int(data.get('downtime_minutes', 0) or 0))
        planned_downtime = max(0, int(data.get('planned_downtime', 0) or 0))
        
        total_downtime = downtime + planned_downtime
        operating_time = max(0, planned_time - total_downtime)
        
        if planned_time > 0:
            availability = (operating_time / planned_time) * 100
        else:
            availability = 0
        
        actual_output_units = int(data.get('output_units', 0) or 0)
        pieces_per_unit = max(1, int(data.get('pieces_per_unit', 1) or 1))
        actual_bottles = actual_output_units * pieces_per_unit
        
        ideal_run_rate = float(data.get('ideal_run_rate', 0) or 0)
        
        if operating_time > 0 and ideal_run_rate > 0:
            actual_rate = actual_bottles / operating_time
            performance = min(100.0, (actual_rate / ideal_run_rate) * 100)
        else:
            performance = 0
        
        waste = max(0, int(data.get('waste_bottles', 0) or 0))
        good_bottles = max(0, actual_bottles - waste)
        
        if actual_bottles > 0:
            quality = (good_bottles / actual_bottles) * 100
        else:
            quality = 0
        
        oee = (availability * performance * quality) / 10000
        oee = round(oee, 2)
        
        return {
            'oee': oee,
            'availability': round(availability, 2),
            'performance': round(performance, 2),
            'quality': round(quality, 2),
            'planned_time': planned_time,
            'operating_time': operating_time,
            'downtime': total_downtime,
            'planned_downtime': planned_downtime,
            'actual_bottles': actual_bottles,
            'good_bottles': good_bottles
        }

    def save_production(self, data: dict):
        session = None
        try:
            session = self.get_session()
            oee_data = self.calculate_oee(data)
            factory_id = self._get_current_factory_id_for_save()
            
            production = Production(
                type='Production',
                date=data['date'],
                line=data.get('line', ''),
                supervisor=data.get('supervisor', ''),
                product=data.get('product', ''),
                output_units=int(data.get('output_units', 0)),
                preforms_used=int(data.get('preforms_used', 0)),
                waste_bottles=int(data.get('waste_bottles', 0)),
                packaging_waste=float(data.get('packaging_waste', 0)),
                line_speed=int(data.get('line_speed', 0)),
                efficiency=float(data.get('efficiency', 0)),
                oee=oee_data['oee'],
                availability=oee_data['availability'],
                performance=oee_data['performance'],
                quality=oee_data['quality'],
                planned_production_time=oee_data['planned_time'],
                operating_time=oee_data['operating_time'],
                downtime_minutes=int(data.get('downtime_minutes', 0)),
                ideal_run_rate=float(data.get('ideal_run_rate', 0)),
                shift=data.get('shift', ''),
                timestamp=datetime.now(),
                company_id=factory_id,
                factory_id=factory_id
            )
            session.add(production)
            session.commit()
            return production.id
        except Exception as e:
            if session:
                session.rollback()
            raise e
        finally:
            if session:
                session.close()

    def get_all_production(self, start_date=None, end_date=None, line=None, product=None, supervisor=None):
        session = None
        try:
            session = self.get_session()
            query = session.query(Production)
            query = self._apply_factory_filter(query, Production)
            
            if start_date:
                query = query.filter(Production.date >= start_date)
            if end_date:
                query = query.filter(Production.date <= end_date)
            if line:
                query = query.filter(Production.line == line)
            if product:
                query = query.filter(Production.product == product)
            if supervisor:
                query = query.filter(Production.supervisor == supervisor)
            
            query = query.order_by(Production.date.desc())
            df = pd.read_sql(query.statement, session.bind)
            return df
        except Exception as e:
            logger.error(f"get_all_production error: {e}")
            return pd.DataFrame()
        finally:
            if session:
                session.close()

    def get_production_by_id(self, record_id: int):
        session = None
        try:
            session = self.get_session()
            query = session.query(Production).filter(Production.id == record_id)
            query = self._apply_factory_filter(query, Production)
            record = query.first()
            if record:
                return {
                    'id': record.id,
                    'date': record.date,
                    'line': record.line,
                    'product': record.product,
                    'output_units': record.output_units,
                    'preforms_used': record.preforms_used,
                    'waste_bottles': record.waste_bottles,
                    'packaging_waste': getattr(record, 'packaging_waste', 0) or 0,
                    'line_speed': getattr(record, 'line_speed', 0) or 0,
                    'efficiency': record.efficiency,
                    'downtime_minutes': record.downtime_minutes,
                    'factory_id': record.factory_id
                }
            return None
        finally:
            if session:
                session.close()

    def delete_production(self, record_id: int):
        session = None
        try:
            session = self.get_session()
            query = session.query(Production).filter(Production.id == record_id)
            query = self._apply_factory_filter(query, Production)
            record = query.first()
            if record:
                session.delete(record)
                session.commit()
                logger.info(f"Production record {record_id} deleted")
                return True
            return False
        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"delete_production error: {e}")
            return False
        finally:
            if session:
                session.close()

    def save_maintenance(self, data: dict):
        session = None
        try:
            session = self.get_session()
            factory_id = self._get_current_factory_id_for_save()
            
            maintenance = Maintenance(
                type=data.get('type', 'planned'),
                date=data['date'],
                line=data.get('line', ''),
                machine=data.get('machine', ''),
                technician=data.get('technician', ''),
                issue=data.get('issue', ''),
                task=data.get('task', ''),
                start_time=str(data.get('start_time', '')),
                end_time=str(data.get('end_time', '')),
                downtime_minutes=int(data.get('downtime_minutes', 0)),
                downtime_category=data.get('downtime_category', ''),
                spare_parts=data.get('spare_parts', ''),
                notes=data.get('notes', ''),
                timestamp=datetime.now(),
                company_id=factory_id,
                factory_id=factory_id
            )
            session.add(maintenance)
            session.commit()
            return maintenance.id
        except Exception as e:
            if session:
                session.rollback()
            raise e
        finally:
            if session:
                session.close()

    def get_all_maintenance(self, start_date=None, end_date=None, line=None, machine=None, technician=None, maint_type=None):
        session = None
        try:
            session = self.get_session()
            query = session.query(Maintenance)
            query = self._apply_factory_filter(query, Maintenance)
            
            if start_date:
                query = query.filter(Maintenance.date >= start_date)
            if end_date:
                query = query.filter(Maintenance.date <= end_date)
            if line:
                query = query.filter(Maintenance.line == line)
            if machine:
                query = query.filter(Maintenance.machine == machine)
            if technician:
                query = query.filter(Maintenance.technician == technician)
            if maint_type:
                query = query.filter(Maintenance.type == maint_type)
            
            query = query.order_by(Maintenance.date.desc())
            df = pd.read_sql(query.statement, session.bind)
            return df
        except Exception as e:
            logger.error(f"get_all_maintenance error: {e}")
            return pd.DataFrame()
        finally:
            if session:
                session.close()
# أضف هذه الدوال إلى class DatabaseManager في ملف database.py

    def get_distinct_products(self):
        """الحصول على قائمة المنتجات المميزة من سجلات الإنتاج (مفلترة حسب المصنع)"""
        session = None
        try:
            session = self.get_session()
            query = session.query(Production.product).filter(
                Production.product.isnot(None),
                Production.product != ''
            )
            query = self._apply_factory_filter(query, Production)
            products = [row[0] for row in query.distinct().order_by(Production.product).all()]
            return products
        except Exception as e:
            logger.error(f"get_distinct_products error: {e}")
            return []
        finally:
            if session:
                session.close()

    def get_distinct_supervisors(self):
        """الحصول على قائمة المشرفين المميزين من سجلات الإنتاج (مفلترة حسب المصنع)"""
        session = None
        try:
            session = self.get_session()
            query = session.query(Production.supervisor).filter(
                Production.supervisor.isnot(None),
                Production.supervisor != ''
            )
            query = self._apply_factory_filter(query, Production)
            supervisors = [row[0] for row in query.distinct().order_by(Production.supervisor).all()]
            return supervisors
        except Exception as e:
            logger.error(f"get_distinct_supervisors error: {e}")
            return []
        finally:
            if session:
                session.close()

    def get_distinct_machines(self):
        """الحصول على قائمة الماكينات المميزة من سجلات الصيانة (مفلترة حسب المصنع)"""
        session = None
        try:
            session = self.get_session()
            query = session.query(Maintenance.machine).filter(
                Maintenance.machine.isnot(None),
                Maintenance.machine != ''
            )
            query = self._apply_factory_filter(query, Maintenance)
            machines = [row[0] for row in query.distinct().order_by(Maintenance.machine).all()]
            return machines
        except Exception as e:
            logger.error(f"get_distinct_machines error: {e}")
            return []
        finally:
            if session:
                session.close()

    def get_distinct_customers(self):
        """الحصول على قائمة العملاء المميزين من سجلات التسليم (مفلترة حسب المصنع)"""
        session = None
        try:
            session = self.get_session()
            query = session.query(Delivery.customer).filter(
                Delivery.customer.isnot(None),
                Delivery.customer != ''
            )
            query = self._apply_factory_filter(query, Delivery)
            customers = [row[0] for row in query.distinct().order_by(Delivery.customer).all()]
            return customers
        except Exception as e:
            logger.error(f"get_distinct_customers error: {e}")
            return []
        finally:
            if session:
                session.close()

    def get_distinct_materials(self):
        """الحصول على قائمة المواد الخام المميزة من سجلات المشتريات (مفلترة حسب المصنع)"""
        session = None
        try:
            session = self.get_session()
            query = session.query(RawReceipt.material).filter(
                RawReceipt.material.isnot(None),
                RawReceipt.material != ''
            )
            query = self._apply_factory_filter(query, RawReceipt)
            materials = [row[0] for row in query.distinct().order_by(RawReceipt.material).all()]
            return materials
        except Exception as e:
            logger.error(f"get_distinct_materials error: {e}")
            return []
        finally:
            if session:
                session.close()

    def get_distinct_invoices(self):
        """الحصول على قائمة الفواتير المميزة من سجلات المشتريات (مفلترة حسب المصنع)"""
        session = None
        try:
            session = self.get_session()
            query = session.query(RawReceipt.invoice).filter(
                RawReceipt.invoice.isnot(None),
                RawReceipt.invoice != ''
            )
            query = self._apply_factory_filter(query, RawReceipt)
            invoices = [row[0] for row in query.distinct().order_by(RawReceipt.invoice).all()]
            return invoices
        except Exception as e:
            logger.error(f"get_distinct_invoices error: {e}")
            return []
        finally:
            if session:
                session.close()                

    def save_delivery(self, data: dict):
        session = None
        try:
            session = self.get_session()
            factory_id = self._get_current_factory_id_for_save()
            
            delivery = Delivery(
                date=data['date'],
                product=data.get('product', ''),
                quantity=int(data.get('quantity', 0)),
                customer=data.get('customer', ''),
                delivery_note=data.get('delivery_note', ''),
                notes=data.get('notes', ''),
                timestamp=datetime.now(),
                company_id=factory_id,
                factory_id=factory_id
            )
            session.add(delivery)
            session.commit()
            return delivery.id
        except Exception as e:
            if session:
                session.rollback()
            raise e
        finally:
            if session:
                session.close()

    def get_all_delivery(self, start_date=None, end_date=None, product=None, customer=None):
        session = None
        try:
            session = self.get_session()
            query = session.query(Delivery)
            query = self._apply_factory_filter(query, Delivery)
            
            if start_date:
                query = query.filter(Delivery.date >= start_date)
            if end_date:
                query = query.filter(Delivery.date <= end_date)
            if product:
                query = query.filter(Delivery.product == product)
            if customer:
                query = query.filter(Delivery.customer == customer)
            
            query = query.order_by(Delivery.date.desc())
            df = pd.read_sql(query.statement, session.bind)
            return df
        except Exception as e:
            logger.error(f"get_all_delivery error: {e}")
            return pd.DataFrame()
        finally:
            if session:
                session.close()

    def save_raw_receipt(self, data: dict):
        session = None
        try:
            session = self.get_session()
            factory_id = self._get_current_factory_id_for_save()
            
            receipt = RawReceipt(
                date=data['date'],
                material=data.get('material', ''),
                quantity=int(data.get('quantity', 0)),
                invoice=data.get('invoice', ''),
                notes=data.get('notes', ''),
                timestamp=datetime.now(),
                company_id=factory_id,
                factory_id=factory_id
            )
            session.add(receipt)
            session.commit()
            return receipt.id
        except Exception as e:
            if session:
                session.rollback()
            raise e
        finally:
            if session:
                session.close()

    def get_all_raw_receipts(self, start_date=None, end_date=None, material=None, invoice=None):
        session = None
        try:
            session = self.get_session()
            query = session.query(RawReceipt)
            query = self._apply_factory_filter(query, RawReceipt)
            
            if start_date:
                query = query.filter(RawReceipt.date >= start_date)
            if end_date:
                query = query.filter(RawReceipt.date <= end_date)
            if material:
                query = query.filter(RawReceipt.material == material)
            if invoice:
                query = query.filter(RawReceipt.invoice == invoice)
            
            query = query.order_by(RawReceipt.date.desc())
            df = pd.read_sql(query.statement, session.bind)
            return df
        except Exception as e:
            logger.error(f"get_all_raw_receipts error: {e}")
            return pd.DataFrame()
        finally:
            if session:
                session.close()

    def get_all_raw_materials(self):
        session = None
        try:
            session = self.get_session()
            query = session.query(RawMaterial).filter(RawMaterial.is_active == True)
            query = self._apply_factory_filter(query, RawMaterial)
            materials = query.all()
            
            result = []
            for m in materials:
                result.append({
                    'id': m.id,
                    'material_id': m.material_id,
                    'name_ar': m.name_ar,
                    'name_en': m.name_en,
                    'current_stock': float(m.current_stock) if m.current_stock else 0,
                    'min_stock': float(m.min_stock) if m.min_stock else 0,
                    'max_stock': float(m.max_stock) if m.max_stock else 0,
                    'unit': m.unit,
                    'unit_cost': float(m.unit_cost) if m.unit_cost else 0,
                    'daily_consumption': float(m.daily_consumption) if m.daily_consumption else 0,
                    'last_updated': m.last_updated
                })
            return result
        except Exception as e:
            logger.error(f"get_all_raw_materials error: {e}")
            return []
        finally:
            if session:
                session.close()

    def get_all_finished_goods(self):
        session = None
        try:
            session = self.get_session()
            query = session.query(FinishedGood)
            query = self._apply_factory_filter(query, FinishedGood)
            goods = query.all()
            
            result = []
            for g in goods:
                result.append({
                    'id': g.id,
                    'name': g.name,
                    'opening_balance': float(g.opening_balance) if g.opening_balance else 0,
                    'stock_in': float(g.stock_in) if g.stock_in else 0,
                    'stock_out': float(g.stock_out) if g.stock_out else 0,
                    'balance': float(g.balance) if g.balance else 0,
                    'unit': g.unit,
                    'month_key': g.month_key,
                    'last_updated': g.last_updated
                })
            return result
        except Exception as e:
            logger.error(f"get_all_finished_goods error: {e}")
            return []
        finally:
            if session:
                session.close()

    def get_oee_trend(self, line=None, days=30):
        session = None
        try:
            session = self.get_session()
            start_date = datetime.now() - timedelta(days=days)
            query = session.query(Production).filter(Production.date >= start_date)
            query = self._apply_factory_filter(query, Production)
            if line:
                query = query.filter(Production.line == line)
            query = query.order_by(Production.date)
            df = pd.read_sql(query.statement, session.bind)
            if df.empty:
                return pd.DataFrame()
            df['date'] = pd.to_datetime(df['date']).dt.date
            daily = df.groupby('date').agg(oee=('oee', 'mean'), availability=('availability', 'mean'), performance=('performance', 'mean'), quality=('quality', 'mean')).reset_index()
            return daily.round(2)
        except Exception as e:
            logger.error(f"get_oee_trend error: {e}")
            return pd.DataFrame()
        finally:
            if session:
                session.close()

    def add_alert(self, alert_type: str, title: str, message: str, severity: str = 'warning', related_id: int = None, related_name: str = None) -> int:
        session = None
        try:
            session = self.get_session()
            factory_id = self._get_current_factory_id_for_save()
            alert = Alert(
                alert_type=alert_type,
                severity=severity,
                title=title,
                message=message,
                related_id=related_id,
                related_name=related_name,
                is_read=False,
                is_dismissed=False,
                created_at=datetime.now(),
                company_id=factory_id,
                factory_id=factory_id
            )
            session.add(alert)
            session.commit()
            return alert.id
        except Exception as e:
            logger.error(f"Failed to add alert: {e}")
            if session:
                session.rollback()
            return None
        finally:
            if session:
                session.close()

    def get_active_alerts(self, limit: int = 50) -> list:
        session = None
        try:
            session = self.get_session()
            query = session.query(Alert)
            query = self._apply_factory_filter(query, Alert)
            alerts = query.order_by(
                Alert.severity.desc(),
                Alert.created_at.desc()
            ).limit(limit).all()
            
            return [{
                'id': a.id,
                'alert_type': a.alert_type,
                'severity': a.severity,
                'title': a.title,
                'message': a.message,
                'related_id': a.related_id,
                'related_name': a.related_name,
                'is_read': a.is_read,
                'created_at': a.created_at
            } for a in alerts]
        except Exception as e:
            logger.error(f"Failed to get active alerts: {e}")
            return []
        finally:
            if session:
                session.close()

    def dismiss_alert(self, alert_id: int, dismissed_by: str = None) -> bool:
        session = None
        try:
            session = self.get_session()
            query = session.query(Alert).filter(Alert.id == alert_id)
            query = self._apply_factory_filter(query, Alert)
            alert = query.first()
            if not alert:
                return False
            session.delete(alert)
            session.commit()
            return True
        except Exception as e:
            if session:
                session.rollback()
            return False
        finally:
            if session:
                session.close()

    def delete_maintenance(self, record_id: int) -> bool:
        session = None
        try:
            session = self.get_session()
            query = session.query(Maintenance).filter(Maintenance.id == record_id)
            query = self._apply_factory_filter(query, Maintenance)
            record = query.first()
            if record:
                session.delete(record)
                session.commit()
                return True
            return False
        except Exception as e:
            if session:
                session.rollback()
            return False
        finally:
            if session:
                session.close()

    def delete_delivery(self, record_id: int) -> bool:
        session = None
        try:
            session = self.get_session()
            query = session.query(Delivery).filter(Delivery.id == record_id)
            query = self._apply_factory_filter(query, Delivery)
            record = query.first()
            if record:
                session.delete(record)
                session.commit()
                return True
            return False
        except Exception as e:
            if session:
                session.rollback()
            return False
        finally:
            if session:
                session.close()

    def delete_raw_receipt(self, record_id: int) -> bool:
        session = None
        try:
            session = self.get_session()
            query = session.query(RawReceipt).filter(RawReceipt.id == record_id)
            query = self._apply_factory_filter(query, RawReceipt)
            record = query.first()
            if record:
                session.delete(record)
                session.commit()
                return True
            return False
        except Exception as e:
            if session:
                session.rollback()
            return False
        finally:
            if session:
                session.close()

    def add_log(self, event_type: str, action: str, event_level: str = 'INFO', details: str = None, user_id: int = None, username: str = None):
        session = None
        try:
            session = self.get_session()
            factory_id = self._get_current_factory_id_for_save()
            log = SystemLog(
                event_type=event_type,
                event_level=event_level,
                user_id=user_id,
                username=username,
                action=action,
                details=details,
                created_at=datetime.now(),
                company_id=factory_id,
                factory_id=factory_id
            )
            session.add(log)
            session.commit()
            return log.id
        except Exception as e:
            if session:
                session.rollback()
            return None
        finally:
            if session:
                session.close()

    def add_info_log(self, event_type: str, action: str, details: str = None):
        return self.add_log(event_type, action, 'INFO', details)

    def add_warning_log(self, event_type: str, action: str, details: str = None):
        return self.add_log(event_type, action, 'WARNING', details)

    def add_error_log(self, event_type: str, action: str, details: str = None):
        return self.add_log(event_type, action, 'ERROR', details)

    def get_logs(self, limit: int = 100, offset: int = 0, event_type: str = None, event_level: str = None, username: str = None, start_date=None, end_date=None):
        session = None
        try:
            session = self.get_session()
            query = session.query(SystemLog)
            query = self._apply_factory_filter(query, SystemLog)
            
            if event_type:
                query = query.filter(SystemLog.event_type == event_type)
            if event_level:
                query = query.filter(SystemLog.event_level == event_level)
            if username:
                query = query.filter(SystemLog.username == username)
            if start_date:
                query = query.filter(SystemLog.created_at >= start_date)
            if end_date:
                query = query.filter(SystemLog.created_at <= end_date)
            
            query = query.order_by(SystemLog.created_at.desc()).limit(limit).offset(offset)
            
            return [{
                'id': log.id,
                'event_type': log.event_type,
                'event_level': log.event_level,
                'user_id': log.user_id,
                'username': log.username,
                'action': log.action,
                'details': log.details,
                'created_at': log.created_at
            } for log in query.all()]
        except Exception as e:
            logger.error(f"Failed to get logs: {e}")
            return []
        finally:
            if session:
                session.close()

    def cleanup_old_logs(self, days: int = 30):
        session = None
        try:
            session = self.get_session()
            cutoff_date = datetime.now() - timedelta(days=days)
            query = session.query(SystemLog).filter(SystemLog.created_at < cutoff_date)
            query = self._apply_factory_filter(query, SystemLog)
            deleted = query.delete(synchronize_session='fetch')
            session.commit()
            return deleted
        except Exception as e:
            if session:
                session.rollback()
            return 0
        finally:
            if session:
                session.close()
# database.py - داخل class DatabaseManager

    def check_and_create_alerts(self, df_raw=None, df_main=None):
        """فحص وإنشاء التنبيهات تلقائياً"""
        # هذه الدالة سيتم تطويرها لاحقاً
        # حالياً نرجع قائمة فارغة
        return []                
    # database.py - أضف هذه الدوال داخل class DatabaseManager

    def create_company(self, name_ar: str, name_en: str, code: str, email: str = None, phone: str = None, address: str = None) -> int:
        """إنشاء شركة/مصنع جديد"""
        session = None
        try:
            session = self.get_session()
            company = Company(
                name_ar=name_ar,
                name_en=name_en,
                code=code,
                email=email,
                phone=phone,
                address_ar=address,
                address_en=address,
                status='active',
                subscription_plan='enterprise',
                created_at=datetime.now()
            )
            session.add(company)
            session.flush()
            session.commit()
            return company.id
        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"create_company error: {e}")
            return None
        finally:
            if session:
                session.close()

    def delete_company(self, company_id: int) -> bool:
        """حذف شركة/مصنع وجميع بياناته"""
        session = None
        try:
            session = self.get_session()
            # ترتيب الحذف مهم بسبب قيود المفاتيح الخارجية (FK)
            company_tables = [
                "raw_material_transactions", "finished_good_transactions",
                "inventory_transactions",
                "product_bom_details", "product_bom", "product_line_speed",
                "maintenance_logs",
                "factory_emails", "alerts", "system_logs", "shifts",
                "production_lines", "products", "materials",
            ]
            dual_id_tables = [
                "production", "maintenance", "delivery", "raw_receipt",
                "downtime_records", "oee_summary", "factory_config",
                "raw_materials", "finished_goods",
            ]
            for table in company_tables:
                session.execute(
                    text(f"DELETE FROM {table} WHERE company_id = :cid"),
                    {"cid": company_id},
                )
            for table in dual_id_tables:
                session.execute(
                    text(f"DELETE FROM {table} WHERE company_id = :cid OR factory_id = :cid"),
                    {"cid": company_id},
                )
            session.execute(
                text("UPDATE users SET company_id = NULL WHERE company_id = :cid"),
                {"cid": company_id},
            )
            session.execute(text("DELETE FROM companies WHERE id = :cid"), {"cid": company_id})
            session.commit()
            return True
        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"delete_company error: {e}")
            return False
        finally:
            if session:
                session.close()

    def create_production_line(self, company_id: int, name_ar: str, name_en: str, code: str) -> int:
        """إنشاء خط إنتاج جديد"""
        session = None
        try:
            session = self.get_session()
            line = ProductionLine(
                company_id=company_id,
                name_ar=name_ar,
                name_en=name_en,
                code=code,
                status='active'
            )
            session.add(line)
            session.commit()
            return line.id
        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"create_production_line error: {e}")
            return None
        finally:
            if session:
                session.close()

    def create_material(self, company_id: int, name_ar: str, name_en: str, code: str, unit: str = "قطعة", 
                      min_stock: float = 0, size: str = "general", 
                      pieces_per_roll: int = None, units_per_pallet: int = None,
                      pieces_per_unit: int = None, dividers_per_pallet: int = None,
                      shrink_film_grams_per_pallet: float = None) -> int:
        """إنشاء مادة خام جديدة"""
        session = None
        try:
            session = self.get_session()
            material = Material(
                company_id=company_id,
                name_ar=name_ar,
                name_en=name_en,
                code=code,
                unit=unit,
                min_stock=min_stock,
                size=size,
                pieces_per_roll=pieces_per_roll,
                units_per_pallet=units_per_pallet,
                pieces_per_unit=pieces_per_unit,
                dividers_per_pallet=dividers_per_pallet,
                shrink_film_grams_per_pallet=shrink_film_grams_per_pallet,
                is_active=True
            )
            session.add(material)
            session.commit()
            return material.id
        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"create_material error: {e}")
            return None
        finally:
            if session:
                session.close()

    def create_product(self, company_id: int, name_ar: str, name_en: str, code: str, pieces_per_unit: int = 1) -> int:
        """إنشاء منتج جديد"""
        session = None
        try:
            session = self.get_session()
            product = Product(
                company_id=company_id,
                name_ar=name_ar,
                name_en=name_en,
                code=code,
                pieces_per_unit=pieces_per_unit,
                is_active=True
            )
            session.add(product)
            session.commit()
            return product.id
        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"create_product error: {e}")
            return None
        finally:
            if session:
                session.close()

    def create_bom_item(self, company_id: int, product_id: int, material_id: int, quantity: float) -> int:
        """إنشاء مكون منتج (BOM)"""
        session = None
        try:
            session = self.get_session()
            bom = ProductBOM(
                company_id=company_id,
                product_id=product_id,
                material_id=material_id,
                quantity=quantity
            )
            session.add(bom)
            session.commit()
            return bom.id
        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"create_bom_item error: {e}")
            return None
        finally:
            if session:
                session.close()

    def create_shift(self, company_id: int, name_ar: str, name_en: str, start_time: str, end_time: str, break_duration: int = 0) -> int:
        """إنشاء وردية جديدة"""
        session = None
        try:
            session = self.get_session()
            shift = Shift(
                company_id=company_id,
                name_ar=name_ar,
                name_en=name_en,
                start_time=start_time,
                end_time=end_time,
                break_duration_minutes=break_duration,
                is_active=True
            )
            session.add(shift)
            session.commit()
            return shift.id
        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"create_shift error: {e}")
            return None
        finally:
            if session:
                session.close()

    def create_user_with_company(self, username: str, password: str, role: str, name: str, company_id: int, email: str = None) -> bool:
        """إنشاء مستخدم مرتبط بشركة - مع bcrypt صحيح"""
        session = None
        try:
            session = self.get_session()
            existing = session.query(User).filter(User.username == username).first()
            if existing:
                logger.warning(f"User {username} already exists")
                return False
            
            # ✅ استخدام bcrypt بنفس طريقة hash_password
            import bcrypt
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            new_user = User(
                username=username,
                password_hash=password_hash,
                role=role,
                name=name,
                is_active=True,
                company_id=company_id,
                is_super_admin=False,
                must_change_password=False,
                email=email
            )
            session.add(new_user)
            session.commit()
            logger.info(f"User {username} created with company_id={company_id}")
            return True
        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"create_user_with_company error: {e}")
            return False
        finally:
            if session:
                session.close()
    def get_current_company_id(self):
        """الحصول على company_id الحالي بشكل موحد"""
        try:
            import streamlit as st
            return st.session_state.get('company_id') or st.session_state.get('factory_id')
        except:
            return None            
                    

    def create_factory_email(self, company_id: int, email: str, name: str = None, role: str = None) -> bool:
        """إضافة إيميل مسئول للمصنع"""
        session = None
        try:
            session = self.get_session()
            existing = session.query(FactoryEmail).filter(
                FactoryEmail.company_id == company_id,
                FactoryEmail.email == email
            ).first()
            if existing:
                return False
            fe = FactoryEmail(
                company_id=company_id,
                email=email,
                name=name,
                role=role,
                is_active=True
            )
            session.add(fe)
            session.commit()
            return True
        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"create_factory_email error: {e}")
            return False
        finally:
            if session:
                session.close()

    def get_factory_emails(self, company_id: int) -> list:
        """الحصول على إيميلات مسئولي المصنع"""
        session = None
        try:
            session = self.get_session()
            emails = session.query(FactoryEmail).filter(
                FactoryEmail.company_id == company_id,
                FactoryEmail.is_active == True
            ).all()
            return [{'id': e.id, 'email': e.email, 'name': e.name, 'role': e.role} for e in emails]
        except Exception as e:
            logger.error(f"get_factory_emails error: {e}")
            return []
        finally:
            if session:
                session.close()

    def delete_factory_email(self, email_id: int) -> bool:
        """حذف إيميل مسئول"""
        session = None
        try:
            session = self.get_session()
            email = session.query(FactoryEmail).filter(FactoryEmail.id == email_id).first()
            if email:
                session.delete(email)
                session.commit()
                return True
            return False
        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"delete_factory_email error: {e}")
            return False
        finally:
            if session:
                session.close()

    def create_product_bom_detail(self, company_id: int, product_id: int,
                                  preforms_per_unit: int = 1, caps_per_unit: int = 1,
                                  labels_per_unit: int = 1, packaging_type: str = 'carton',
                                  units_per_carton: int = 48, units_per_shrink: int = 20,
                                  shrink_pieces_per_roll: int = 1980,
                                  label_glue_grams_per_bottle: float = 0.135,
                                  carton_glue_grams_per_carton: float = 0.5,
                                  min_stock_units: int = 0,
                                  preform_material_id: int = None,
                                  cap_material_id: int = None,
                                  label_material_id: int = None,
                                  carton_material_id: int = None,
                                  shrink_material_id: int = None,
                                  shrink_divider_material_id: int = None,
                                  shrink_dividers_per_pallet: int = None,
                                  label_glue_material_id: int = None,
                                  carton_glue_material_id: int = None,
                                  shrink_film_material_id: int = None,
                                  shrink_film_grams_per_pallet: float = None,
                                  units_per_pallet: int = None) -> int:
        """إنشاء تفاصيل BOM كاملة للمنتج"""
        session = None
        try:
            session = self.get_session()
            existing = session.query(ProductBOMDetail).filter(
                ProductBOMDetail.company_id == company_id,
                ProductBOMDetail.product_id == product_id
            ).first()
            if existing:
                existing.preforms_per_unit = preforms_per_unit
                existing.caps_per_unit = caps_per_unit
                existing.labels_per_unit = labels_per_unit
                existing.packaging_type = packaging_type
                existing.units_per_carton = units_per_carton
                existing.units_per_shrink = units_per_shrink
                existing.shrink_pieces_per_roll = shrink_pieces_per_roll
                existing.label_glue_grams_per_bottle = label_glue_grams_per_bottle
                existing.carton_glue_grams_per_carton = carton_glue_grams_per_carton
                existing.min_stock_units = min_stock_units
                existing.preform_material_id = preform_material_id
                existing.cap_material_id = cap_material_id
                existing.label_material_id = label_material_id
                existing.carton_material_id = carton_material_id
                existing.shrink_material_id = shrink_material_id
                existing.shrink_divider_material_id = shrink_divider_material_id
                existing.shrink_dividers_per_pallet = shrink_dividers_per_pallet
                existing.label_glue_material_id = label_glue_material_id
                existing.carton_glue_material_id = carton_glue_material_id
                existing.shrink_film_material_id = shrink_film_material_id
                existing.shrink_film_grams_per_pallet = shrink_film_grams_per_pallet
                existing.units_per_pallet = units_per_pallet
                existing.updated_at = datetime.now()
                session.commit()
                return existing.id
            else:
                detail = ProductBOMDetail(
                    company_id=company_id,
                    product_id=product_id,
                    preforms_per_unit=preforms_per_unit,
                    caps_per_unit=caps_per_unit,
                    labels_per_unit=labels_per_unit,
                    packaging_type=packaging_type,
                    units_per_carton=units_per_carton,
                    units_per_shrink=units_per_shrink,
                    shrink_pieces_per_roll=shrink_pieces_per_roll,
                    label_glue_grams_per_bottle=label_glue_grams_per_bottle,
                    carton_glue_grams_per_carton=carton_glue_grams_per_carton,
                    min_stock_units=min_stock_units,
                    preform_material_id=preform_material_id,
                    cap_material_id=cap_material_id,
                    label_material_id=label_material_id,
                    carton_material_id=carton_material_id,
                    shrink_material_id=shrink_material_id,
                    shrink_divider_material_id=shrink_divider_material_id,
                    shrink_dividers_per_pallet=shrink_dividers_per_pallet,
                    label_glue_material_id=label_glue_material_id,
                    carton_glue_material_id=carton_glue_material_id,
                    shrink_film_material_id=shrink_film_material_id,
                    shrink_film_grams_per_pallet=shrink_film_grams_per_pallet,
                    units_per_pallet=units_per_pallet
                )
                session.add(detail)
                session.commit()
                return detail.id
        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"create_product_bom_detail error: {e}")
            return None
        finally:
            if session:
                session.close()

    def convert_shrink_pieces_to_rolls(self, pieces_needed: int, material_id: int) -> tuple:
        """
        تحويل عدد قطع الشرنك المطلوبة إلى عدد رولات
        returns: (rolls_needed, pieces_per_roll)
        """
        session = None
        try:
            session = self.get_session()
            material = session.query(Material).filter(Material.id == material_id).first()
            if not material:
                return pieces_needed, 1  # افتراضي إذا لم توجد مادة
            
            pieces_per_roll = material.pieces_per_roll or 1980  # افتراضي 1980 إذا لم يُحدد
            rolls_needed = pieces_needed / pieces_per_roll
            return rolls_needed, pieces_per_roll
        except Exception as e:
            logger.error(f"convert_shrink_pieces_to_rolls error: {e}")
            return pieces_needed, 1980  # افتراضي في حالة الخطأ
        finally:
            if session:
                session.close()

    def get_companies_list(self, status: str = None) -> list:
        """الحصول على قائمة الشركات (لشاشة الدخول)"""
        session = None
        try:
            session = self.get_session()
            query = session.query(Company)
            if status:
                query = query.filter(Company.status == status)
            companies = query.order_by(Company.name_ar).all()
            return [{'id': c.id, 'name_ar': c.name_ar, 'name_en': c.name_en, 'code': c.code} for c in companies]
        except Exception as e:
            logger.error(f"get_companies_list error: {e}")
            return []
        finally:
            if session:
                session.close()

    def get_company_by_code(self, code: str):
        """الحصول على شركة عن طريق الكود"""
        session = None
        try:
            session = self.get_session()
            company = session.query(Company).filter(Company.code == code).first()
            if company:
                return {'id': company.id, 'name_ar': company.name_ar, 'name_en': company.name_en, 'code': company.code}
            return None
        except Exception as e:
            logger.error(f"get_company_by_code error: {e}")
            return None
        finally:
            if session:
                session.close()

    def create_line_product_speed(self, company_id: int, line_id: int, product_id: int, speed_per_hour: int) -> bool:
        """إنشاء سرعة إنتاج لمنتج على خط معين"""
        session = None
        try:
            session = self.get_session()
            existing = session.query(ProductLineSpeed).filter(
                ProductLineSpeed.company_id == company_id,
                ProductLineSpeed.production_line_id == line_id,
                ProductLineSpeed.product_id == product_id
            ).first()
            if existing:
                existing.speed_bottles_per_hour = speed_per_hour
                existing.updated_at = datetime.now()
            else:
                ls = ProductLineSpeed(
                    company_id=company_id,
                    production_line_id=line_id,
                    product_id=product_id,
                    speed_bottles_per_hour=speed_per_hour
                )
                session.add(ls)
            session.commit()
            return True
        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"create_line_product_speed error: {e}")
            return False
        finally:
            if session:
                session.close()

    def get_company_production_lines(self, company_id: int) -> list:
        """الحصول على خطوط الإنتاج لشركة"""
        session = None
        try:
            session = self.get_session()
            lines = session.query(ProductionLine).filter(
                ProductionLine.company_id == company_id,
                ProductionLine.status == 'active'
            ).all()
            return [{'id': l.id, 'name_ar': l.name_ar, 'name_en': l.name_en, 'code': l.code} for l in lines]
        except Exception as e:
            logger.error(f"get_company_production_lines error: {e}")
            return []
        finally:
            if session:
                session.close()

    def get_company_products(self, company_id: int) -> list:
        """الحصول على منتجات الشركة"""
        session = None
        try:
            session = self.get_session()
            products = session.query(Product).filter(
                Product.company_id == company_id,
                Product.is_active == True
            ).all()
            return [{'id': p.id, 'name_ar': p.name_ar, 'name_en': p.name_en, 'code': p.code, 'pieces_per_unit': p.pieces_per_unit} for p in products]
        except Exception as e:
            logger.error(f"get_company_products error: {e}")
            return []
        finally:
            if session:
                session.close()

    def get_company_materials(self, company_id: int) -> list:
        """الحصول على مواد خام الشركة"""
        session = None
        try:
            session = self.get_session()
            materials = session.query(Material).filter(
                Material.company_id == company_id,
                Material.is_active == True
            ).all()
            return [{'id': m.id, 'name_ar': m.name_ar, 'name_en': m.name_en, 'code': m.code, 'unit': m.unit, 'min_stock': m.min_stock} for m in materials]
        except Exception as e:
            logger.error(f"get_company_materials error: {e}")
            return []
        finally:
            if session:
                session.close()


# ============================================================================
# Global instance
# ============================================================================
db_manager = DatabaseManager()


# ============================================================================
# Compatibility functions
# ============================================================================

def init_database():
    pass

def save_production_to_db(data):
    return db_manager.save_production(data)

def save_maintenance_to_db(data):
    return db_manager.save_maintenance(data)

def save_delivery_to_db(data):
    return db_manager.save_delivery(data)

def save_raw_receipt_to_db(data):
    return db_manager.save_raw_receipt(data)

def load_all_production():
    return db_manager.get_all_production()

def load_all_maintenance():
    return db_manager.get_all_maintenance()

def load_all_delivery():
    return db_manager.get_all_delivery()

def delete_production_by_id(record_id):
    return db_manager.delete_production(record_id)

def delete_maintenance_record(record_id: int) -> bool:
    return db_manager.delete_maintenance(record_id)

def delete_delivery_record(record_id: int) -> bool:
    return db_manager.delete_delivery(record_id)

def delete_raw_receipt_record(record_id: int) -> bool:
    return db_manager.delete_raw_receipt(record_id)

def delete_company_record(company_id: int) -> bool:
    return db_manager.delete_company(company_id)