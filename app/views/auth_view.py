"""
Streamlit Authentication UI View for EduHyperRAG.
Provides user login and registration forms for Teachers and Students.
"""

import streamlit as st
from src.auth.authenticator import authenticate_user, login_user, register_user


def render_auth_view() -> None:
    """Renders Login and Signup tabs."""
    st.markdown("## 🔐 EduHyperRAG Portal Access")
    st.write("Welcome! Please log in or create an account to access the AI Tutor platform.")

    tab_login, tab_signup = st.tabs(["🔑 Login", "📝 Create Account"])

    # -------------------------------------------------------------------------
    # TAB 1: LOGIN FORM
    # -------------------------------------------------------------------------
    with tab_login:
        st.subheader("Account Login")
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="e.g. teacher or student")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit_login = st.form_submit_button("Log In", type="primary")

            if submit_login:
                if not username.strip() or not password.strip():
                    st.warning("Please provide both username and password.")
                else:
                    user = authenticate_user(username, password)
                    if user:
                        login_user(user)
                        st.success(f"Welcome back, {user['username']}! ({user['role'].capitalize()})")
                        st.rerun()
                    else:
                        st.error("Invalid username or password. Please try again.")

        st.info("💡 **Demo Credentials**:\n- **Teacher**: Username `teacher` \| Password `password123`\n- **Student**: Username `student` \| Password `password123`")

    # -------------------------------------------------------------------------
    # TAB 2: SIGNUP FORM
    # -------------------------------------------------------------------------
    with tab_signup:
        st.subheader("New User Registration")
        with st.form("signup_form"):
            new_username = st.text_input("Choose Username")
            new_email = st.text_input("Email Address")
            new_password = st.text_input("Choose Password (min 6 chars)", type="password")
            role = st.selectbox("Select Account Role", ["student", "teacher"])
            submit_signup = st.form_submit_button("Register Account")

            if submit_signup:
                if not new_username.strip() or not new_email.strip() or not new_password.strip():
                    st.warning("Please fill in all fields.")
                else:
                    try:
                        user = register_user(
                            username=new_username,
                            email=new_email,
                            password=new_password,
                            role=role,
                        )
                        st.success(f"Account successfully created for '{user['username']}'! You can now log in.")
                    except ValueError as err:
                        st.error(str(err))
