import streamlit as st
from auth import create_user, user_exists

st.title("🧾 Sign up")

u = st.text_input("Choose a username")
p = st.text_input("Choose a password", type="password")
p2 = st.text_input("Confirm password", type="password")

if st.button("Create account"):
    if not u or not p:
        st.error("Please fill all fields.")
    elif p != p2:
        st.error("Passwords do not match.")
    elif user_exists(u):
        st.error("Username already exists.")
    else:
        if create_user(u, p):
            st.success("Account created. Please login.")
            st.switch_page("pages/Login.py")
        else:
            st.error("Could not create account. Try a different username.")
