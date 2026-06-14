# auth.py - النسخة الكاملة المعدلة

import streamlit as st
import json
import base64
import os
import logging
from datetime import datetime
from database import db_manager
from constants import USERS, LANG
from helpers import load_language

# إعداد logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def save_credentials_local(username, password, remember=True, company_id=None):
    """Save credentials to localStorage"""
    if remember:
        try:
            data = {"u": username, "p": password, "c": company_id, "t": datetime.now().isoformat()}
            encoded = base64.b64encode(json.dumps(data).encode()).decode()
            st.markdown(f"<script>localStorage.setItem('sfs_creds', '{encoded}');</script>", unsafe_allow_html=True)
            return True
        except:
            return False
    return False
def set_company_context(user):
    import streamlit as st
    
    if user.get('is_super_admin', False):
        # المشرف العام يرى كل شيء
        st.session_state.company_id = None
        st.session_state.factory_id = None
        st.session_state.is_super_admin = True
    else:
        # المستخدم العادي مقيد بشركته
        company_id = user.get('company_id')
        if company_id:
            st.session_state.company_id = company_id
            st.session_state.factory_id = company_id
        else:
            # مستخدم بدون شركة - لا يرى شيئاً
            st.session_state.company_id = None
            st.session_state.factory_id = None
        st.session_state.is_super_admin = False
    
    logger.info(f"Company context set: company_id={st.session_state.company_id}")

def load_credentials_local():
    """Load credentials safely from Streamlit session or params"""
    if 'creds' in st.query_params:
        try:
            decoded = base64.b64decode(st.query_params['creds']).decode()
            data = json.loads(decoded)
            return data.get('u'), data.get('p'), True, data.get('c')
        except:
            return None, None, False, None
    return None, None, False, None

def clear_credentials_local():
    """Clear saved credentials"""
    st.markdown("<script>localStorage.removeItem('sfs_creds');</script>", unsafe_allow_html=True)
    if 'creds' in st.query_params:
        del st.query_params['creds']

def init_session_state():
    """Initialize session state variables"""
    if 'lang' not in st.session_state:
        st.session_state.lang = 'ar'
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = False
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    if 'user_name' not in st.session_state:
        st.session_state.user_name = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'inventory_version' not in st.session_state:
        st.session_state.inventory_version = 0
    if 'must_change_password' not in st.session_state:
        st.session_state.must_change_password = False
    if 'factory_id' not in st.session_state:
        st.session_state.factory_id = None
    if 'company_id' not in st.session_state:
        st.session_state.company_id = None
    if 'is_super_admin' not in st.session_state:
        st.session_state.is_super_admin = False

# auth.py - استبدل دالة login_screen بالكامل

def login_screen(t):
    """Display login screen with company selection"""
    init_session_state()

    # Language selector
    col_lang1, col_lang2, col_lang3 = st.columns([1, 2, 1])
    with col_lang1:
        current_lang = st.session_state.get('lang', 'ar')
        if current_lang == 'ar':
            if st.button("🇬🇧 " + t.get("english_btn", "English"), width='stretch'):
                st.session_state.lang = 'en'
                st.session_state.t = load_language('en')
                st.rerun()
        else:
            if st.button("🇸🇦 " + t.get("arabic_btn", "Arabic"), width='stretch'):
                st.session_state.lang = 'ar'
                st.session_state.t = load_language('ar')
                st.rerun()

    saved_user, saved_pass, _, saved_company_id = load_credentials_local()
    
    if saved_user and saved_pass:
            user = db_manager.authenticate_user(saved_user, saved_pass, saved_company_id)
            if user:
                st.session_state.authenticated = True
                st.session_state.user_role = user['role']
                st.session_state.user_name = user['name']
                st.session_state.username = user['username']
                st.session_state.user_id = user['id']
                st.session_state.is_super_admin = user.get('is_super_admin', False)
                st.session_state.company_id = user.get('company_id')
                st.session_state.factory_id = user.get('company_id')
                st.cache_data.clear()
                st.rerun()
            return
    
    st.markdown(f"<h1 style='text-align: center; color: #0047AB;'>🏭 {t.get('app_title', 'Smart Factory System')}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center; color: #555;'>{t.get('system_subtitle', 'OEE Management & Analytics System')}</h3>", unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader(t.get("login_btn", "Login"))
        
        # ✅ خطوة 1: اختيار المصنع أولاً
        companies = db_manager.get_companies_list(status='active')
        
        # إضافة خيار "المشرف العام" للمستخدمين الذين لديهم صلاحيات
        company_options = {0: "-- " + t.get("select_factory_first", "اختر المصنع أولا --")}
        
        for c in companies:
            company_options[c['id']] = f"🏭 {c['name_ar']} ({c['code']})"
        
        # إضافة خيار المشرف العام (سيظهر بعد اختيار المستخدم)
        selected_company_id = st.selectbox(
            "🏭 " + t.get("factory_select", "اختر المصنع"),
            options=list(company_options.keys()),
            format_func=lambda x: company_options.get(x, ""),
            index=0,
            key="login_factory_select"
        )

        with st.form("login_form"):
            username = st.text_input(t.get("username", "Username"))
            password = st.text_input(t.get("password", "Password"), type="password")
            remember = st.checkbox(t.get("remember_me", "Remember me"))
            
            submit = st.form_submit_button(t.get("login_btn", "Login"), width='stretch')
            
            if submit:
                if not username or not password:
                    st.error(t.get("login_validation_error", "Please enter username and password"))
                    return
                
                # ✅ التحقق من اختيار المصنع
                if selected_company_id == 0:
                    st.error("⚠️ " + t.get("please_select_factory", "الرجاء اختيار المصنع أولاً"))
                    return
                
                logger.info(f"Login attempt for user: {username} on company_id: {selected_company_id}")
                
                # ✅ المصادقة مع تمرير company_id
                user = db_manager.authenticate_user(username, password, selected_company_id)
                
                if user:
                    # التحقق من أن المستخدم ينتمي للمصنع المختار (لغير المشرف العام)
                    if not user.get('is_super_admin', False):
                        if user.get('company_id') != selected_company_id:
                            st.error(f"❌ {t.get('user_not_belong_to_factory', 'هذا المستخدم لا ينتمي للمصنع المختار')}")
                            return
                    
                    st.session_state.authenticated = True
                    st.session_state.user_role = user['role']
                    st.session_state.user_name = user['name']
                    st.session_state.username = user['username']
                    st.session_state.user_id = user['id']
                    st.session_state.is_super_admin = user.get('is_super_admin', False)
                    
                    if user.get('is_super_admin', False):
                        st.session_state.company_id = None
                        st.session_state.factory_id = None
                    else:
                        st.session_state.company_id = user.get('company_id')
                        st.session_state.factory_id = user.get('company_id')
                    
                    if remember:
                        save_credentials_local(username, password, True, selected_company_id)
                    
                    st.cache_data.clear()
                    st.success(f"✅ Welcome {user['name']}!")
                    logger.info(f"User {username} logged in successfully to company {selected_company_id}")
                    st.rerun()
                    return
                else:
                    st.error(f"❌ {t.get('login_error', 'اسم المستخدم أو كلمة المرور غير صحيحة')}")
        st.markdown("---")
        st.markdown("### 🏭 " + t.get("new_factory", "إنشاء مصنع جديد"))
        st.caption("استخدم المعالج متعدد الخطوات لإنشاء مصنع جديد ببياناته الكاملة")
        
        with st.form("super_admin_wizard_form"):
            sa_username = st.text_input("👑 اسم المستخدم للمشرف العام", placeholder="admin")
            sa_password = st.text_input("🔑 كلمة سر المشرف العام", type="password")
            if st.form_submit_button("🚀 " + t.get("open_factory_wizard", "فتح معالج إنشاء مصنع جديد"),
                                     use_container_width=True, type="primary"):
                sa_user = db_manager.authenticate_user(sa_username, sa_password)
                if sa_user and sa_user.get('is_super_admin', False):
                    st.session_state.show_factory_wizard = True
                    st.rerun()
                else:
                    st.error("❌ بيانات المشرف العام غير صحيحة - يجب تسجيل الدخول بحساب المشرف العام")
                    
def logout():
    """Logout user"""
    username = st.session_state.get('username', '') or st.session_state.get('user_name', '')
    
    try:
        from database import db_manager
        if hasattr(db_manager, 'add_info_log'):
            db_manager.add_info_log('logout', f"User '{username}' logged out")
    except Exception as e:
        print(f"Logout log error: {e}")
    
    # مسح session state
    for key in ['authenticated', 'user_role', 'user_name', 'username', 'user_id', 
                'must_change_password', 'factory_id', 'is_super_admin']:
        if key in st.session_state:
            del st.session_state[key]
    
    st.rerun()
# database.py - أضف هذه الدالة

def init_multi_tenant_tables(self):
    """تهيئة الجداول الخاصة بـ Multi-Tenant"""
    try:
        with self.engine.connect() as conn:
            # التحقق من وجود جدول companies
            if self._use_sqlite:
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='companies'"))
            else:
                result = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name='companies')"))
            
            # إذا لم يكن الجدول موجوداً، قم بإنشائه
            # هذا سيتم تلقائياً بواسطة Base.metadata.create_all()
            pass
    except Exception as e:
        logger.warning(f"init_multi_tenant_tables: {e}")    

def check_authentication():
    """Check if user is authenticated"""
    return st.session_state.get('authenticated', False)

def change_password(username, old_password, new_password):
    """Change user password"""
    user = db_manager.authenticate_user(username, old_password)
    if user:
        success = db_manager.update_user_password(username, new_password)
        if success:
            try:
                if hasattr(db_manager, 'add_info_log'):
                    db_manager.add_info_log('password', f"User '{username}' changed password")
            except:
                pass
        return success
    return False