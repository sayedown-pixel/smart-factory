import streamlit as st
import pandas as pd
from datetime import datetime
from database import db_manager, delete_company_record
from sqlalchemy import text


def show_super_admin_dashboard(t):
    """لوحة تحكم المدير العام - إدارة الاشتراكات والمصانع"""
    
    st.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <h1 style="color: #1e3a5f;">👑 Super Admin Dashboard</h1>
        <p style="color: #64748b;">إدارة جميع المصانع والاشتراكات</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # جلب جميع الشركات مع معلومات الاشتراك
    try:
        companies = db_manager.get_all_companies_with_subscription()
    except Exception as e:
        st.error(f"Error loading companies: {e}")
        return
    
    if not companies:
        st.info(t.get("no_companies_yet", "📭 لا توجد شركات مسجلة حتى الآن"))
        return
    
    # إحصائيات عامة
    st.subheader("📊 General Statistics")
    
    now = datetime.now()
    expired = [c for c in companies if c.get('is_expired', False)]
    active_trial = [c for c in companies if not c.get('is_expired', False) and c.get('subscription_plan') == 'trial']
    expiring_soon = [c for c in companies if not c.get('is_expired', False) and 0 < c.get('days_left', 0) <= 7]
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🏭 Total Companies", len(companies))
    with col2:
        st.metric("✅ Active (Trial)", len(active_trial))
    with col3:
        st.metric("🔴 Expired", len(expired))
    with col4:
        st.metric("⚠️ Expiring Soon (≤7d)", len(expiring_soon))
    
    st.markdown("---")
    
    # ---- Subscription Management Tab ----
    tab1, tab2 = st.tabs([t.get("sa_subscriptions", "👑 Subscription Management"), t.get("delete_company", "🗑️ Delete Company")])
    
    with tab1:
        st.subheader(t.get("sa_subscriptions", "👑 Subscription Management"))
        
        for c in companies:
            with st.container(border=True):
                cols = st.columns([2, 1, 1, 1, 1, 1])
                
                name = f"{c.get('name_ar', '')} ({c.get('name_en', '')})"
                created = c.get('created_at')
                created_str = created.strftime("%Y-%m-%d") if created else "-"
                trial_end = c.get('subscription_end')
                trial_end_str = trial_end.strftime("%Y-%m-%d") if trial_end else "-"
                days_left = c.get('days_left', 0)
                is_expired = c.get('is_expired', False)
                
                if is_expired:
                    status_str = "🔴 " + t.get("subscription_expired", "Expired")
                elif days_left <= 3:
                    status_str = "🔴 " + t.get("trial_period", "Trial") + f" ({days_left}d)"
                elif days_left <= 7:
                    status_str = "🟡 " + t.get("trial_period", "Trial") + f" ({days_left}d)"
                else:
                    status_str = "🟢 " + t.get("trial_period", "Trial") + f" ({days_left}d)"
                
                cols[0].write(f"**ID {c.get('id')}:** {name}")
                cols[1].write(f"📅 {t.get('sa_created_at', 'Created')}: {created_str}")
                cols[2].write(f"⏳ {t.get('sa_trial_end', 'Trial End')}: {trial_end_str}")
                cols[3].write(f"📆 {t.get('sa_days_left', 'Days Left')}: **{days_left}**")
                cols[4].write(f"📊 {t.get('sa_status', 'Status')}: {status_str}")
                
                with cols[5]:
                    if st.button(f"🔄 {t.get('sa_renew', 'Renew')}", key=f"renew_{c.get('id')}", use_container_width=True):
                        if db_manager.renew_company_subscription(c.get('id'), 60):
                            st.success(t.get("subscription_renewed", "✅ Subscription renewed successfully for 60 days"))
                            st.rerun()
                        else:
                            st.error(t.get("delete_failed", "❌ Failed to renew subscription"))
    
    with tab2:
        # ---- Delete Company Section ----
        st.subheader("🗑️ " + t.get("delete_company", "Delete Company"))
        
        company_ids = {c['id']: f"{c['id']} - {c.get('name_ar', '')} ({c.get('name_en', '')})" for c in companies}
        selected_id_del = st.selectbox(
            t.get("select_company_id", "Select Company ID"),
            options=sorted(company_ids.keys()),
            format_func=lambda x: company_ids[x],
            key="del_company_select_admin"
        )
        confirm = st.checkbox(t.get("confirm_delete_company", "Yes, I want to permanently delete this company and ALL its data"))
        if st.button(t.get("delete_company", "Delete Company"), type="primary", use_container_width=True, disabled=not confirm):
            if delete_company_record(selected_id_del):
                st.success(t.get("company_deleted", "✅ Company deleted successfully"))
                st.rerun()
            else:
                st.error(t.get("delete_failed", "❌ Failed to delete company"))
