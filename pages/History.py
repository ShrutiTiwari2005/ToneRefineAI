import streamlit as st, json, os

st.title("📚 History")

if "user" not in st.session_state:
    st.switch_page("pages/Login.py")

def _safe(u: str) -> str:
    s = "".join(c for c in (u or "") if c.isalnum())
    return s or "user"

username = _safe(st.session_state.user)
DATA_DIR = "user_data"
HFILE = os.path.join(DATA_DIR, f"{username}_history.json")

if not os.path.exists(HFILE):
    st.info("No history yet.")
else:
    with open(HFILE, "r", encoding="utf-8") as f:
        hist = json.load(f)
    if not hist:
        st.info("No history yet.")
    else:
        for item in reversed(hist[-100:]):
            st.markdown(f"**{item['time']} — {item['tone']}**")
            st.write("**Original:**"); st.code(item["input"])
            st.write("**Refined:**"); st.success(item["output"])
            st.divider()
