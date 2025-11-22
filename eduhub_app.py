# -------------------------------
# PART 1: Imports, Config, and Sidebar Setup
# -------------------------------
import os
import random
import streamlit as st
import theme   # ✅ import theme for colors
import json
import hashlib
import shutil
import uuid, time   # ✅ added for session tracking

from send_email import send_email
from utils import list_files, days_remaining, is_membership_active
from drive_utils import authenticate_drive, upload_to_drive

UPLOAD_ROOT = "uploads"
os.makedirs(UPLOAD_ROOT, exist_ok=True)

# Admin credentials from secrets
admin_user = st.secrets["admin_user"]
admin_pass = st.secrets["admin_pass"]

# ✅ Helper: dynamically list all parent folders
def get_parent_folders():
    return [f for f in os.listdir(UPLOAD_ROOT) if os.path.isdir(os.path.join(UPLOAD_ROOT, f))]

# ✅ NEW: recursively list subfolders within any path (for deep nesting)
def get_subfolders(path):
    """Return immediate subfolders inside the given path."""
    if not os.path.exists(path):
        return []
    return [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]

# Streamlit page config
st.set_page_config(page_title="EduHub Learning Resources", layout="wide")

# Apply global theme styles
st.markdown(theme.load_theme(), unsafe_allow_html=True)

# Custom CSS
st.markdown("""
    <style>
    .streamlit-expanderHeader {flex-direction: row-reverse;}
    .subscription-card {
        text-align:center;
        color:#cc0000;
        font-size:18px;
        font-family: "Trebuchet MS", "Lucida Sans Unicode", "Lucida Grande", Arial, sans-serif;
        border:3px solid #cc0000;
        border-radius:12px;
        background: linear-gradient(180deg, #fffaf9 0%, #fff5f5 100%);
        padding:20px;
        margin:12px 0 18px 0;
        line-height:1.6;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.08);
    }
    .subscription-card strong { color:#cc0000; }
    </style>
""", unsafe_allow_html=True)

# -------------------------------
# Traffic Tracking
# -------------------------------
VISITS_FILE = "visits.json"
PAGE_VIEWS_FILE = "page_views.json"

def load_visits():
    if os.path.exists(VISITS_FILE):
        with open(VISITS_FILE, "r") as f:
            return json.load(f)
    return {"total": 0}

def save_visits(visits):
    with open(VISITS_FILE, "w") as f:
        json.dump(visits, f)

def load_page_views():
    if os.path.exists(PAGE_VIEWS_FILE):
        with open(PAGE_VIEWS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_page_views(views):
    with open(PAGE_VIEWS_FILE, "w") as f:
        json.dump(views, f)

def log_page_view(page_name):
    views = load_page_views()
    views[page_name] = views.get(page_name, 0) + 1
    save_page_views(views)
    return views[page_name]

# ✅ Increment global visits each time app loads
visits = load_visits()
visits["total"] += 1
save_visits(visits)

# -------------------------------
# Persistence helpers
# -------------------------------
USERS_FILE = "users.json"
DRIVE_FILE_MAP = "drive_files.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {admin_user: admin_pass}  # default admin if file missing

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def load_drive_files():
    if os.path.exists(DRIVE_FILE_MAP):
        with open(DRIVE_FILE_MAP, "r") as f:
            return json.load(f)
    return {}

def save_drive_files(drive_files):
    with open(DRIVE_FILE_MAP, "w") as f:
        json.dump(drive_files, f)

# -------------------------------
# Initialize session state
# -------------------------------
for key, value in {
    "users": load_users(),
    "logged_in": False,
    "username": "",
    "membership": "",
    "expiry": "",
    "show_login": True,
    "show_signup": False,
    "show_recovery": False,
    "reset_code": "",
    "reset_email": "",
    "drive": None,
    "drive_files": load_drive_files()
}.items():
    if key not in st.session_state:
        st.session_state[key] = value

# -------------------------------
# Gadget/session tracking helpers
# -------------------------------
SESSIONS_FILE = "sessions.json"

def load_sessions():
    if os.path.exists(SESSIONS_FILE):
        with open(SESSIONS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_sessions(sessions):
    with open(SESSIONS_FILE, "w") as f:
        json.dump(sessions, f)

def add_session(username):
    sessions = load_sessions()
    active = sessions.get(username, [])
    # Optional: expire sessions older than 24h
    active = [s for s in active if time.time() - s["timestamp"] < 86400]

    if len(active) >= 2:
        return False  # ❌ Already at max gadgets

    new_session = {"id": str(uuid.uuid4()), "timestamp": time.time()}
    active.append(new_session)
    sessions[username] = active
    save_sessions(sessions)
    return True

def count_sessions(username):
    sessions = load_sessions()
    active = sessions.get(username, [])
    active = [s for s in active if time.time() - s["timestamp"] < 86400]
    return len(active)

# -------------------------------
# Sidebar resources (dynamic tree with clickable files)
# -------------------------------
st.sidebar.markdown("<h3 style='color:#003366;'>📘 EduHub Resources</h3>", unsafe_allow_html=True)

def show_sidebar_tree(base_folder, indent=0):
    folder_path = os.path.join(UPLOAD_ROOT, base_folder)
    if not os.path.exists(folder_path):
        return

    subitems = os.listdir(folder_path)
    subfolders = [f for f in subitems if os.path.isdir(os.path.join(folder_path, f))]
    files = [f for f in subitems if os.path.isfile(os.path.join(folder_path, f))]

    # Show subfolders recursively
    for sub in sorted(subfolders):
        with st.expander(f"{' ' * indent}📁 {sub}", expanded=False):
            show_sidebar_tree(os.path.join(base_folder, sub), indent + 2)

    # Show files with login-aware behavior
    for idx, f in enumerate(sorted(files)):
        file_id = st.session_state.get("drive_files", {}).get(f, None)
        full_rel_path = os.path.join(base_folder, f)
        safe_key = f"{full_rel_path}_{indent}_{idx}"  # ✅ unique key

        if st.session_state.get("logged_in", False):
            if file_id:
                st.markdown(
                    f"{' ' * (indent + 2)}[📄 {f}](https://drive.google.com/file/d/{file_id}/view)",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(f"{' ' * (indent + 2)}📄 {f} (No Drive link)")
        else:
            if st.button(f"{' ' * (indent + 2)}📄 {f}", key=safe_key):
                st.warning("Log in to access this file.")
                st.rerun()

# Render all parent folders dynamically
for folder in get_parent_folders():
    with st.sidebar.expander(f"🔹 {folder}", expanded=False):
        show_sidebar_tree(folder)

# --- Heading stays at the very top center ---
st.markdown(
    "<div style='text-align:center;margin-top:-50px;'>"
    "<h3 style='color:#003366; font-size:20px;'>EDUHUB LEARNING RESOURCES</h3>"
    "</div>",
    unsafe_allow_html=True
)

# --- Layout columns ---
left_col, center_col, right_col = st.columns([2,6,2])
# -------------------------------
# PART 2: Member Tools (Right Sidebar)
# -------------------------------
with right_col:
    st.markdown("<h3 style='color:#006600;'>Member Tools</h3>", unsafe_allow_html=True)

    # Login block
    if st.session_state["show_login"]:
        username = st.text_input("Username or Email", key="login_user_expander")
        password = st.text_input("Password", type="password", key="login_pass_expander")

        if st.button("Log In", key="login_btn_expander"):
            users = st.session_state.get("users", {})

            if username == admin_user and password == admin_pass:
                st.session_state.update({
                    "logged_in": True,
                    "username": admin_user,
                    "membership": "ADMIN",
                    "expiry": "2099-12-31",
                    "show_login": False,
                    "show_signup": False,
                    "show_recovery": False
                })
                st.success("✅ Logged in as Admin.")
                st.rerun()

            elif username in users and users[username] == password:
                if add_session(username):  # ✅ enforce gadget limit
                    st.session_state.update({
                        "logged_in": True,
                        "username": username,
                        "membership": "MEMBER",
                        "expiry": "2099-12-31",
                        "show_login": False,
                        "show_signup": False,
                        "show_recovery": False
                    })
                    st.success(f"✅ Logged in as {username}.")
                    st.rerun()
                else:
                    st.error("❌ You have reached the maximum of 2 gadgets logged in. Please log out from another device.")
            else:
                st.error("❌ Invalid username or password.")

        # 🔹 Sign Up button shows subscription info (no inputs)
        if st.button("Sign Up", key="signup_btn_expander"):
            st.session_state.update({
                "show_login": False,
                "show_signup": True,
                "show_recovery": False
            })
            st.rerun()

        # 🔹 Forgot Password
        if st.button("Forgot Password?", key="forgot_btn_expander"):
            st.session_state.update({
                "show_login": False,
                "show_signup": False,
                "show_recovery": True
            })
            st.rerun()

    # Sign Up block (payment instructions only + go back)
    elif st.session_state["show_signup"]:
        # 🔹 Go Back to Log In button
        if st.button("⬅️ Go Back to Log In", key="go_back_login_btn"):
            st.session_state.update({
                "show_signup": False,
                "show_login": True,
                "show_recovery": False
            })
            st.rerun()

        # Right column intentionally shows no inputs during Sign Up
        st.info("Use the center section for subscription details.")

    # Recovery block (validates existing user, then allows reset)
    elif st.session_state["show_recovery"]:
        email = st.text_input("Enter your username/email", key="recovery_email_expander")

        if st.button("Send Reset Code", key="send_reset_btn_expander"):
            users = st.session_state.get("users", {})
            if email in users:
                code = str(random.randint(100000, 999999))
                st.session_state["reset_code"] = code
                st.session_state["reset_email"] = email
                body = f"Your EduHub password reset code is: {code}"
                send_email(email, "EduHub Password Reset Code", body)
                st.success("✅ Reset code sent to your email.")
            else:
                st.error("❌ Username/email not found.")

        entered_code = st.text_input("Enter the 6-digit code", key="code_input_expander")
        new_password = st.text_input("Enter new password", type="password", key="new_pass_expander")

        if st.button("Reset Password", key="reset_password_btn_expander"):
            if entered_code == st.session_state.get("reset_code", "") and st.session_state.get("reset_email"):
                st.session_state["users"][st.session_state["reset_email"]] = new_password
                save_users(st.session_state["users"])
                st.success("✅ Password reset successful. You can now log in.")
                st.session_state.update({
                    "reset_code": "",
                    "reset_email": "",
                    "show_recovery": False,
                    "show_login": True
                })
                st.rerun()
            else:
                st.error("❌ Invalid reset code.")

    # ✅ Show welcome + membership info here
    if st.session_state["logged_in"]:
        st.markdown(f"👋 Welcome, <strong>{st.session_state['username']}</strong>", unsafe_allow_html=True)
        st.markdown(
            f"📅 Membership: {st.session_state['membership']} | ⏳ Days left: {days_remaining(st.session_state['expiry'])}",
            unsafe_allow_html=True
        )

        # Logout control
        if st.button("Log Out", key="logout_button_right"):
            st.session_state.update({
                "logged_in": False,
                "username": "",
                "membership": "",
                "expiry": "",
                "show_login": True,
                "show_signup": False,
                "show_recovery": False,
                "drive": None
            })
            st.success("You have been logged out.")
            st.rerun()

# -------------------------------
# PART 3: Exams, Folder Tree helpers, and Center display
# -------------------------------

# 🔹 Folder tree helper (define before use)
def show_folder_tree(base_folder):
    folder_path = os.path.join(UPLOAD_ROOT, base_folder)
    if not os.path.exists(folder_path):
        return
    with st.expander(f"📂 {base_folder}", expanded=False):
        subitems = os.listdir(folder_path)
        subfolders = [f for f in subitems if os.path.isdir(os.path.join(folder_path, f))]
        files = [f for f in subitems if os.path.isfile(os.path.join(folder_path, f))]

        # Show subfolders recursively
        for sub in sorted(subfolders):
            show_folder_tree(os.path.join(base_folder, sub))

        # Show files (with Drive link if available)
        for idx, f in enumerate(sorted(files)):
            file_id = st.session_state.get("drive_files", {}).get(f, None)
            if file_id:
                st.markdown(f"[📄 {f}](https://drive.google.com/file/d/{file_id}/view)", unsafe_allow_html=True)
            else:
                st.markdown(f"📄 {f} (No Drive link)")

# Exams display (dynamic, no hardcoding) + subscription message placement
with center_col:
    st.markdown("<h3 style='color:#cc6600;'>📙 Examinations</h3>", unsafe_allow_html=True)

    # When Sign Up is active, show the subscription info card here (center section)
    if st.session_state["show_signup"]:
        st.markdown(
            """
            <div class="subscription-card">
                🚨 <strong style="font-size:20px;">PAY BEFORE YOU PROCEED</strong><br><br>
                📢 To JOIN/SIGN UP, CALL/TEXT/WHATSAPP <strong>0715377466</strong> for log in credentials after payment.<br><br>
                💳 <span style="color:#003366;">Subscription Options:</span><br>
                • <strong style="color:#006600;">KSH 530</strong> → 1 MONTH FULL UNLIMITED ACCESS<br>
                • <strong style="color:#006600;">KSH 830</strong> → 1 YEAR FULL UNLIMITED ACCESS<br><br>
                ✅ Your subscription has no limitations — download all resources without extra charge.<br><br>
                Send money to: <strong>0715377466 (THOMAS)</strong><br>
                Then text your email (or your name) to <strong>0715377466</strong>.<br><br>
                🔑 We will send you login credentials within a minute.
            </div>
            """,
            unsafe_allow_html=True
        )

    # Exams list
    for folder in sorted(get_parent_folders()):
        with st.expander(f"📁 {folder}", expanded=False):
            try:
                files = list_files(folder)
                for file in files:
                    st.markdown(f"- {file}")
            except Exception as e:
                st.error(f"Error loading {folder}: {e}")

# Central folder contents (dynamic)
if st.session_state["logged_in"]:
    if not is_membership_active(st.session_state["expiry"]):
        st.warning("⚠️ Your membership has expired. Please renew to continue accessing resources.")

    st.markdown("<h3 style='color:#003366;'>📂 EduHub Folder Contents</h3>", unsafe_allow_html=True)
    for folder in sorted(get_parent_folders()):
        show_folder_tree(folder)
# -------------------------------
# Admin Panel (Tabbed Layout) — unified, no duplicates
# -------------------------------
if st.session_state.get("membership") == "ADMIN" and st.session_state.get("logged_in"):
    st.markdown("<h3 style='color:#003366;'>🛠️ Admin Panel</h3>", unsafe_allow_html=True)

    # ✅ define all four tabs (only visible to Admin)
    admin_tab, user_tab, folder_tab, file_tab = st.tabs(
        ["Admin Tools", "User Management", "Folder Management", "File Management"]
    )

    # -------------------------------
    # ADMIN TOOLS TAB
    # -------------------------------
    with admin_tab:
        st.markdown("<h4 style='color:#003366;'>⚙️ Admin Tools</h4>", unsafe_allow_html=True)
        st.info("General admin utilities go here.")

        # ✅ Traffic Summary visible only to Admins
        st.markdown("#### 📊 Traffic Summary")
        st.write(f"👥 Total app visits: {visits['total']}")

        views_summary = load_page_views()
        if views_summary:
            for page, count in views_summary.items():
                st.write(f"📄 {page}: {count} views")
        else:
            st.write("No page views yet.")  # ← scoped to Admin only

    # -------------------------------
    # USER MANAGEMENT TAB
    # -------------------------------
    with user_tab:
        st.markdown("<h4 style='color:#003366;'>👥 User Management</h4>", unsafe_allow_html=True)

        # ---------------- SUBSCRIBED MEMBERS LIST ----------------
        st.markdown("<h4 style='color:#003366;'>👥 Subscribed Members</h4>", unsafe_allow_html=True)

        users = load_users()
        st.session_state["users"] = users
        sessions = load_sessions()

        if users:
            table_html = "<table style='width:100%; border-collapse: collapse;'>"
            table_html += "<tr><th>Username/Email</th><th>Active Gadgets</th></tr>"
            for u in users.keys():
                count = count_sessions(u)
                table_html += f"<tr><td>{u}</td><td>{count}</td></tr>"
            table_html += "</table>"
            st.markdown(table_html, unsafe_allow_html=True)
        else:
            st.warning("No subscribed members found.")

        # ➕ Add User controls (keys updated to avoid duplicates)
        new_user = st.text_input("Enter new username/email", key="admin_add_user_input_user_tab")
        new_pass = st.text_input("Assign password", type="password", key="admin_add_pass_input_user_tab")

        if st.button("➕ Add User", key="admin_add_user_btn_user_tab"):
            if new_user and new_pass:
                st.session_state["users"][new_user] = new_pass
                save_users(st.session_state["users"])
                st.success(f"✅ User '{new_user}' created successfully.")
                st.rerun()
            else:
                st.error("Please enter both username/email and password.")
    # -------------------------------
    # FOLDER MANAGEMENT TAB (Parent + Subfolder tools unified)
    # -------------------------------
    with folder_tab:
        st.markdown("<h4 style='color:#003366;'>📁 Manage Parent Folders</h4>", unsafe_allow_html=True)
        parent_folders = get_parent_folders()
        selected_parent = st.selectbox("Select parent folder", parent_folders, key="parent_folder_select_admin")

        colA, colB, colC = st.columns(3)

        with colA:
            new_parent = st.text_input("New parent folder name", key="new_parent_input")
            if st.button("➕ Add Parent Folder", key="add_parent_btn"):
                if new_parent:
                    new_path = os.path.join(UPLOAD_ROOT, new_parent)
                    os.makedirs(new_path, exist_ok=True)
                    st.success(f"✅ Parent folder '{new_parent}' created.")
                    st.rerun()
                else:
                    st.error("Please enter a folder name.")

        with colB:
            del_parent = st.text_input("Delete parent folder", key="del_parent_input")
            if st.button("🗑️ Delete Parent Folder", key="del_parent_btn"):
                if del_parent:
                    del_path = os.path.join(UPLOAD_ROOT, del_parent)
                    if os.path.exists(del_path):
                        shutil.rmtree(del_path)
                        st.success(f"🗑️ Parent folder '{del_parent}' deleted.")
                        st.rerun()
                    else:
                        st.error("Folder not found.")
                else:
                    st.error("Please enter a folder name.")

        with colC:
            rename_parent_old = st.text_input("Parent folder to rename", key="rename_parent_old_input")
            rename_parent_new = st.text_input("New name for parent folder", key="rename_parent_new_input")
            if st.button("✏️ Rename Parent Folder", key="rename_parent_btn"):
                if rename_parent_old and rename_parent_new:
                    old_path = os.path.join(UPLOAD_ROOT, rename_parent_old)
                    new_path = os.path.join(UPLOAD_ROOT, rename_parent_new)
                    if os.path.exists(old_path):
                        os.rename(old_path, new_path)
                        st.success(f"✅ Renamed parent folder '{rename_parent_old}' to '{rename_parent_new}'")
                        st.rerun()
                    else:
                        st.error("Folder not found.")

        st.markdown("<h4 style='color:#003366;'>📂 Manage Subfolders</h4>", unsafe_allow_html=True)
        target_parent = st.selectbox("Select parent folder for subfolders", get_parent_folders(), key="subfolder_parent_select_admin")

        nested_path = os.path.join(UPLOAD_ROOT, target_parent)
        chosen_path = target_parent

        # ✅ Drill down recursively
        while True:
            subfolders = get_subfolders(nested_path)
            if not subfolders:
                break
            choice = st.selectbox(
                f"Select subfolder inside {chosen_path}",
                ["(none)"] + subfolders,
                key=f"nested_{chosen_path}_select"
            )
            if choice == "(none)":
                break
            nested_path = os.path.join(nested_path, choice)
            chosen_path = os.path.join(chosen_path, choice)

        colE, colF, colG = st.columns(3)

        # ---------------- ADD SUBFOLDER ----------------
        with colE:
            subfolder_name = st.text_input("New subfolder name", key="new_subfolder_input")
            if st.button("➕ Add Subfolder", key="add_subfolder_btn"):
                if subfolder_name:
                    sub_path = os.path.join(nested_path, subfolder_name)
                    os.makedirs(sub_path, exist_ok=True)
                    st.success(f"✅ Subfolder '{subfolder_name}' added under '{chosen_path}'")
                    st.rerun()
                else:
                    st.error("Please enter a subfolder name.")

        # ---------------- DELETE SUBFOLDER ----------------
        with colF:
            del_subfolder = st.text_input("Delete subfolder", key="del_subfolder_input")
            if st.button("🗑️ Delete Subfolder", key="del_subfolder_btn"):
                if del_subfolder:
                    sub_path = os.path.join(nested_path, del_subfolder)
                    if os.path.exists(sub_path):
                        shutil.rmtree(sub_path)
                        st.success(f"🗑️ Subfolder '{del_subfolder}' deleted from '{chosen_path}'")
                        st.rerun()
                    else:
                        st.error("Subfolder not found.")
                else:
                    st.error("Please enter a subfolder name.")

        # ---------------- RENAME SUBFOLDER ----------------
        with colG:
            rename_sub_old = st.text_input("Subfolder to rename", key="rename_sub_old_input")
            rename_sub_new = st.text_input("New name for subfolder", key="rename_sub_new_input")
            if st.button("✏️ Rename Subfolder", key="rename_sub_btn"):
                if rename_sub_old and rename_sub_new:
                    old_path = os.path.join(nested_path, rename_sub_old)
                    new_path = os.path.join(nested_path, rename_sub_new)
                    if os.path.exists(old_path):
                        os.rename(old_path, new_path)
                        st.success(f"✅ Renamed subfolder '{rename_sub_old}' to '{rename_sub_new}'")
                        st.rerun()
                    else:
                        st.error("Subfolder not found.")

    # -------------------------------
    # FILE MANAGEMENT TAB
    # -------------------------------
    with file_tab:
        st.markdown("<h4 style='color:#003366;'>📄 Manage Files</h4>", unsafe_allow_html=True)
        parent_folders = get_parent_folders()
        target_parent = st.selectbox("Select parent folder", parent_folders, key="file_parent_select_admin")

        nested_path = os.path.join(UPLOAD_ROOT, target_parent)
        chosen_path = target_parent

        while True:
            subfolders = get_subfolders(nested_path)
            if not subfolders:
                break
            choice = st.selectbox(
                f"Select subfolder inside {chosen_path}",
                ["(none)"] + subfolders,
                key=f"file_nested_{chosen_path}_select"
            )
            if choice == "(none)":
                break
            nested_path = os.path.join(nested_path, choice)
            chosen_path = os.path.join(chosen_path, choice)

        colH, colI, colJ = st.columns(3)

        # ---------------- UPLOAD FILE ----------------
        with colH:
            uploaded_file = st.file_uploader("Upload new file", key="file_upload_input")
            if uploaded_file is not None:
                save_path = os.path.join(nested_path, uploaded_file.name)
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success(f"✅ File '{uploaded_file.name}' uploaded to '{chosen_path}'")

                if st.session_state.get("drive"):
                    file_id = upload_to_drive(st.session_state["drive"], save_path, uploaded_file.name)
                    st.session_state["drive_files"][uploaded_file.name] = file_id
                    save_drive_files(st.session_state["drive_files"])
                    st.success(f"☁️ File '{uploaded_file.name}' also uploaded to Google Drive.")
                st.rerun()

        # ---------------- DELETE FILE ----------------
        with colI:
            del_file = st.text_input("Delete file name", key="del_file_input")
            if st.button("🗑️ Delete File", key="del_file_btn"):
                if del_file:
                    del_path = os.path.join(nested_path, del_file)
                    if os.path.exists(del_path):
                        os.remove(del_path)
                        st.success(f"🗑️ File '{del_file}' deleted from '{chosen_path}'")
                        st.rerun()
                    else:
                        st.error("File not found.")
                else:
                    st.error("Please enter a file name to delete.")

        # ---------------- RENAME FILE ----------------
        with colJ:
            old_file = st.text_input("File to rename", key="rename_file_old_input")
            new_file = st.text_input("New name for file", key="rename_file_new_input")
            if st.button("✏️ Rename File", key="rename_file_btn"):
                if old_file and new_file:
                    old_path = os.path.join(nested_path, old_file)
                    new_path = os.path.join(nested_path, new_file)
                    if os.path.exists(old_path):
                        os.rename(old_path, new_path)
                        st.success(f"✅ Renamed file '{old_file}' to '{new_file}'")
                        st.rerun()
                    else:
                        st.error("File not found.")
                else:
                    st.error("Please enter both old and new file names.")

# -------------------------------
# Footer (full-width, text shifted right to avoid sidebar overlap)
# -------------------------------
st.markdown(
    """
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100vw;   /* full viewport width */
        background: linear-gradient(90deg, #003366, #006699);
        color: white;
        text-align: center;
        padding: 14px 0;
        font-size: 15px;
        font-family: "Trebuchet MS", Arial, sans-serif;
        box-shadow: 0 -2px 6px rgba(0,0,0,0.2);
        z-index: 1000;
    }
    .footer-content {
        margin-left: 220px; /* shift text to the right to clear sidebar */
    }
    .footer strong {
        color: #ffcc00;
    }
    </style>
    <div class="footer">
        <div class="footer-content">
            Powered by <strong>Mr. Thomas Nyagiro</strong> © 2025 EduHub Learning Resources |
            Designed By a Teacher For Teachers and Learners.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

