import streamlit as st

st.set_page_config(page_title="ToneRefine AI", layout="centered")

if "user" not in st.session_state:
    st.switch_page("pages/Login.py")
else:
    st.switch_page("pages/Dashboard.py")
