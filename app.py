import streamlit as st
import pandas as pd
import os
import requests
import urllib.parse
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

from database import (
    save_production, load_production_10days, load_production_chart,
    save_maintenance, load_maintenance_10days,
    delete_production, delete_maintenance
)

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="BIRMA Integrated System", page_icon="🏭", layout="wide")

# --- 2. نظام اللغات ---
ln = st.sidebar.selectbox("🌐 Language / اللغة", ["ar", "en"], index=0)

LANG = {
    "ar": {
        "designer":     "م/ السيد عون",
        "menu":         ["📈 إدارة الإنتاج", "🔧 مركز الصيانة المتكامل", "📊 السجلات والتقارير"],
        "line_label":   "خط العمل",
        "sup_label":    "اسم المشرف المسؤول",
        "prod_label":   "الصنف المنتج",
        "target_label": "الإنتاج الفعلي (وحدة)",
        "preform_label":"البريفورم المستخدم (قطعة)",
        "raw_label":    "خامة التغليف المستخدمة",
        "date_label":   "تاريخ الوردية",
        "maint_header": "🛠 مركز صيانة",
        "maint_types":  ["صيانة دورية (Planned)", "بلاغ أعطال (Breakdown)"],
        "tech_label":   "الفني المسؤول",
        "issue_label":  "وصف العطل",
        "start_t":      "بداية التوقف",
        "end_t":        "نهاية الإصلاح",
        "note_label":   "ملاحظات إضافية",
        "save_btn":     "💾 حفظ البيانات وإرسال إشعار",
        "success_msg":  "✅ تم الحفظ وإرسال التنبيه بنجاح",
        "eff_title":    "متوسط الكفاءة %",
        "waste_title":  "تحليل الهالك تاريخياً",
        "history_p":    "📋 سجل الإنتاج (10 أيام)",
        "history_m":    "🔧 سجل الصيانة (10 أيام)",
        "admin_title":  "🔒 لوحة التحكم (للمشرف)",
        "delete_btn":   "🗑 حذف السجل المختار",
        "del_success":  "🗑 تم حذف السجل بنجاح",
        "tools_label":  "🔧 الأدوات:",
        "proc_label":   "📜 معيار العمل/التنظيف:",
        "weekend_msg":  "🏖 اليوم الجمعة عطلة نهاية الأسبوع - لا توجد صيانات دورية مجدولة.",
        "no_data":      "لا توجد بيانات في آخر 10 أيام",
        "del_prod_title":"حذف من سجل الإنتاج",
        "del_maint_title":"حذف من سجل الصيانة",
        "select_row":   "اختار السجل للحذف",
        "no_file":      "⚠️ ملف الصيانة غير موجود:",
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
        "history_p":    "📋 Production Log (10 Days)",
        "history_m":    "🔧 Maintenance Log (10 Days)",
        "admin_title":  "🔒 Admin Panel",
        "delete_btn":   "🗑 Delete Selected Record",
        "del_success":  "🗑 Record Deleted Successfully",
        "tools_label":  "🔧 Tools:",
        "proc_label":   "📜 Cleaning/Work Standard:",
        "weekend_msg":  "🏖 Today is Friday (Weekend) - No scheduled maintenance.",
        "no_data":      "No data in the last 10 days",
        "del_prod_title":"Delete from Production Log",
        "del_maint_title":"Delete from Maintenance Log",
        "select_row":   "Select record to delete",
        "no_file":      "⚠️ Maintenance file not found:",
    }
}

L = LANG[ln]

# --- 3. الهوية والشعار ---
st.sidebar.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
if os.path.exists("birma mark.png"):
    st.sidebar.image("birma mark.png", use_container_width=True)
else:
    st.sidebar.markdown("<h1 style='color:#0047AB;'>BIRMA</h1>", unsafe_allow_html=True)
st.sidebar.markdown("</div>", unsafe_allow_html=True)
st.sidebar.divider()
st.sidebar.markdown(f"<p style='text-align:center;font-size:12px;color:gray;margin-bottom:0;'>Designed by:</p>", unsafe_allow_html=True)
st.sidebar.markdown(f"<h3 style='text-align:center;color:#2E8B57;margin-top:0;'>{L['designer']}</h3>", unsafe_allow_html=True)
st.sidebar.divider()

# --- 4. التيليجرام ---
def send_telegram(msg):
    try:
        token   = st.secrets["telegram"]["bot_token"]
        chat_id = st.secrets["telegram"]["chat_id"]
        requests.get(
            f"https://api.telegram.org/bot{token}/sendMessage"
            f"?chat_id={chat_id}&text={urllib.parse.quote(msg)}&parse_mode=Markdown",
            timeout=5
        )
    except:
        pass

# --- 5. جدولة الصيانة ---
def get_scheduled_tasks(df_tasks):
    today = datetime.now()
    day_name = today.strftime('%A')
    if day_name == 'Friday':
        return pd.DataFrame()
    allowed_freqs = ['Daily']
    if day_name == 'Saturday':
        allowed_freqs.append('Weekly')
    if today.day == 1:
        allowed_freqs.append('Monthly')
    return df_tasks[df_tasks['Freq'].isin(allowed_freqs)]

# --- الثوابت الفنية ---
CONFIG = {
    "الخط الأول(smi)": {
        "الأصناف": ["200 ml Carton", "200 ml Shrink", "600 ml Carton", "1.5 L Shrink"],
        "العبوات": {"200 ml Carton": 48, "200 ml Shrink": 20, "600 ml Carton": 30, "1.5 L Shrink": 6},
        "السرعة":  {"200 ml Carton": 35000, "200 ml Shrink": 35000, "600 ml Carton": 20000, "1.5 L Shrink": 12000}
    },
    "الخط الثاني(welbing)": {
        "الأصناف": ["200 ml Carton", "200 ml Shrink", "330 ml Carton", "331 ml Shrink"],
        "العبوات": {"200 ml Carton": 48, "200 ml Shrink": 20, "330 ml Carton": 40, "331 ml Shrink": 20},
        "السرعة":  {"200 ml Carton": 40000, "200 ml Shrink": 40000, "330 ml Carton": 40000, "331 ml Shrink": 40000}
    }
}

MACHINE_MAP = {
    "النفخ(blowing)":        "blowing_machine.xlsx",
    "الليبل(labeling)":      "labeling_machine.xlsx",
    "السيور(Conveyor)":      "Conveyor_machine.xlsx",
    "الكرتون(packing)":      "packing_machine.xlsx",
    "البالتايزر(paletizer)": "paletizer_machine.xlsx",
    "الشرنك(shrink)":        "shrink_machine.xlsx",
    "التعبئة(filling)":      "Filling_machine.xlsx"
}

# --- 6. واجهة المستخدم ---
selected_menu = st.sidebar.selectbox("Menu", L["menu"])
selected_line = st.sidebar.radio(L["line_label"], list(CONFIG.keys()))

# ══ أ. الإنتاج ══
if selected_menu == L["menu"][0]:
    st.header(f"{L['menu'][0]} - {selected_line}")
    with st.form("prod_form"):
        c1, c2 = st.columns(2)
        with c1:
            name    = st.text_input(L["sup_label"])
            product = st.selectbox(L["prod_label"], CONFIG[selected_line]["الأصناف"])
            target  = st.number_input(L["target_label"], min_value=0)
        with c2:
            preforms = st.number_input(L["preform_label"], min_value=0)
            raw_type = "Carton" if "Carton" in product else "Shrink"
            raw_val  = st.number_input(f"{L['raw_label']} ({raw_type})", min_value=0)
            p_date   = st.date_input(L["date_label"])

        if st.form_submit_button(L["save_btn"]):
            b_per_u = CONFIG[selected_line]["العبوات"][product]
            total_b = target * b_per_u
            eff     = round((total_b / (CONFIG[selected_line]["السرعة"][product] * 15)) * 100, 1)
            save_production({
                "type":          "Production",
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
                f"🚀 *Production Update*\n"
                f"Line: {selected_line}\nProduct: {product}\n"
                f"Output: {target:,}\nEff: {eff}%"
            )
            st.success(L["success_msg"])
            st.rerun()

# ══ ب. الصيانة ══
elif selected_menu == L["menu"][1]:
    st.header(L["maint_header"])
    m_type  = st.radio("Type", L["maint_types"], horizontal=True)
    machine = st.sidebar.selectbox("Machine", list(MACHINE_MAP.keys()))

    if m_type == L["maint_types"][0]:
        path = MACHINE_MAP[machine]
        if os.path.exists(path):
            df_raw = pd.read_excel(path, skiprows=2)
            df_raw.columns = ['Cat','No','Name','Photo','Tools','Proc','Freq','Stat','Note','Staff']
            scheduled_tasks = get_scheduled_tasks(df_raw)

            if scheduled_tasks.empty:
                st.warning(L["weekend_msg"])
            else:
                with st.form("m_form"):
                    tech = st.text_input(L["tech_label"])
                    recs = []
                    for i, r in scheduled_tasks.iterrows():
                        st.divider()
                        c_i, c_p = st.columns([2, 1])
                        with c_i:
                            st.markdown(f"### 🔧 {r['Name']} ({r['Freq']})")
                            st.markdown(f"**{L['tools_label']}** `{r['Tools'] if pd.notna(r['Tools']) else 'N/A'}`")
                            st.info(f"**{L['proc_label']}**\n{r['Proc'] if pd.notna(r['Proc']) else 'N/A'}")
                            ok   = st.checkbox(f"DONE - {r['Name']}", key=f"k{i}")
                            note = st.text_input(L["note_label"], key=f"n{i}")
                        with c_p:
                            img = os.path.join("images", str(r['Photo']).strip())
                            if os.path.exists(img):
                                st.image(img, use_container_width=True)
                        if ok:
                            recs.append({
                                "type":    "Maint_Daily",
                                "line":    selected_line,
                                "date":    str(datetime.now().date()),
                                "machine": machine,
                                "task":    r['Name'],
                                "staff":   tech,
                                "notes":   note,
                            })
                    if st.form_submit_button(L["save_btn"]):
                        for rec in recs:
                            save_maintenance(rec)
                        st.success(L["success_msg"])
                        st.rerun()
        else:
            st.error(f"{L['no_file']} `{path}`")

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
                    "type":    "Maint_Breakdown",
                    "line":    selected_line,
                    "date":    str(datetime.now().date()),
                    "machine": machine,
                    "task":    issue,
                    "staff":   t_name,
                    "notes":   f"{t1}→{t2} ({duration} دقيقة) | {m_note}",
                })
                send_telegram(
                    f"⚠️ *Breakdown*\nMachine: {machine}\n"
                    f"Tech: {t_name}\nIssue: {issue}\n"
                    f"Downtime: {duration} min"
                )
                st.success(L["success_msg"])
                st.rerun()

# ══ ج. السجلات والتقارير ══
elif selected_menu == L["menu"][2]:
    st.header(L["menu"][2])

    # الرسوم البيانية
    chart_data = load_production_chart()
    if not chart_data.empty:
        g1, g2 = st.columns(2)
        with g1:
            fig_g = go.Figure(go.Indicator(
                mode  = "gauge+number",
                value = chart_data['efficiency_pct'].mean(),
                title = {'text': L["eff_title"]},
                gauge = {
                    'axis':  {'range': [0, 100]},
                    'bar':   {'color': '#2E8B57'},
                    'steps': [
                        {'range': [0,  60],  'color': '#ffcccc'},
                        {'range': [60, 80],  'color': '#fff3cd'},
                        {'range': [80, 100], 'color': '#d4edda'},
                    ]
                }
            ))
            st.plotly_chart(fig_g, use_container_width=True)
        with g2:
            fig_b = px.bar(
                chart_data, x='date', y='waste_bottles',
                color='product', title=L["waste_title"]
            )
            st.plotly_chart(fig_b, use_container_width=True)

    st.divider()

    # السجلات
    tab1, tab2 = st.tabs([L["history_p"], L["history_m"]])

    # ── سجل الإنتاج ──
    with tab1:
        prod_10 = load_production_10days()
        if prod_10.empty:
            st.info(L["no_data"])
        else:
            st.dataframe(prod_10, use_container_width=True, hide_index=True)
            st.markdown(f"#### {L['del_prod_title']}")
            options_p = {
                f"[{r['id']}]  {r['date']}  |  {r['line']}  |  {r['product']}  |  {r['output_units']:,} وحدة": r['id']
                for _, r in prod_10.iterrows()
            }
            sel_p = st.selectbox(L["select_row"], list(options_p.keys()), key="sel_p")
            if st.button(L["delete_btn"], key="btn_del_p"):
                delete_production(options_p[sel_p])
                st.success(L["del_success"])
                st.rerun()

    # ── سجل الصيانة ──
    with tab2:
        maint_10 = load_maintenance_10days()
        if maint_10.empty:
            st.info(L["no_data"])
        else:
            st.dataframe(maint_10, use_container_width=True, hide_index=True)
            st.markdown(f"#### {L['del_maint_title']}")
            options_m = {
                f"[{r['id']}]  {r['date']}  |  {r['machine']}  |  {r['type']}  |  {r['staff']}": r['id']
                for _, r in maint_10.iterrows()
            }
            sel_m = st.selectbox(L["select_row"], list(options_m.keys()), key="sel_m")
            if st.button(L["delete_btn"], key="btn_del_m"):
                delete_maintenance(options_m[sel_m])
                st.success(L["del_success"])
                st.rerun()

# --- لوحة تحكم المشرف ---
st.sidebar.divider()
with st.sidebar.expander(L["admin_title"]):
    pw = st.text_input("Password", type="password")
    if pw == "admin123":
        st.success("✅ مرحباً بالمشرف")
        st.markdown("**حذف من الإنتاج:**")
        prod_all = load_production_10days()
        if not prod_all.empty:
            opts_ap = {
                f"[{r['id']}] {r['date']} | {r['product']}": r['id']
                for _, r in prod_all.iterrows()
            }
            sel_ap = st.selectbox("إنتاج", list(opts_ap.keys()), key="adm_p")
            if st.button(L["delete_btn"], key="adm_del_p"):
                delete_production(opts_ap[sel_ap])
                st.success(L["del_success"])
                st.rerun()

        st.markdown("**حذف من الصيانة:**")
        maint_all = load_maintenance_10days()
        if not maint_all.empty:
            opts_am = {
                f"[{r['id']}] {r['date']} | {r['machine']}": r['id']
                for _, r in maint_all.iterrows()
            }
            sel_am = st.selectbox("صيانة", list(opts_am.keys()), key="adm_m")
            if st.button(L["delete_btn"], key="adm_del_m"):
                delete_maintenance(opts_am[sel_am])
                st.success(L["del_success"])
                st.rerun()

st.markdown(
    f"<br><hr><center><p style='color:gray;'>BIRMA v6.2 | "
    f"<b>Designed by: {L['designer']}</b></p></center>",
    unsafe_allow_html=True
)
