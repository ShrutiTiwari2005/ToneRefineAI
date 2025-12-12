# ToneRefine AI

Refines any message/email by fixing **spelling + grammar** and converting it to a chosen **tone** (Polite, Professional, Friendly, Apologetic).  
Built with **Streamlit + FLAN-T5 (small) + PySpellChecker**. Runs on CPU.

## Features
- Auto greeting & name title-case
- Spell/grammar cleanup
- Tone transform (LLM) + tone enforcement
- Login/Signup + History (JSON)

## How to run
```bash
pip install -r requirements.txt
streamlit run app.py
