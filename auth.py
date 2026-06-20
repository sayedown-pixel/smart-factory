# auth.py - النسخة الكاملة المعدلة

import streamlit as st
import logging
from database import db_manager
from helpers import load_language

# إعداد logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

APP_NAME = "Smart Factory System"
COMPANY_NAME = "smart factory system"


def save_login_preferences(username, company_id=None):
    """Remember non-sensitive login hints only."""
    st.session_state.remembered_username = username
    st.session_state.remembered_company_id = str(company_id or "")
    return True


def load_login_preferences():
    """Load remembered non-sensitive login hints."""
    return (
        st.session_state.get("remembered_username", ""),
        st.session_state.get("remembered_company_id", ""),
    )


def render_login_branding(t):
    """Render the public login header and privacy notice."""
    st.markdown(
        f"""
        <div style="text-align:center; padding: 1.25rem 0 0.5rem;">
            <div style="
                width: 86px;
                height: 86px;
                margin: 0 auto 0.75rem;
                border-radius: 22px;
                background: linear-gradient(135deg, #0047AB 0%, #0f766e 100%);
                color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 2.4rem;
                font-weight: 800;
                box-shadow: 0 12px 28px rgba(15, 23, 42, 0.18);
            ">SFS</div>
            <h1 style="margin: 0; color: #0047AB;">{APP_NAME}</h1>
            <h3 style="margin: 0.35rem 0 0; color: #555;">{COMPANY_NAME}</h3>
            <p style="margin: 0.35rem 0 0; color: #64748b;">
                {t.get('system_subtitle', 'OEE Management & Analytics System')}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander(t.get("privacy_policy", "Privacy Policy"), expanded=False):
        st.markdown(
            t.get(
                "privacy_policy_text",
                """
                **Smart Factory System** uses your login data only to verify your identity,
                assign the correct factory permissions, and protect production, maintenance,
                inventory, and reporting records.

                Passwords are never displayed or stored in the browser by this login screen.
                Use HTTPS in production to encrypt traffic between users and the server.
                """,
            )
        )
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

def clear_credentials_local():
    """Clear legacy saved credentials."""
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

    clear_credentials_local()
    remembered_username, remembered_company_id = load_login_preferences()
    
    
    render_login_branding(t)
    st.markdown("---")

    # Support info section
    with st.expander(t.get("support_title", "📞 Technical Support"), expanded=False):
        st.markdown(f"""
        <div style="text-align:center; padding:10px;">
            <p><strong>{t.get('support_contact', 'Contact Technical Support:')}</strong></p>
            <p>📧 {t.get('support_email1', 'sayedown@hotmail.com')}</p>
            <p>📧 {t.get('support_email2', 'sayedown1982@gmail.com')}</p>
            <p>{t.get('support_whatsapp', '📱 WhatsApp: +966533788704')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader(t.get("login_btn", "Login"))
        
        # ✅ Factory ID text input instead of company dropdown
        selected_company_id = st.text_input(
            "🏭 " + t.get("factory_id", "Factory ID"),
            value=remembered_company_id,
            placeholder=t.get("factory_id_placeholder", "Example: 1"),
            help=t.get("factory_id_help", "Enter the factory ID number that was created"),
            key="login_factory_id"
        )

        with st.form("login_form"):
            username = st.text_input(t.get("username", "Username"), value=remembered_username)
            password = st.text_input(t.get("password", "Password"), type="password")
            remember = st.checkbox(t.get("remember_me", "Remember me"))
            
            submit = st.form_submit_button(t.get("login_btn", "Login"), width='stretch')
            
            if submit:
                if not username or not password:
                    st.error(t.get("login_validation_error", "Please enter username and password"))
                    return
                
                # ✅ Parse factory ID
                if not selected_company_id or not selected_company_id.strip():
                    st.error("⚠️ " + t.get("factory_id_required", "⚠️ Please enter the factory ID"))
                    return
                
                try:
                    parsed_id = int(selected_company_id.strip())
                except ValueError:
                    st.error("⚠️ " + t.get("factory_id_required", "⚠️ Please enter a valid numeric factory ID"))
                    return
                
                # Verify the factory exists
                companies = db_manager.get_companies_list(status='active')
                company_ids = [c['id'] for c in companies]
                if parsed_id not in company_ids:
                    st.error("❌ " + t.get("factory_not_found", "❌ Factory not found"))
                    return
                
                logger.info(f"Login attempt for user: {username} on company_id: {parsed_id}")
                
                # ✅ Authenticate with company_id
                user = db_manager.authenticate_user(username, password, parsed_id)
                
                if user:
                    # Verify the user belongs to the selected factory (for non-super-admin)
                    if not user.get('is_super_admin', False):
                        if user.get('company_id') != parsed_id:
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
                        st.session_state.trial_expired = False
                        st.session_state.read_only = False
                    else:
                        st.session_state.company_id = user.get('company_id')
                        st.session_state.factory_id = user.get('company_id')
                        # Check trial status for non-super-admin
                        try:
                            trial = db_manager.check_company_trial_status(user.get('company_id'))
                            st.session_state.trial_expired = trial.get('is_expired', False)
                            st.session_state.trial_days_left = trial.get('days_left', 0)
                            st.session_state.trial_end = trial.get('trial_end')
                            st.session_state.read_only = trial.get('is_expired', False)
                        except Exception as e:
                            st.session_state.trial_expired = False
                            st.session_state.read_only = False
                            st.session_state.trial_days_left = 60
                    
                    if remember:
                        save_login_preferences(username, parsed_id)
                    
                    st.cache_data.clear()
                    if st.session_state.get('trial_expired', False):
                        st.error(t.get("trial_expired", "❌ Trial Period Expired"))
                        st.warning(t.get("trial_expired_msg", "The trial period for this factory has expired. Please contact technical support for renewal."))
                    elif st.session_state.get('trial_days_left', 60) <= 3:
                        st.warning(t.get("trial_expire_soon", "⚠️ Trial period will expire in {days} days").replace("{days}", str(st.session_state.trial_days_left)))
                    logger.info(f"User {username} logged in successfully to company {parsed_id}")
                    st.rerun()
                    return
                else:
                    st.error(f"❌ {t.get('login_error', 'اسم المستخدم أو كلمة المرور غير صحيحة')}")
        st.markdown("---")
        st.markdown("### 🏭 " + t.get("new_factory", "إنشاء مصنع جديد"))
        st.caption("استخدم المعالج متعدد الخطوات لإنشاء مصنع جديد ببياناته الكاملة")
        
        with st.form("super_admin_wizard_form"):
            sa_username = st.text_input("👑 " + t.get("wizard_admin_username", "اسم المستخدم للمشرف العام"), placeholder="admin")
            sa_password = st.text_input("🔑 " + t.get("wizard_admin_password", "كلمة سر المشرف العام"), type="password")
            if st.form_submit_button("🚀 " + t.get("open_factory_wizard", "فتح معالج إنشاء مصنع جديد"),
                                     use_container_width=True, type="primary"):
                # Use hardcoded "smart_factory" password instead of DB check
                if sa_password == "smart_factory":
                    st.session_state.show_factory_wizard = True
                    st.rerun()
                else:
                    st.error("❌ " + t.get("wizard_auth_error", "كلمة المرور غير صحيحة - استخدم كلمة سر معالج إنشاء المصنع"))
                    
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
