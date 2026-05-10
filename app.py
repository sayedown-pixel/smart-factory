import streamlit as st
import pandas as pd
import os
import requests
import urllib.parse
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection
import plotly.graph_objects as go
import plotly.express as px
from sklearn.linear_model import LinearRegression

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="BIRMA Integrated System", page_icon="🏭", layout="wide")

# --- 2. نظام اللغات ---
if 'lang' not in st.session_state:
    st.session_state.lang = 'ar'

ln = st.sidebar.selectbox("🌐 Language / اللغة", ["ar", "en"], index=0)

LANG = {
    "ar": {
        "designer": "م/ السيد عون",
        "menu": ["📈 إدارة الإنتاج", "🔧 مركز الصيانة المتكامل", "📊 السجلات والتقارير"],
        "line_label": "خط العمل",
        "sup_label": "اسم المشرف المسؤول",
        "prod_label": "الصنف المنتج",
        "target_label": "الإنتاج الفعلي (وحدة)",
        "preform_label": "البريفورم المستخدم (قطعة)",
        "raw_label": "خامة التغليف المستخدمة",
        "date_label": "تاريخ الوردية",
        "maint_header": "🛠 مركز صيانة",
        "maint_types": ["صيانة دورية (Planned)", "بلاغ أعطال (Breakdown)"],
        "tech_label": "الفني المسؤول",
        "issue_label": "وصف العطل",
        "start_t": "بداية التوقف",
        "end_t": "نهاية الإصلاح",
        "note_label": "ملاحظات إضافية",
        "save_btn": "حفظ البيانات وإرسال إشعار",
        "success_msg": "✅ تم الحفظ وإرسال التنبيه بنجاح",
        "eff_title": "متوسط الكفاءة %",
        "waste_title": "تحليل الهالك تاريخياً",
        "history_p": "📋 سجل الإنتاج (10 أيام)",
        "history_m": "🔧 سجل الصيانة (10 أيام)",
        "admin_title": "🔒 لوحة التحكم (للمشرف)",
        "delete_btn": "🗑 حذف السجل المختار",
        "del_success": "🗑 تم حذف السجل بنجاح",
        "tools_label": "🔧 الأدوات:",
        "proc_label": "📜 معيار العمل/التنظيف:",
        "weekend_msg": "🏖 اليوم الجمعة عطلة نهاية الأسبوع - لا توجد صيانات دورية مجدولة.",
        "no_data": "لا توجد بيانات في آخر 10 أيام",
        "del_prod_title": "حذف من سجل الإنتاج",
        "del_maint_title": "حذف من سجل الصيانة",
        "select_row": "اختار السجل للحذف",
        "confirm_del": "⚠️ هل أنت متأكد من الحذف؟",
    },
    "en": {
        "designer": "Eng. Elsayed Aoun",
        "menu": ["📈 Production Management", "🔧 Maintenance Center", "📊 Records & Reports"],
        "line_label": "Working Line",
        "sup_label": "Supervisor Name",
        "prod_label": "Product Type",
        "target_label": "Actual Output (Units)",
        "preform_label": "Preforms Used (pcs)",
        "raw_label": "Raw Packaging Used",
        "date_label": "Shift Date",
        "maint_header": "🛠 Maintenance Center",
        "maint_types": ["Planned Maintenance", "Breakdown"],
        "tech_label": "Technician Name",
        "issue_label": "Issue Description",
        "start_t": "Downtime Start",
        "end_t": "Repair End",
        "note_label": "Additional Notes",
        "save_btn": "Save & Send Alert",
        "success_msg": "✅ Saved & Notified Successfully",
        "eff_title": "Average Efficiency %",
        "waste_title": "Historical Waste Analysis",
        "history_p": "📋 Production Log (10 Days)",
        "history_m": "🔧 Maintenance Log (10 Days)",
        "admin_title": "🔒 Admin Panel",
        "delete_btn": "🗑 Delete Selected Record",
        "del_success": "🗑 Record Deleted Successfully",
        "tools_label": "🔧 Tools:",
        "proc_label": "📜 Cleaning/Work Standard:",
        "weekend_msg": "🏖 Today is Friday (Weekend) - No scheduled maintenance.",
        "no_data": "No data in the last 10 days",
        "del_prod_title": "Delete from Production Log",
        "del_maint_title": "Delete from Maintenance Log",
        "select_row": "Select record to delete",
        "confirm_del": "⚠️ Are you sure you want to delete?",
    }
}

# --- 3. الهوية والشعار ---
st.sidebar.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
if os.path.exists("birma mark.png"):
    st.sidebar.image("birma mark.png", use_container_width=True)
else:
    st.sidebar.markdown("<h1 style='color: #0047AB;'>BIRMA</h1>", unsafe_allow_html=True)
st.sidebar.markdown("</div>", unsafe_allow_html=True)

st.sidebar.divider()
st.sidebar.markdown(f"<p style='text-align: center; font-size: 12px; color: gray; margin-bottom:0;'>Designed by:</p>", unsafe_allow_html=True)
st.sidebar.markdown(f"<h3 style='text-align: center; color: #2E8B57; margin-top:0;'>{LANG[ln]['designer']}</h3>", unsafe_allow_html=True)
st.sidebar.divider()

# --- 4. الربط والخدمات ---
try:
    conn = st.connection("gsheets_testing", type=GSheetsConnection)
    df_main = conn.read(spreadsheet=st.secrets["connections"]["gsheets_testing"]["spreadsheet"], ttl=0)
except:
    df_main = pd.DataFrame()

def send_telegram(msg):
    try:
        token = st.secrets["telegram"]["bot_token"]
        chat_id = st.secrets["telegram"]["chat_id"]
        requests.get(f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={urllib.parse.quote(msg)}&parse_mode=Markdown")
    except:
        pass

# --- 5. منطق فلترة مواعيد الصيانة ---
def get_scheduled_tasks(df_tasks):
    today = datetime.now()
    day_name = today.strftime('%A')
    is_first_of_month = (today.day == 1)

    if day_name == 'Friday':
        return pd.DataFrame()

    allowed_freqs = ['Daily']
    if day_name == 'Saturday':
        allowed_freqs.append('Weekly')
    if is_first_of_month:
        allowed_freqs.append('Monthly')

    return df_tasks[df_tasks['Freq'].isin(allowed_freqs)]

# --- دالة فلترة آخر 10 أيام ---
def filter_last_10_days(df, date_col='Date'):
    if df.empty:
        return df
    try:
        cutoff = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
        df[date_col] = df[date_col].astype(str)
        return df[df[date_col] >= cutoff].copy()
    except:
        return df

# الثوابت الفنية
CONFIG = {
    "الخط الأول(smi)": {
        "الأصناف": ["200 ml Carton", "200 ml Shrink", "600 ml Carton", "1.5 L Shrink"],
        "العبوات": {"200 ml Carton": 48, "200 ml Shrink": 20, "600 ml Carton": 30, "1.5 L Shrink": 6},
        "السرعة": {"200 ml Carton": 35000, "200 ml Shrink": 35000, "600 ml Carton": 20000, "1.5 L Shrink": 12000}
    },
    "الخط الثاني(welbing)": {
        "الأصناف": ["200 ml Carton", "200 ml Shrink", "330 ml Carton", "331 ml Shrink"],
        "العبوات": {"200 ml Carton": 48, "200 ml Shrink": 20, "330 ml Carton": 40, "331 ml Shrink": 20},
        "السرعة": {"200 ml Carton": 40000, "200 ml Shrink": 40000, "330 ml Carton": 40000, "331 ml Shrink": 40000}
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
selected_menu = st.sidebar.selectbox("Menu", LANG[ln]["menu"])
selected_line = st.sidebar.radio(LANG[ln]["line_label"], list(CONFIG.keys()))

# أ. الإنتاج
if selected_menu == LANG[ln]["menu"][0]:
    st.header(f"{LANG[ln]['menu'][0]} - {selected_line}")
    with st.form("prod_form"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input(LANG[ln]["sup_label"])
            product = st.selectbox(LANG[ln]["prod_label"], CONFIG[selected_line]["الأصناف"])
            target = st.number_input(LANG[ln]["target_label"], min_value=0)
        with c2:
            preforms = st.number_input(LANG[ln]["preform_label"], min_value=0)
            raw_type = "Carton" if "Carton" in product else "Shrink"
            raw_val = st.number_input(f"{LANG[ln]['raw_label']} ({raw_type})", min_value=0)
            p_date = st.date_input(LANG[ln]["date_label"])

        if st.form_submit_button(LANG[ln]["save_btn"]):
            b_per_u = CONFIG[selected_line]["العبوات"][product]
            total_b = target * b_per_u
            eff = round((total_b / (CONFIG[selected_line]["السرعة"][product] * 15)) * 100, 1)
            new_row = pd.DataFrame([{
                "Type": "Production", "Line": selected_line, "Date": str(p_date),
                "Staff": name, "Product": product, "Output_Units": target,
                "Waste_Bottles": preforms - total_b, "Waste_Raw": raw_val - target,
                "Efficiency_%": eff, "Timestamp": datetime.now().strftime("%H:%M")
            }])
            conn.update(
                spreadsheet=st.secrets["connections"]["gsheets_testing"]["spreadsheet"],
                data=pd.concat([df_main, new_row], ignore_index=True)
            )
            send_telegram(f"🚀 *Production Update*\nLine: {selected_line}\nOutput: {target}\nEff: {eff}%")
            st.success(LANG[ln]["success_msg"])
            st.rerun()

# ب. الصيانة
elif selected_menu == LANG[ln]["menu"][1]:
    st.header(LANG[ln]["maint_header"])
    m_type = st.radio("Type", LANG[ln]["maint_types"], horizontal=True)
    machine = st.sidebar.selectbox("Machine", list(MACHINE_MAP.keys()))

    if m_type == LANG[ln]["maint_types"][0]:
        path = MACHINE_MAP[machine]
        if os.path.exists(path):
            df_raw = pd.read_excel(path, skiprows=2)
            df_raw.columns = ['Cat', 'No', 'Name', 'Photo', 'Tools', 'Proc', 'Freq', 'Stat', 'Note', 'Staff']
            scheduled_tasks = get_scheduled_tasks(df_raw)

            if scheduled_tasks.empty:
                st.warning(LANG[ln]["weekend_msg"])
            else:
                with st.form("m_form"):
                    tech = st.text_input(LANG[ln]["tech_label"])
                    recs = []
                    for i, r in scheduled_tasks.iterrows():
                        st.divider()
                        c_i, c_p = st.columns([2, 1])
                        with c_i:
                            st.markdown(f"### 🔧 {r['Name']} ({r['Freq']})")
                            st.markdown(f"**{LANG[ln]['tools_label']}** `{r['Tools'] if pd.notna(r['Tools']) else 'N/A'}`")
                            st.info(f"**{LANG[ln]['proc_label']}**\n{r['Proc'] if pd.notna(r['Proc']) else 'N/A'}")
                            ok = st.checkbox(f"DONE - {r['Name']}", key=f"k{i}")
                            note = st.text_input(LANG[ln]["note_label"], key=f"n{i}")
                        with c_p:
                            img = os.path.join("images", str(r['Photo']).strip())
                            if os.path.exists(img):
                                st.image(img, use_container_width=True)
                        if ok:
                            recs.append({
                                "Type": "Maint_Daily", "Line": selected_line,
                                "Date": str(datetime.now().date()), "Machine": machine,
                                "Task": r['Name'], "Staff": tech, "Notes": note
                            })

                    if st.form_submit_button(LANG[ln]["save_btn"]):
                        conn.update(
                            spreadsheet=st.secrets["connections"]["gsheets_testing"]["spreadsheet"],
                            data=pd.concat([df_main, pd.DataFrame(recs)], ignore_index=True)
                        )
                        st.success(LANG[ln]["success_msg"])
                        st.rerun()
    else:
        with st.form("break_form"):
            t_name = st.text_input(LANG[ln]["tech_label"])
            issue = st.text_area(LANG[ln]["issue_label"])
            col1, col2 = st.columns(2)
            t1 = col1.time_input(LANG[ln]["start_t"])
            t2 = col2.time_input(LANG[ln]["end_t"])
            m_note = st.text_area(LANG[ln]["note_label"])
            if st.form_submit_button(LANG[ln]["save_btn"]):
                new_b = pd.DataFrame([{
                    "Type": "Maint_Breakdown", "Line": selected_line,
                    "Date": str(datetime.now().date()), "Machine": machine,
                    "Staff": t_name, "Notes": f"{t1}-{t2} | {issue} | {m_note}"
                }])
                conn.update(
                    spreadsheet=st.secrets["connections"]["gsheets_testing"]["spreadsheet"],
                    data=pd.concat([df_main, new_b], ignore_index=True)
                )
                send_telegram(f"⚠️ *Breakdown*\nMachine: {machine}\nTech: {t_name}\nIssue: {issue}")
                st.success(LANG[ln]["success_msg"])
                st.rerun()

# ج. السجلات والتقارير ← التعديل الرئيسي هنا
elif selected_menu == LANG[ln]["menu"][2]:
    st.header(LANG[ln]["menu"][2])

    if not df_main.empty:

        # ── الرسوم البيانية ──
        prod_data = df_main[df_main['Type'] == 'Production'].tail(15)
        if not prod_data.empty:
            g1, g2 = st.columns(2)
            with g1:
                fig_g = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=prod_data['Efficiency_%'].mean(),
                    title={'text': LANG[ln]["eff_title"]},
                    gauge={
                        'axis': {'range': [0, 100]},
                        'bar': {'color': '#2E8B57'},
                        'steps': [
                            {'range': [0, 60],   'color': '#ffcccc'},
                            {'range': [60, 80],  'color': '#fff3cd'},
                            {'range': [80, 100], 'color': '#d4edda'},
                        ]
                    }
                ))
                st.plotly_chart(fig_g, use_container_width=True)
            with g2:
                fig_b = px.bar(
                    prod_data, x='Date', y='Waste_Bottles',
                    color='Product', title=LANG[ln]["waste_title"]
                )
                st.plotly_chart(fig_b, use_container_width=True)

        st.divider()

        # ── السجلات (آخر 10 أيام) ──
        tab1, tab2 = st.tabs([LANG[ln]["history_p"], LANG[ln]["history_m"]])

        # سجل الإنتاج
        with tab1:
            prod_10 = filter_last_10_days(
                df_main[df_main['Type'] == 'Production'].copy()
            ).sort_values('Date', ascending=False)

            if prod_10.empty:
                st.info(LANG[ln]["no_data"])
            else:
                st.dataframe(prod_10, use_container_width=True, hide_index=True)

                # حذف سجل إنتاج
                st.markdown(f"#### {LANG[ln]['del_prod_title']}")
                prod_10_reset = prod_10.reset_index()

                options = {
                    f"[{row['index']}] {row['Date']} | {row['Line']} | {row['Product']} | {row['Output_Units']} وحدة": row['index']
                    for _, row in prod_10_reset.iterrows()
                }
                selected_label = st.selectbox(
                    LANG[ln]["select_row"],
                    list(options.keys()),
                    key="del_prod_sel"
                )
                if st.button(LANG[ln]["delete_btn"], key="del_prod_btn"):
                    row_idx = options[selected_label]
                    df_updated = df_main.drop(row_idx)
                    conn.update(
                        spreadsheet=st.secrets["connections"]["gsheets_testing"]["spreadsheet"],
                        data=df_updated
                    )
                    st.success(LANG[ln]["del_success"])
                    st.rerun()

        # سجل الصيانة
        with tab2:
            maint_10 = filter_last_10_days(
                df_main[df_main['Type'].str.contains('Maint', na=False)].copy()
            ).sort_values('Date', ascending=False)

            if maint_10.empty:
                st.info(LANG[ln]["no_data"])
            else:
                st.dataframe(maint_10, use_container_width=True, hide_index=True)

                # حذف سجل صيانة
                st.markdown(f"#### {LANG[ln]['del_maint_title']}")
                maint_10_reset = maint_10.reset_index()

                m_options = {
                    f"[{row['index']}] {row['Date']} | {row.get('Machine', '')} | {row['Type']}": row['index']
                    for _, row in maint_10_reset.iterrows()
                }
                selected_m_label = st.selectbox(
                    LANG[ln]["select_row"],
                    list(m_options.keys()),
                    key="del_maint_sel"
                )
                if st.button(LANG[ln]["delete_btn"], key="del_maint_btn"):
                    row_idx = m_options[selected_m_label]
                    df_updated = df_main.drop(row_idx)
                    conn.update(
                        spreadsheet=st.secrets["connections"]["gsheets_testing"]["spreadsheet"],
                        data=df_updated
                    )
                    st.success(LANG[ln]["del_success"])
                    st.rerun()

    else:
        st.info(LANG[ln]["no_data"])

# --- لوحة تحكم المشرف ---
st.sidebar.divider()
with st.sidebar.expander(LANG[ln]["admin_title"]):
    pw = st.text_input("Password", type="password")
    if pw == "admin123":
        st.success("✅ مرحباً بالمشرف")
        if not df_main.empty:
            row_to_del = st.selectbox("Select Row ID", df_main.index)
            if st.button(LANG[ln]["delete_btn"]):
                df_updated = df_main.drop(row_to_del)
                conn.update(
                    spreadsheet=st.secrets["connections"]["gsheets_testing"]["spreadsheet"],
                    data=df_updated
                )
                st.success(LANG[ln]["del_success"])
                st.rerun()

st.markdown(
    f"<br><hr><center><p style='color: gray;'>BIRMA v6.1 | "
    f"<b>Designed by: {LANG[ln]['designer']}</b></p></center>",
    unsafe_allow_html=True
)
