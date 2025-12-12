import streamlit as st
from auth import authenticate

st.title("🔑 Login")

if "user" in st.session_state:
    st.switch_page("pages/Dashboard.py")

u = st.text_input("Username")
p = st.text_input("Password", type="password")

col1, col2 = st.columns(2)
if col1.button("Login"):
    if authenticate(u, p):
        st.session_state.user = u
        st.switch_page("pages/Dashboard.py")
    else:
        st.error("Invalid username or password.")

if col2.button("Create an account"):
    st.switch_page("pages/Signup.py")
