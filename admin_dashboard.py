# admin_dashboard.py

import streamlit as st
import pandas as pd
from datetime import datetime
from database import db_manager, delete_company_record
from sqlalchemy import text


def show_super_admin_dashboard(t):
    """لوحة تحكم المدير العام"""
    
    st.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <h1 style="color: #1e3a5f;">👑 Super Admin Dashboard</h1>
        <p style="color: #64748b;">إدارة جميع المصانع والإحصائيات العامة</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # جلب جميع الشركات/المصانع
    try:
        session = db_manager.get_session()
        companies = session.execute(text("SELECT * FROM companies ORDER BY id")).fetchall()
        session.close()
    except Exception as e:
        st.error(f"Error loading companies: {e}")
        return
    
    if not companies:
        st.info("📭 لا توجد شركات مسجلة حتى الآن")
        return
    
    # إحصائيات عامة
    st.subheader("📊 General Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🏭 Total Companies", len(companies))
    with col2:
        active = len([c for c in companies if c.status == 'active'])
        st.metric("✅ Active Companies", active)
    with col3:
        session = db_manager.get_session()
        total_users = session.execute(text("SELECT COUNT(*) FROM users")).fetchone()[0]
        session.close()
        st.metric("👥 Total Users", total_users)
    with col4:
        enterprise = len([c for c in companies if c.subscription_plan == 'enterprise'])
        st.metric("💎 Enterprise", enterprise)
    
    st.markdown("---")
    
    # جدول الشركات
    st.subheader("🏭 Companies List")
    
    companies_data = []
    for c in companies:
        companies_data.append({
            "ID": c.id,
            "Name (AR)": c.name_ar,
            "Name (EN)": c.name_en,
            "Code": c.code,
            "Status": "🟢 Active" if c.status == 'active' else ("🟡 Pending" if c.status == 'pending' else "🔴 Suspended"),
            "Plan": "💎 Enterprise" if c.subscription_plan == 'enterprise' else ("⭐ Pro" if c.subscription_plan == 'pro' else "📦 Basic"),
            "Created": c.created_at.strftime("%Y-%m-%d") if c.created_at else "-"
        })
    
    df_companies = pd.DataFrame(companies_data)
    st.dataframe(df_companies, width='stretch', hide_index=True)
    
    st.markdown("---")

    # ---- Delete Company Section ----
    st.subheader("🗑️ " + t.get("delete_company", "Delete Company"))

    company_ids = {c.id: f"{c.id} - {c.name_ar} ({c.name_en})" for c in companies}
    selected_id = st.selectbox(
        t.get("select_company_id", "Select Company ID"),
        options=sorted(company_ids.keys()),
        format_func=lambda x: company_ids[x],
        key="del_company_select"
    )
    confirm = st.checkbox(t.get("confirm_delete_company", "Yes, I want to permanently delete this company and ALL its data"))
    if st.button(t.get("delete_company", "Delete Company"), type="primary", use_container_width=True, disabled=not confirm):
        if delete_company_record(selected_id):
            st.success(t.get("company_deleted", "✅ Company deleted successfully"))
            st.rerun()
        else:
            st.error(t.get("delete_failed", "❌ Failed to delete company"))