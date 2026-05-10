# ============================================================
#  BIRMA SaaS - مدير قاعدة البيانات SQLite
#  كل مصنع له ملف .db منفصل = عزل تام
#  Designed by: م/ السيد عون
# ============================================================

import sqlite3
import pandas as pd
import os
from config import FACTORY_CONFIG as FC

# مسار قاعدة البيانات - اسمها من config
DB_PATH = os.path.join("data", f"{FC['db_name']}.db")

def get_connection():
    """فتح اتصال بقاعدة البيانات وإنشاء الجداول لو مش موجودة"""
    os.makedirs("data", exist_ok=True)
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    _create_tables(con)
    return con

def _create_tables(con):
    """إنشاء الجداول عند أول تشغيل"""
    con.executescript("""
        CREATE TABLE IF NOT EXISTS production (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            factory         TEXT,
            line            TEXT,
            date            TEXT,
            staff           TEXT,
            product         TEXT,
            output_units    INTEGER,
            waste_bottles   INTEGER,
            waste_raw       REAL,
            efficiency_pct  REAL,
            timestamp       TEXT
        );

        CREATE TABLE IF NOT EXISTS maintenance (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            type        TEXT,   -- Planned | Breakdown
            factory     TEXT,
            line        TEXT,
            date        TEXT,
            machine     TEXT,
            task        TEXT,
            staff       TEXT,
            notes       TEXT,
            downtime_min INTEGER DEFAULT 0
        );
    """)
    con.commit()

# ──────────────────────────────────────────────────────────
# قراءة البيانات
# ──────────────────────────────────────────────────────────

def load_production(limit=30) -> pd.DataFrame:
    con = get_connection()
    return pd.read_sql(
        f"SELECT * FROM production ORDER BY id DESC LIMIT {limit}",
        con
    )

def load_maintenance(limit=30) -> pd.DataFrame:
    con = get_connection()
    return pd.read_sql(
        f"SELECT * FROM maintenance ORDER BY id DESC LIMIT {limit}",
        con
    )

# ──────────────────────────────────────────────────────────
# حفظ البيانات
# ──────────────────────────────────────────────────────────

def save_production(row: dict):
    con = get_connection()
    con.execute("""
        INSERT INTO production
            (factory, line, date, staff, product,
             output_units, waste_bottles, waste_raw,
             efficiency_pct, timestamp)
        VALUES
            (:factory, :line, :date, :staff, :product,
             :output_units, :waste_bottles, :waste_raw,
             :efficiency_pct, :timestamp)
    """, row)
    con.commit()

def save_maintenance(row: dict):
    con = get_connection()
    con.execute("""
        INSERT INTO maintenance
            (type, factory, line, date, machine,
             task, staff, notes, downtime_min)
        VALUES
            (:type, :factory, :line, :date, :machine,
             :task, :staff, :notes, :downtime_min)
    """, row)
    con.commit()

# ──────────────────────────────────────────────────────────
# حذف سجل (للمشرف)
# ──────────────────────────────────────────────────────────

def delete_record(table: str, record_id: int):
    """table = 'production' أو 'maintenance'"""
    con = get_connection()
    con.execute(f"DELETE FROM {table} WHERE id = ?", (record_id,))
    con.commit()
