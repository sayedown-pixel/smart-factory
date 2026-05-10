import streamlit as st
import pandas as pd
import os
import requests
import urllib.parse
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

from config   import FACTORY_CONFIG as FC
from database import (
    save_production, save_maintenance,
    load_production, load_maintenance,
    delete_record, get_connection
)

# ============================================================
# 1. إعدادات الصفحة
# ============================================================
st.set_page_config(
    page_title=f"BIRMA | {FC['factory_name']}",
    page_icon="🏭",
    layout="wide"
)

# ============================================================
# 2. نظام اللغتين
# ============================================================
ln = st.sidebar.selectbox("🌐 Language / اللغة", ["ar", "en"], index=0)

LANG = {
    "ar": {
        "designer":     "م/ السيد عون",
        "menu":         ["📈 إدارة الإنتاج", "🔧 مركز الصيانة", "📊 السجلات والتقارير"],
        "line_label":   "خط العمل",
        "sup_label":    "اسم المشرف المسؤول",
        "prod_label":   "الصنف المنتج",
        "target_label": "الإنتاج الفعلي (وحدة)",
        "preform_label":"البريفورم المستخدم (قطعة)",
        "raw_label":    "خامة التغليف المستخدمة",
        "date_label":   "تاريخ الوردية",
        "maint_header": "🛠 مركز الصيانة",
        "maint_types":  ["صيانة دورية (Planned)", "بلاغ أعطال (Breakdown)"],
        "tech_label":   "الفني المسؤول",
        "issue_label":  "وصف العطل",
        "start_t":      "بداية التوقف",
        "end_t":        "نهاية الإصلاح",
        "note_label":   "ملاحظات إضافية",
        "save_btn":     "💾 حفظ وإرسال إشعار",
        "success_msg":  "✅ تم الحفظ وإرسال التنبيه بنجاح",
        "eff_title":    "متوسط الكفاءة %",
        "waste_title":  "تحليل الهالك تاريخياً",
        "history_p":    "سجل الإنتاج",
        "history_m":    "سجل الصيانة",
        "admin_title":  "🔒 لوحة التحكم (للمشرف)",
        "del_prod":     "حذف من الإنتاج",
        "del_maint":    "حذف من الصيانة",
        "del_success":  "🗑 تم الحذف بنجاح",
        "tools_label":  "🔧 الأدوات:",
        "proc_label":   "📜 معيار العمل/التنظيف:",
        "weekend_msg":  "🏖 اليوم جمعة - لا توجد صيانات دورية مجدولة.",
        "no_file":      "⚠️ ملف الصيانة غير موجود:",
        "no_data":      "لا توجد بيانات بعد.",
    },
    "en": {
        "designer":     "Eng. Elsayed Aoun",
        "menu":         ["📈 Production Management", "🔧 Maintenance Center", "📊 Records & Reports"],
        "line_label":   "Working Line",
        "sup_label":    "Supervisor Name",
        "prod_label":   "Product Type",
        "target_label": "Actual Output (Units)",
        "preform_label":"Preforms Used (pcs)",
        "raw_label":    "Raw Packaging Used",
        "date_label":   "Shift Date",
        "maint_header": "🛠 Maintenance Center",
        "maint_types":  ["Planned Maintenance", "Breakdown"],
        "tech_label":   "Technician Name",
        "issue_label":  "Issue Description",
        "start_t":      "Downtime Start",
        "end_t":        "Repair End",
        "note_label":   "Additional Notes",
        "save_btn":     "💾 Save & Send Alert",
        "success_msg":  "✅ Saved & Notified Successfully",
        "eff_title":    "Average Efficiency %",
        "waste_title":  "Historical Waste Analysis",
        "history_p":    "Production Logs",
        "history_m":    "Maintenance Logs",
        "admin_title":  "🔒 Admin Panel",
        "del_prod":     "Delete from Production",
        "del_maint":    "Delete from Maintenance",
        "del_success":  "🗑 Deleted Successfully",
        "tools_label":  "🔧 Tools:",
        "proc_label":   "📜 Cleaning/Work Standard:",
        "weekend_msg":  "🏖 Friday - No scheduled maintenance.",
        "no_file":      "⚠️ Maintenance file not found:",
        "no_data":      "No data yet.",
    }
}

L = LANG[ln]

# ============================================================
# 3. الشعار والهوية
# ============================================================
st.sidebar.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
logo = FC.get("factory_logo", "")
if logo and os.path.exists(logo):
    st.sidebar.image(logo, use_container_width=True)
else:
    st.sidebar.markdown(
        f"<h2 style='color:#0047AB;text-align:center;'>{FC['factory_name']}</h2>",
        unsafe_allow_html=True
    )
st.sidebar.markdown("</div>", unsafe_allow_html=True)
st.sidebar.caption(f"📍 {FC['factory_city']}")
st.sidebar.divider()
st.sidebar.markdown(
    f"<p style='text-align:center;font-size:11px;color:gray;'>Designed by:</p>"
    f"<h4 style='text-align:center;color:#2E8B57;margin-top:0;'>{L['designer']}</h4>",
    unsafe_allow_html=True
)
st.sidebar.divider()

# ============================================================
# 4. التيليجرام
# ============================================================
def send_telegram(msg: str):
    try:
        token   = FC["telegram_token"]
        chat_id = FC["telegram_chat"]
        url = (
            f"https://api.telegram.org/bot{token}/sendMessage"
            f"?chat_id={chat_id}"
            f"&text={urllib.parse.quote(msg)}"
            f"&parse_mode=Markdown"
        )
        requests.get(url, timeout=5)
    except:
        pass

# ============================================================
# 5. جدولة الصيانة الذكية
# ============================================================
def get_scheduled_tasks(df: pd.DataFrame) -> pd.DataFrame:
    today    = datetime.now()
    day_name = today.strftime('%A')
    is_first = (today.day == 1)

    if day_name == 'Friday':
        return pd.DataFrame()

    allowed = ['Daily']
    if day_name == 'Saturday':
        allowed.append('Weekly')
    if is_first:
        allowed.append('Monthly')

    return df[df['Freq'].isin(allowed)]

# ============================================================
# 6. القائمة الرئيسية
# ============================================================
selected_menu = st.sidebar.selectbox("Menu", L["menu"])
selected_line = st.sidebar.radio(L["line_label"], list(FC["lines"].keys()))
line_cfg      = FC["lines"][selected_line]

# ──────────────────────────────────────────────────────────
# أ. الإنتاج
# ──────────────────────────────────────────────────────────
if selected_menu == L["menu"][0]:
    st.header(f"{L['menu'][0]} — {selected_line}")

    with st.form("prod_form"):
        c1, c2 = st.columns(2)
        with c1:
            name    = st.text_input(L["sup_label"])
            product = st.selectbox(L["prod_label"], line_cfg["products"])
            target  = st.number_input(L["target_label"], min_value=0)
        with c2:
            preforms = st.number_input(L["preform_label"], min_value=0)
            raw_type = "Carton" if "Carton" in product else "Shrink"
            raw_val  = st.number_input(f"{L['raw_label']} ({raw_type})", min_value=0.0)
            p_date   = st.date_input(L["date_label"])

        if st.form_submit_button(L["save_btn"]):
            bpu     = line_cfg["bottles_per_unit"][product]
            total_b = target * bpu
            speed   = line_cfg["speed_per_shift"][product]
            eff     = round((total_b / speed) * 100, 1) if speed else 0

            save_production({
                "factory":       FC["factory_name"],
                "line":          selected_line,
                "date":          str(p_date),
                "staff":         name,
                "product":       product,
                "output_units":  target,
                "waste_bottles": preforms - total_b,
                "waste_raw":     raw_val - target,
                "efficiency_pct":eff,
                "timestamp":     datetime.now().strftime("%H:%M"),
            })

            send_telegram(
                f"🚀 *إنتاج جديد*\n"
                f"المصنع: {FC['factory_name']}\n"
                f"الخط: {selected_line}\n"
                f"الصنف: {product}\n"
                f"الإنتاج: {target:,} وحدة\n"
                f"الكفاءة: {eff}%\n"
                f"الهالك: {preforms - total_b:,} زجاجة"
            )
            st.success(L["success_msg"])
            st.rerun()

# ──────────────────────────────────────────────────────────
# ب. الصيانة
# ──────────────────────────────────────────────────────────
elif selected_menu == L["menu"][1]:
    st.header(L["maint_header"])
    m_type  = st.radio("Type", L["maint_types"], horizontal=True)
    machine = st.sidebar.selectbox("Machine", list(FC["machines"].keys()))

    # صيانة دورية
    if m_type == L["maint_types"][0]:
        path = FC["machines"][machine]
        if not os.path.exists(path):
            st.error(f"{L['no_file']} `{path}`")
        else:
            df_raw = pd.read_excel(path, skiprows=2)
            df_raw.columns = ['Cat','No','Name','Photo','Tools','Proc','Freq','Stat','Note','Staff']
            scheduled = get_scheduled_tasks(df_raw)

            if scheduled.empty:
                st.warning(L["weekend_msg"])
            else:
                with st.form("m_form"):
                    tech = st.text_input(L["tech_label"])
                    recs = []
                    for i, r in scheduled.iterrows():
                        st.divider()
                        ci, cp = st.columns([2, 1])
                        with ci:
                            st.markdown(f"### 🔧 {r['Name']}  `{r['Freq']}`")
                            st.markdown(f"**{L['tools_label']}** `{r['Tools'] if pd.notna(r['Tools']) else 'N/A'}`")
                            st.info(f"**{L['proc_label']}**\n{r['Proc'] if pd.notna(r['Proc']) else 'N/A'}")
                            ok   = st.checkbox(f"✅ DONE — {r['Name']}", key=f"k{i}")
                            note = st.text_input(L["note_label"], key=f"n{i}")
                        with cp:
                            img = os.path.join("images", str(r['Photo']).strip())
                            if os.path.exists(img):
                                st.image(img, use_container_width=True)
                        if ok:
                            recs.append({
                                "type":        "Planned",
                                "factory":     FC["factory_name"],
                                "line":        selected_line,
                                "date":        str(datetime.now().date()),
                                "machine":     machine,
                                "task":        r['Name'],
                                "staff":       tech,
                                "notes":       note,
                                "downtime_min":0,
                            })

                    if st.form_submit_button(L["save_btn"]) and recs:
                        for rec in recs:
                            save_maintenance(rec)
                        send_telegram(
                            f"🔧 *صيانة دورية*\n"
                            f"المصنع: {FC['factory_name']}\n"
                            f"الماكينة: {machine}\n"
                            f"المهام المنجزة: {len(recs)}\n"
                            f"الفني: {tech}"
                        )
                        st.success(L["success_msg"])
                        st.rerun()

    # أعطال
    else:
        with st.form("break_form"):
            t_name = st.text_input(L["tech_label"])
            issue  = st.text_area(L["issue_label"])
            col1, col2 = st.columns(2)
            t1 = col1.time_input(L["start_t"])
            t2 = col2.time_input(L["end_t"])
            m_note = st.text_area(L["note_label"])

            if st.form_submit_button(L["save_btn"]):
                duration = (
                    datetime.combine(datetime.today(), t2) -
                    datetime.combine(datetime.today(), t1)
                ).seconds // 60

                save_maintenance({
                    "type":        "Breakdown",
                    "factory":     FC["factory_name"],
                    "line":        selected_line,
                    "date":        str(datetime.now().date()),
                    "machine":     machine,
                    "task":        issue,
                    "staff":       t_name,
                    "notes":       f"{t1}→{t2} | {m_note}",
                    "downtime_min":duration,
                })
                send_telegram(
                    f"⚠️ *عطل جديد!*\n"
                    f"المصنع: {FC['factory_name']}\n"
                    f"الماكينة: {machine}\n"
                    f"الفني: {t_name}\n"
                    f"العطل: {issue}\n"
                    f"مدة التوقف: {duration} دقيقة"
                )
                st.success(L["success_msg"])
                st.rerun()

# ──────────────────────────────────────────────────────────
# ج. السجلات والتقارير
# ──────────────────────────────────────────────────────────
elif selected_menu == L["menu"][2]:
    st.header(L["menu"][2])

    prod_data  = load_production(30)
    maint_data = load_maintenance(30)

    if prod_data.empty:
        st.info(L["no_data"])
    else:
        g1, g2, g3 = st.columns(3)

        avg_eff = prod_data['efficiency_pct'].mean()
        with g1:
            fig = go.Figure(go.Indicator(
                mode  = "gauge+number",
                value = avg_eff,
                title = {'text': L["eff_title"]},
                gauge = {
                    'axis':  {'range': [0, 100]},
                    'bar':   {'color': "#2E8B57"},
                    'steps': [
                        {'range': [0,  60],  'color': "#ffcccc"},
                        {'range': [60, 80],  'color': "#fff3cd"},
                        {'range': [80, 100], 'color': "#d4edda"},
                    ],
                }
            ))
            st.plotly_chart(fig, use_container_width=True)

        with g2:
            st.metric("📦 إجمالي الوحدات", f"{int(prod_data['output_units'].sum()):,}")
            st.metric("🗑 إجمالي الهالك",   f"{int(prod_data['waste_bottles'].sum()):,} زجاجة")

        with g3:
            if not maint_data.empty:
                breakdowns = maint_data[maint_data['type'] == 'Breakdown']
                total_down = breakdowns['downtime_min'].sum() if not breakdowns.empty else 0
                st.metric("⏱ إجمالي التوقفات", f"{int(total_down)} دقيقة")
                st.metric("🔧 بلاغات أعطال",    f"{len(breakdowns)} بلاغ")

        # رسم الهالك
        fig_b = px.bar(
            prod_data, x='date', y='waste_bottles',
            color='product', title=L["waste_title"],
            labels={'waste_bottles': 'هالك (زجاجة)', 'date': 'التاريخ'}
        )
        st.plotly_chart(fig_b, use_container_width=True)

        # رسم التوقفات
        if not maint_data.empty:
            fig_d = px.bar(
                maint_data[maint_data['type']=='Breakdown'],
                x='date', y='downtime_min', color='machine',
                title="⏱ التوقفات بالدقيقة",
                labels={'downtime_min': 'دقائق', 'date': 'التاريخ'}
            )
            st.plotly_chart(fig_d, use_container_width=True)

    tab1, tab2 = st.tabs([L["history_p"], L["history_m"]])
    with tab1:
        st.dataframe(prod_data, use_container_width=True)
    with tab2:
        st.dataframe(maint_data, use_container_width=True)

# ============================================================
# 7. لوحة تحكم المشرف
# ============================================================
st.sidebar.divider()
with st.sidebar.expander(L["admin_title"]):
    pw = st.text_input("Password", type="password")
    if pw == FC["admin_password"]:
        st.success("✅ مرحباً بالمشرف")

        prod_data  = load_production(50)
        maint_data = load_maintenance(50)

        st.markdown("**حذف من الإنتاج:**")
        if not prod_data.empty:
            row_p = st.selectbox("ID الإنتاج", prod_data['id'].tolist(), key="del_p")
            if st.button(L["del_prod"]):
                delete_record("production", row_p)
                st.success(L["del_success"])
                st.rerun()

        st.markdown("**حذف من الصيانة:**")
        if not maint_data.empty:
            row_m = st.selectbox("ID الصيانة", maint_data['id'].tolist(), key="del_m")
            if st.button(L["del_maint"]):
                delete_record("maintenance", row_m)
                st.success(L["del_success"])
                st.rerun()

# ============================================================
# Footer
# ============================================================
st.markdown(
    f"<br><hr><center><p style='color:gray;'>"
    f"BIRMA v7.0 | {FC['factory_name']} | "
    f"<b>Designed by: {L['designer']}</b>"
    f"</p></center>",
    unsafe_allow_html=True
)
