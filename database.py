# ============================================================
#  BIRMA - مدير قاعدة البيانات SQLite
#  Designed by: م/ السيد عون
# ============================================================

import sqlite3
import pandas as pd
import os

DB_PATH = os.path.join("data", "birma.db")

def get_connection():
    os.makedirs("data", exist_ok=True)
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    _create_tables(con)
    return con

def _create_tables(con):
    con.executescript("""
        CREATE TABLE IF NOT EXISTS production (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            type            TEXT DEFAULT 'Production',
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
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            type    TEXT,
            line    TEXT,
            date    TEXT,
            machine TEXT,
            task    TEXT,
            staff   TEXT,
            notes   TEXT
        );
    """)
    con.commit()

# ── إنتاج ──
def save_production(row: dict):
    con = get_connection()
    con.execute("""
        INSERT INTO production
            (type,line,date,staff,product,output_units,waste_bottles,waste_raw,efficiency_pct,timestamp)
        VALUES
            (:type,:line,:date,:staff,:product,:output_units,:waste_bottles,:waste_raw,:efficiency_pct,:timestamp)
    """, row)
    con.commit()

def load_production_10days() -> pd.DataFrame:
    con = get_connection()
    return pd.read_sql("""
        SELECT * FROM production
        WHERE date >= date('now','-10 days')
        ORDER BY date DESC, id DESC
    """, con)

# ── صيانة ──
def save_maintenance(row: dict):
    con = get_connection()
    con.execute("""
        INSERT INTO maintenance
            (type,line,date,machine,task,staff,notes)
        VALUES
            (:type,:line,:date,:machine,:task,:staff,:notes)
    """, row)
    con.commit()

def load_maintenance_10days() -> pd.DataFrame:
    con = get_connection()
    return pd.read_sql("""
        SELECT * FROM maintenance
        WHERE date >= date('now','-10 days')
        ORDER BY date DESC, id DESC
    """, con)

# ── حذف ──
def delete_production(record_id: int):
    con = get_connection()
    con.execute("DELETE FROM production WHERE id=?", (record_id,))
    con.commit()

def delete_maintenance(record_id: int):
    con = get_connection()
    con.execute("DELETE FROM maintenance WHERE id=?", (record_id,))
    con.commit()

# ── للرسوم البيانية (آخر 15 سجل) ──
def load_production_chart() -> pd.DataFrame:
    con = get_connection()
    return pd.read_sql("""
        SELECT * FROM production
        ORDER BY id DESC LIMIT 15
    """, con)
