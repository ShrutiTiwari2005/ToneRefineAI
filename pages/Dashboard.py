import streamlit as st
import json, os, datetime, time

import refine_model
from refine_model import refine_tone

st.title("📧 ToneRefine AI — Grammar + Tone Polisher")

# ---------- Auth gate ----------
if "user" not in st.session_state:
    st.switch_page("pages/Login.py")

def _safe_user(u: str) -> str:
    s = "".join(c for c in (u or "") if c.isalnum())
    return s or "user"

username = _safe_user(st.session_state.user)

# ---------- History setup ----------
DATA_DIR = "user_data"
os.makedirs(DATA_DIR, exist_ok=True)
HFILE = os.path.join(DATA_DIR, f"{username}_history.json")

def _read_hist():
    if not os.path.exists(HFILE): return []
    try:
        with open(HFILE, "r", encoding="utf-8") as f: return json.load(f)
    except Exception: return []

def _write_hist(data):
    with open(HFILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

if not os.path.exists(HFILE): _write_hist([])

# ---------- UI ----------
st.subheader("✍️ Enter your text")
text = st.text_area("Your message:", height=180, placeholder="hello marty, i am not coming tomorow…")
st.caption(f"Characters: {len(text)}")

tone = st.selectbox("Target tone", ["Professional", "Polite", "Friendly", "Apologetic"])

smart = st.toggle("Use Smart LLM (FLAN-T5 small)", value=True)
refine_model.USE_SMART = smart
st.caption(f"Mode: {'SMART (LLM)' if smart else 'FAST (Rule-based)'}")

if st.button("✨ Refine Tone"):
    if not text.strip():
        st.error("Please enter some text.")
    else:
        with st.spinner("Refining…"):
            t0 = time.time()
            out = refine_tone(text, tone)
            dur = time.time() - t0
        st.subheader("🎉 Refined Output")
        st.text_area("Output", out, height=160)
        st.caption(f"Time: {dur:.2f}s  •  Model: {'FLAN-T5 small' if smart else 'Rule'}")

        # save
        hist = _read_hist()
        hist.append({
            "time": datetime.datetime.now().isoformat(timespec="seconds"),
            "tone": tone, "input": text, "output": out
        })
        _write_hist(hist)
        st.toast("Saved to history.", icon="✅")

if st.button("📚 View History"):
    hist = _read_hist()
    if not hist:
        st.info("No history yet.")
    else:
        for item in reversed(hist[-100:]):
            st.markdown(f"**{item['time']} — {item['tone']}**")
            st.write("**Original:**"); st.code(item["input"])
            st.write("**Refined:**"); st.success(item["output"])
            st.divider()

if st.button("🚪 Logout"):
    st.session_state.pop("user", None)
    st.switch_page("pages/Login.py")
