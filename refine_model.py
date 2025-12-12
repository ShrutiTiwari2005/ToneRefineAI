# refine_model.py — FINAL (All tones; CPU-friendly)
# -------------------------------------------------
# ✔ Spelling/grammar pre-clean (auto greeting+name handling)
# ✔ Smart rewrite via FLAN-T5-small (fast on Acer i5)
# ✔ Anti-echo + strong tone-enforcement (Polite/Professional/Friendly/Apologetic)
# ✔ Tone synonyms → canonical mapping

import re
from typing import List, Tuple

# ===================== Token helpers =====================
WORD = r"[A-Za-z]+(?:'[A-Za-z]+)?"
NUM  = r"\d+"
PUNC = r"[^\w\s]"

def _tokenize(s: str) -> List[str]:
    return re.findall(fr"{WORD}|{NUM}|{PUNC}", s, flags=re.UNICODE)

def _join_tokens(toks: List[str]) -> str:
    out = []
    for i, t in enumerate(toks):
        if i > 0 and re.match(r"[A-Za-z0-9]", t) and re.match(r"[A-Za-z0-9)\]]", toks[i-1]):
            out.append(" ")
        out.append(t)
    return "".join(out)

# ===================== Spelling / Grammar pre-clean =====================
try:
    from spellchecker import SpellChecker  # type: ignore[import-not-found]
    _sp = SpellChecker(distance=1)  # conservative corrections
except Exception:
    _sp = None  # library missing → skip spell-fix gracefully

_GREET_CANON = {"hello", "hi", "hey", "dear"}
_GREET_NOISY = _GREET_CANON | {"helo", "helloo", "hii", "heyy", "dearr"}

def _canon_greeting(tok: str) -> str:
    low = tok.lower()
    if low in _GREET_NOISY:
        if low.startswith("dear"): return "Dear"
        if low.startswith("hi"):   return "Hi"
        if low.startswith("hey"):  return "Hey"
        return "Hello"
    if _sp:
        corr = _sp.correction(low)
        if corr in _GREET_CANON:
            return corr.capitalize()
    return ""

def _detect_greeting_and_name(toks: List[str]) -> Tuple[int, int, str]:
    # pattern: <greeting> <name …> ,  (comma/newline ends name)
    if not toks: return -1, -1, ""
    g = _canon_greeting(toks[0])
    if not g:    return -1, -1, ""
    i = 1
    while i < len(toks):
        if toks[i] in {",", "\n"}:
            i += 1
            break
        if toks[i] in {".", "!", "?"}:
            break
        i += 1
    return 0, i, g

def _titlecase_name_segment(toks: List[str], start: int, end: int) -> None:
    for i in range(start, end):
        t = toks[i]
        if re.fullmatch(WORD, t, flags=re.UNICODE):
            parts = t.split("'")
            parts = [p.capitalize() if p else p for p in parts]
            toks[i] = "'".join(parts)

def _preclean_text(text: str) -> str:
    """Light normalization + greeting/name + conservative spelling fix."""
    s = (text or "").strip()
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\s*\n\s*", "\n", s)

    # common fixes
    s = re.sub(r"\bi\b", "I", s)
    s = re.sub(r"\bdont\b", "don't", s, flags=re.I)
    s = re.sub(r"\bcant\b", "can't", s, flags=re.I)
    s = re.sub(r"\bim\b", "I'm", s, flags=re.I)
    s = re.sub(r"\bwon t\b", "won't", s, flags=re.I)
    s = re.sub(r"\bcan not\b", "cannot", s, flags=re.I)

    toks = _tokenize(s)

    # 1) greeting + name
    g_idx, name_end, gcanon = _detect_greeting_and_name(toks)
    if g_idx == 0 and gcanon:
        toks[0] = gcanon
        _titlecase_name_segment(toks, 1, name_end - 1)

    # 2) spelling with auto name protection
    if _sp:
        fixed = []
        for i, t in enumerate(toks):
            low = t.lower()
            if re.fullmatch(PUNC, t) or t.isdigit() or re.search(r"\d", t):
                fixed.append(t); continue
            if i == 0 and gcanon:
                fixed.append(t); continue
            if g_idx == 0 and i in range(1, name_end - 1):
                fixed.append(t); continue
            if t[:1].isupper() and t[1:].islower():   # likely name mid-sentence
                fixed.append(t); continue
            if len(t) <= 2:
                fixed.append(t); continue
            corr = _sp.correction(low)
            fixed.append(corr if corr else t)
        toks = fixed

    text2 = _join_tokens(toks)

    # 3) sentence case
    def _sent_case(m):
        lead = m.group(1); ch = m.group(2)
        return f"{lead}{ch.upper()}"
    text2 = re.sub(r"(^|\.\s+|\!\s+|\?\s+)([a-z])", _sent_case, text2)

    # 4) ensure terminator
    if text2 and text2[-1] not in ".!?":
        text2 += "."
    return text2

# ===================== Tone mapping & enforcement =====================
_CANON = {
    "polite": "Polite",
    "professional": "Professional",
    "friendly": "Friendly",
    "apologetic": "Apologetic",
}
# synonyms → canonical
_ALIASES = {
    "formal": "Professional",
    "business": "Professional",
    "official": "Professional",
    "casual": "Friendly",
    "warm": "Friendly",
    "sorry": "Apologetic",
}

def _canonical_tone(tone: str) -> str:
    if not tone: return "Professional"
    low = tone.lower().strip()
    if low in _CANON: return _CANON[low]
    if low in _ALIASES: return _ALIASES[low]
    # fallback: first letter caps
    return low.capitalize()

def _enforce_tone(out: str, tone: str) -> str:
    """Post-processor to guarantee requested tone markers while concise."""
    s = (out or "").strip()
    s = re.sub(r"\s+", " ", s)

    # soften/normalize a few rough phrases
    replacements = [
        (r"\bi am not come\b", "I will not be able to come"),
        (r"\bi am not coming\b", "I will not be able to come"),
        (r"\bdont\b", "don't"),
        (r"\bdo not call me now\b", "please call me later"),
        (r"\bdon't call me now\b", "please call me later"),
        (r"\bi m\b", "I am"),
    ]
    for pat, rep in replacements:
        s = re.sub(pat, rep, s, flags=re.I)

    def ensure_end(x: str) -> str:
        return x if not x or x[-1] in ".!?" else x + "."

    def ensure_phrase(x: str, needles, insert):
        if not any(n in x.lower() for n in needles):
            x = x.rstrip(".!?")
            x = f"{x} {insert}."
        return x

    ct = _canonical_tone(tone)

    if ct == "Polite":
        s = ensure_phrase(s, ["please", "could you", "kindly"], "Could you please")
        s = ensure_phrase(s, ["thank you", "thanks"], "Thank you")
        s = re.sub(r"\bwon't\b", "will not", s, flags=re.I)

    elif ct == "Professional":
        conv = [(r"\bI'm\b","I am"), (r"\bcan't\b","cannot"),
                (r"\bwon't\b","will not"), (r"\bn't\b"," not")]
        for pat, rep in conv: s = re.sub(pat, rep, s, flags=re.I)
        s = re.sub(r"[🙂😊😅🙃]+", "", s)
        s = s.replace("!", "")
        s = ensure_phrase(s, ["please","kindly"], "Please")

    elif ct == "Friendly":
        s = s.replace("Please do not", "Please don't")
        s = ensure_phrase(s, ["thanks","thank you"], "Thanks")

    elif ct == "Apologetic":
        if "apolog" not in s.lower() and "sorry" not in s.lower():
            s = f"I’m sorry for the inconvenience. {s}"
        s = ensure_phrase(s, ["thank you for understanding","thank you"], "Thank you for understanding")

    return ensure_end(s.strip())

# ===================== Public API =====================
USE_SMART = True  # Dashboard toggle will set this
_MODEL_NAME = "google/flan-t5-small"  # fast on CPU; use "google/flan-t5-base" for higher quality

def refine_tone(text: str, tone: str) -> str:
    """
    2-pass pipeline:
      1) super-fast local cleanup (spelling, basic grammar, greeting/name)
      2) Smart LLM rewrite for target tone (if enabled) with tone enforcement;
         else concise rule-based fallback (also tone-enforced)
    """
    cleaned = _preclean_text(text)
    ct = _canonical_tone(tone)

    if USE_SMART:
        return _smart_rewrite(cleaned, ct)

    # FAST fallback (no LLM)
    if ct == "Professional":
        return _enforce_tone(f"{cleaned} Please address this at your earliest convenience. Thank you for your cooperation.", ct)
    if ct == "Polite":
        return _enforce_tone(f"{cleaned} Could you please look into this at your earliest convenience? Thank you.", ct)
    if ct == "Friendly":
        return _enforce_tone(f"{cleaned} Just a heads-up—thanks a lot!", ct)
    if ct == "Apologetic":
        return _enforce_tone(f"I’m sorry for the inconvenience. {cleaned} Thank you for understanding.", ct)
    return _enforce_tone(cleaned, ct)

# ===================== SMART backend (FLAN-T5 small) =====================
_tok = None
_mdl = None

def _load_smart():
    global _tok, _mdl
    if _tok is None:
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        _tok = AutoTokenizer.from_pretrained(_MODEL_NAME)
        _mdl = AutoModelForSeq2SeqLM.from_pretrained(_MODEL_NAME)  # CPU load
    return _tok, _mdl

def _smart_rewrite(text: str, tone: str) -> str:
    tok, mdl = _load_smart()

    # safer prompt: no "Input/Rewrite" labels (prevents literal echoes)
    prompt = (
        "You are a professional email editor.\n"
        f"Rewrite the following message in a {tone} tone.\n"
        "Fix spelling, grammar, and capitalization.\n"
        "Preserve the original meaning; do not add new facts.\n"
        "Return only the final polished message.\n\n"
        f"Message:\n{text}\n\n"
        "Final polished message:"
    )

    ids = tok(prompt, return_tensors="pt", truncation=True, max_length=448)

    # Pass-1: deterministic beams (CPU-friendly, reduces copy)
    out = mdl.generate(
        **ids,
        do_sample=False,
        num_beams=4,
        length_penalty=0.95,
        repetition_penalty=1.08,
        early_stopping=True,
        max_new_tokens=140,
    )

    def _clean(s: str) -> str:
        s = s.replace("Final polished message:", "")
        s = s.replace("final polished message:", "")
        s = s.replace("Polished message:", "")
        s = s.replace("Message:", "")
        s = s.replace("INPUT", "").replace("Input", "")
        s = re.sub(r"\s+\n", "\n", s)
        return s.strip()

    txt1 = _clean(tok.decode(out[0], skip_special_tokens=True))

    # Anti-echo: if output ~ input, sample few and pick best non-echo
    def _norm(s: str) -> List[str]:
        return re.sub(r"[\W_]+", " ", s.lower()).split()
    if abs(len(set(_norm(txt1)) ^ set(_norm(text)))) <= 2:
        out2 = mdl.generate(
            **ids,
            do_sample=True, top_p=0.9, temperature=0.6,
            num_return_sequences=3, num_beams=1, max_new_tokens=140,
        )
        cands = [_clean(tok.decode(o, skip_special_tokens=True)) for o in out2]
        for c in cands:
            if abs(len(set(_norm(c)) ^ set(_norm(text)))) > 2:
                return _enforce_tone(c, tone)

    return _enforce_tone(txt1, tone)
