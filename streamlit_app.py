import os
import re
import time
import base64
import requests
import streamlit as st

st.set_page_config(
    page_title="ג'מי תורה - עוזר הלכה ובינה מלאכותית תורנית",
    page_icon="📜",
    layout="wide"
)

# ── קבועי תצורה ────────────────────────────────────────────────
MODELS = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-pro"]
SEFARIA_DEEP     = 6
SEFARIA_QUICK    = 3
REQUEST_TIMEOUT  = 90
TEMPERATURE      = 0.65
KITZUR_MAX_CHARS = 1500
KITZUR_SECTIONS  = 3
HISTORY_MAX      = 5
GEMINI_BASE      = "https://generativelanguage.googleapis.com/v1beta/models"
SEFARIA_URL      = "https://www.sefaria.org/api/search-wrapper"

SYSTEM_DEEP = """אתה ג'מי תורה — מנוע בינה מלאכותית תורני ברמת גדול הדור.
חובה לבסס את תשובתך על המקורות שצורפו.
כללי תשובה:
א. פתח בפסוק או מאמר חז"ל רלוונטי.
ב. חלק לסעיפים ברורים עם כותרות מודגשות.
ג. ציין מקורות מדויקים: שם ספר + פרק + סעיף/דף.
ד. הצג דעות שונות כשיש מחלוקת.
ה. סיים ב"למעשה..." — סיכום מעשי ברור.
כתוב בעברית בלבד. תשובה מקיפה — אל תקצר."""

SYSTEM_QUICK = """אתה ג'מי תורה — עוזר תורני ממוקד ומהיר.
ענה תשובה קצרה ותמציתית (עד 3-4 משפטים).
בסס על המקורות שצורפו. ציין שם המקור בלבד. אל תרחיב."""

CSS = """
<style>
body,p,div,h1,h2,h3,h4,h5,h6,li,span,input,label,textarea,
.stMarkdown,.stAlert,.stTextInput label {
    direction:rtl !important; text-align:right !important;
    font-family:'Segoe UI',Arial,sans-serif;
}
.block-container {
    padding-top:2rem !important; padding-bottom:2rem !important;
    padding-left:5rem !important; padding-right:5rem !important;
    max-width:1100px !important;
}
.premium-header {
    background:linear-gradient(135deg,#0b151f,#142436);
    border-bottom:3px solid #c5a059; padding:36px 40px; border-radius:16px;
    box-shadow:0 10px 30px rgba(0,0,0,0.3); margin-bottom:30px;
    display:flex; justify-content:space-between; align-items:center; gap:24px;
}
.premium-header h1 {
    color:#f4ecd8 !important; font-size:2.8rem !important;
    font-weight:800; margin:0 0 8px 0 !important; white-space:nowrap;
}
.premium-header p { color:#c5a059 !important; font-size:1.2rem !important; margin:0 !important; }
.rabbi-banner-img {
    width:200px; border-radius:14px;
    border:3px solid #c5a059; box-shadow:0 6px 25px rgba(0,0,0,0.5); flex-shrink:0;
}
@media (max-width:768px) {
    .block-container { padding-left:1rem !important; padding-right:1rem !important; }
    .premium-header {
        flex-direction:column !important; align-items:center !important;
        padding:24px 20px !important; gap:16px !important;
    }
    .premium-header h1 { font-size:2rem !important; text-align:center !important; white-space:normal !important; }
    .premium-header p  { text-align:center !important; }
    .rabbi-banner-img  { width:130px !important; }
}
.stTextInput > div > div > input {
    direction:rtl !important; text-align:right !important;
    border:2px solid #223446 !important; border-radius:12px !important;
    padding:16px 20px !important; font-size:17px !important;
    background-color:#0f1923 !important; color:#ffffff !important;
}
.stTextInput > div > div > input:focus { border-color:#c5a059 !important; }
.stButton > button {
    direction:rtl !important; border-radius:10px !important;
    border:1.5px solid #c5a059 !important; background:transparent !important;
    color:#c5a059 !important; font-size:13px !important; width:100% !important;
}
.stButton > button:hover { background:#c5a059 !important; color:#0b151f !important; }
.answer-box {
    background:#0f1923; border:1px solid #223446; border-radius:14px;
    border-right:5px solid #c5a059; padding:28px 32px; color:#f0e6d3;
    font-size:16px; line-height:2; direction:rtl; text-align:right;
}
.answer-box-quick {
    background:#0f1923; border:1px solid #c5a059; border-radius:12px;
    padding:20px 24px; color:#f0e6d3; font-size:15px; line-height:1.9;
    direction:rtl; text-align:right;
}
.source-box {
    background:#0d1e2e; border-right:4px solid #c5a059;
    border-radius:8px; padding:12px 16px; margin-bottom:10px;
}
.source-ref  { color:#c5a059; font-weight:700; font-size:14px; margin-bottom:4px; }
.source-text { color:#c8bfa8; font-size:13px; line-height:1.7; }
.debug-line {
    font-family:monospace; font-size:11px; color:#4a9960;
    background:#0a1a0a; border:1px solid #1a3a1a; border-radius:6px;
    padding:4px 10px; margin-bottom:12px; direction:ltr; text-align:left;
}
#MainMenu,footer,header { visibility:hidden !important; }
[data-testid="manage-app-button"],[data-testid="stToolbarActions"],
[data-testid="stToolbar"],.stDeployButton { display:none !important; }
</style>
<script>
(function(){
    const h=()=>{
        ['[data-testid="manage-app-button"]','[data-testid="stToolbarActions"]',
         '[data-testid="stToolbar"]','.stDeployButton','footer']
        .forEach(s=>document.querySelectorAll(s)
        .forEach(el=>el.style.setProperty('display','none','important')));
    };
    new MutationObserver(h).observe(document.documentElement,{childList:true,subtree:true});
    h();setTimeout(h,1000);setTimeout(h,3000);
})();
</script>
"""

SAFETY = [
    {"category": "HARM_CATEGORY_HATE_SPEECH",       "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HARASSMENT",        "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# ── עזרים ──────────────────────────────────────────────────────
def get_base64_image(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def strip_html(text):
    return re.sub(r'<[^>]+>', ' ', text).strip()

def clean_query(query):
    return re.sub(
        r'\b(מה|האם|כיצד|למה|מדוע|איך|מתי|היכן|מי|הסבר|פרט|ספר)\b',
        '', query
    ).strip()

def get_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        try:
            key = str(st.secrets["GEMINI_API_KEY"]).strip()
        except Exception:
            st.error("⚠️ מפתח API לא נמצא. הגדר GEMINI_API_KEY ב-Secrets.")
            st.stop()
    if len(key) < 10:
        st.error("⚠️ המפתח קצר מדי. בדוק את ה-Secrets.")
        st.stop()
    return key

def search_local_kitzur(query: str) -> str:
    try:
        if not os.path.exists("kitzur_shulchan_aruch.txt"):
            return ""
        with open("kitzur_shulchan_aruch.txt", "r", encoding="utf-8", errors="ignore") as f:
            lines = f.read().split("\n")
        keywords = [w for w in query.split() if len(w) > 2]
        if not keywords:
            return ""
        scored = []
        for i, line in enumerate(lines):
            score = sum(1 for kw in keywords if kw in line)
            if score > 0:
                section = "\n".join(lines[max(0, i-1):min(len(lines), i+5)]).strip()
                if len(section) > 20:
                    scored.append((score, section))
        if not scored:
            return ""
        scored.sort(key=lambda x: x[0], reverse=True)
        return "\n\n".join(s for _, s in scored[:KITZUR_SECTIONS])[:KITZUR_MAX_CHARS]
    except Exception:
        return ""

def search_sefaria(query: str, size: int) -> list:
    seen, results = set(), []
    def _fetch(q):
        try:
            r = requests.get(
                SEFARIA_URL,
                params={"query": q, "type": "text", "size": size, "field": "naive_lemmatizer"},
                timeout=7
            )
            for hit in r.json().get("hits", {}).get("hits", []):
                src = hit.get("_source", {})
                ref = src.get("ref", "")
                he  = strip_html(src.get("he", ""))
                if ref and he and len(he) > 15 and ref not in seen:
                    seen.add(ref)
                    results.append({
                        "heRef": src.get("heRef", ref),
                        "he":    he[:400] + ("..." if len(he) > 400 else "")
                    })
        except Exception:
            pass
    _fetch(query)
    kw = clean_query(query)
    if kw and kw != query:
        _fetch(kw)
    return results[:size]

def call_gemini(api_key: str, prompt: str, system: str) -> tuple[str, str]:
    """
    קריאה ל-Gemini REST API.
    מנסה 3 שיטות אימות שונות — חשוב במיוחד למפתחות בפורמט AQ.
    מחזיר (תשובה, שיטת_אימות_שעבדה)
    """
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": system}]},
        "generationConfig": {"temperature": TEMPERATURE, "maxOutputTokens": 4096},
        "safetySettings": SAFETY,
    }

    # שלוש שיטות אימות — הקוד ינסה כל אחת
    auth_methods = [
        ("x-goog-api-key header",
         {"x-goog-api-key": api_key, "Content-Type": "application/json"},
         {}),
        ("Bearer token",
         {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
         {}),
        ("?key= query param",
         {"Content-Type": "application/json"},
         {"key": api_key}),
    ]

    last_err = ""
    for model in MODELS:
        for method_name, headers, params in auth_methods:
            for attempt in range(2):
                try:
                    url  = f"{GEMINI_BASE}/{model}:generateContent"
                    resp = requests.post(
                        url,
                        headers=headers,
                        params=params,
                        json=payload,
                        timeout=REQUEST_TIMEOUT,
                    )

                    if resp.status_code == 200:
                        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                        return text, f"{model} via {method_name}"

                    err_body  = resp.json()
                    code      = err_body.get("error", {}).get("code", resp.status_code)
                    msg       = err_body.get("error", {}).get("message", "")
                    last_err  = f"{code}: {msg[:200]}"

                    if code == 429:
                        time.sleep(2 ** attempt * 5)
                    elif code in (400, 404, 401, 403):
                        break  # נסה שיטה/מודל הבא
                    else:
                        time.sleep(3)

                except requests.exceptions.Timeout:
                    last_err = "timeout"
                    break
                except Exception as e:
                    last_err = str(e)[:200]
                    break

    raise Exception(last_err)

# ── ממשק ─────────────────────────────────────────────────────────
st.markdown(CSS, unsafe_allow_html=True)
api_key = get_api_key()

# DEBUG: מציג מפתח וסוגו
key_type = "AQ. (new format)" if api_key.startswith("AQ.") else "AIzaSy (classic)" if api_key.startswith("AIza") else "unknown"
st.markdown(
    f'<div class="debug-line">🔑 KEY: {api_key[:12]}... | LEN: {len(api_key)} | TYPE: {key_type}</div>',
    unsafe_allow_html=True
)

rabbi_base64 = get_base64_image("rabbi.jpeg") or get_base64_image("rabbi.png")
img_tag = (
    f'<img src="data:image/jpeg;base64,{rabbi_base64}" class="rabbi-banner-img" />'
    if rabbi_base64 else ''
)
st.markdown(f"""
<div class="premium-header">
  <div>
    <h1>ג&#39;מי תורה 📜</h1>
    <p>מנוע חיפוש, פסיקה ולימוד מבוסס מקורות</p>
  </div>
  {img_tag}
</div>""", unsafe_allow_html=True)

for k in ["history", "deep_q", "quick_q", "deep_ans", "quick_ans", "_last_deep", "_last_quick"]:
    if k not in st.session_state:
        st.session_state[k] = [] if k == "history" else ""

st.markdown('<p style="color:#c5a059;font-weight:600;">💡 שאלות לדוגמה:</p>', unsafe_allow_html=True)
EXAMPLES = [
    "מה הלכות שבת לגבי חשמל?",
    "מקור מצוות כיבוד אב ואם",
    "דיני אבילות שבעה",
    "הלכות כשרות בסיסיות",
]
for i, (col, q) in enumerate(zip(st.columns(4), EXAMPLES)):
    if col.button(q, key=f"ex_{i}", use_container_width=True):
        st.session_state.update({
            "deep_q": q, "quick_q": q,
            "deep_ans": "", "quick_ans": "",
            "_last_deep": "", "_last_quick": "",
        })
        st.rerun()

tab_deep, tab_quick = st.tabs([
    "🏛️   עיון מעמיק — תשובה מפורטת",
    "⚡   בירור מהיר — תשובה תמציתית",
])

def show_sources(sources):
    if not sources:
        return
    html = "".join(
        f'<div class="source-box">'
        f'<div class="source-ref">📖 {s["heRef"]}</div>'
        f'<div class="source-text">{s["he"]}</div>'
        f'</div>'
        for s in sources
    )
    with st.expander(f"📚 {len(sources)} מקורות ממאגר ספריא", expanded=False):
        st.markdown(html, unsafe_allow_html=True)

def build_context(kitzur, sources) -> str:
    parts = []
    if kitzur:
        parts.append(f"מתוך קיצור שולחן ערוך:\n{kitzur}")
    if sources:
        src_str = "\n\n".join(
            f"[{i+1}] {s['heRef']}: {s['he']}" for i, s in enumerate(sources)
        )
        parts.append(f"מקורות ממאגר ספריא:\n{src_str}")
    if parts:
        parts.append("התבסס על מקורות אלו וציין אותם.")
    return "\n\n".join(parts)

def handle_error(err: str, api_key: str):
    if "401" in err or "403" in err or "UNAUTHENTICATED" in err or "PERMISSION_DENIED" in err:
        st.error(
            f"⚠️ **שגיאת אימות**\n\n"
            f"המפתח `{api_key[:12]}...` לא מתקבל על ידי גוגל.\n\n"
            "**פתרון:** כנס ל-aistudio.google.com ← בדוק שהמפתח פעיל ← העתק מחדש ← עדכן Secrets"
        )
    elif "429" in err or "RESOURCE_EXHAUSTED" in err or "quota" in err.lower():
        st.error(
            "⚠️ **מכסת ה-API אזלה (429)**\n\n"
            "**חינם:** Gmail חדש → aistudio.google.com → מפתח חדש → Secrets → Reboot\n\n"
            "**קבוע:** billing ב-console.cloud.google.com ($5 = 50,000+ בקשות)"
        )
    elif "timeout" in err.lower():
        st.error("⏱️ **פסק זמן** — נסה שוב.")
    else:
        st.error(f"❌ שגיאה: {err}")

# ════════════════════ TAB 1 — עיון מעמיק ════════════════════════
with tab_deep:
    st.markdown(
        '<p style="color:#c5a059;font-weight:600;margin-top:8px;">'
        'חיפוש נרחב מ-6 מקורות, תשובה מפורטת עם כל הדעות</p>',
        unsafe_allow_html=True
    )
    q_deep = st.text_input(
        "🔮 שאל שאלת עיון או סוגיה:",
        value=st.session_state.deep_q,
        key="input_deep"
    )
    st.markdown(
        '<div style="color:#7a7a7a;font-size:12px;font-style:italic;">'
        '⚠️ לעניין הלכה למעשה — יש להיוועץ ברב מורה הוראה.</div>',
        unsafe_allow_html=True
    )

    if st.session_state.deep_ans:
        st.markdown("### ✍️ תשובת ג'מי תורה:")
        st.markdown(
            f'<div class="answer-box">{st.session_state.deep_ans}</div>',
            unsafe_allow_html=True
        )

    if q_deep.strip() and q_deep.strip() != st.session_state._last_deep:
        st.session_state._last_deep = q_deep.strip()
        st.session_state.deep_q     = q_deep.strip()

        with st.spinner("🔍 מחפש מקורות..."):
            kitzur  = search_local_kitzur(q_deep.strip())
            sources = search_sefaria(q_deep.strip(), SEFARIA_DEEP)

        show_sources(sources)
        prompt = f"שאלה: {q_deep.strip()}\n\n{build_context(kitzur, sources)}"

        st.markdown("### ✍️ תשובת ג'מי תורה:")
        ph = st.empty()
        ph.info("⏳ ג'מי תורה מעיין במקורות... (עד 30 שניות)")
        try:
            ans, used_method = call_gemini(api_key, prompt, SYSTEM_DEEP)
            ph.markdown(f'<div class="answer-box">{ans}</div>', unsafe_allow_html=True)
            st.caption(f"✅ הופעל: {used_method}")
            st.session_state.deep_ans = ans
            st.session_state.history  = (
                [{"q": q_deep.strip(), "a": ans}] + st.session_state.history
            )[:HISTORY_MAX]
            st.balloons()
        except Exception as e:
            ph.empty()
            handle_error(str(e), api_key)

# ════════════════════ TAB 2 — בירור מהיר ════════════════════════
with tab_quick:
    st.markdown(
        '<p style="color:#c5a059;font-weight:600;margin-top:8px;">'
        'חיפוש ממוקד מ-3 מקורות, תשובה קצרה ומהירה</p>',
        unsafe_allow_html=True
    )
    q_quick = st.text_input(
        "⚡ שאל שאלה מהירה:",
        value=st.session_state.quick_q,
        key="input_quick"
    )

    if st.session_state.quick_ans:
        st.markdown(
            f'<div class="answer-box-quick">{st.session_state.quick_ans}</div>',
            unsafe_allow_html=True
        )

    if q_quick.strip() and q_quick.strip() != st.session_state._last_quick:
        st.session_state._last_quick = q_quick.strip()
        st.session_state.quick_q     = q_quick.strip()

        with st.spinner("⚡ מחפש..."):
            sources_q = search_sefaria(q_quick.strip(), SEFARIA_QUICK)

        show_sources(sources_q)
        context_q = "\n".join(f"- {s['heRef']}: {s['he']}" for s in sources_q)
        prompt_q  = f"שאלה: {q_quick.strip()}\n\nמקורות:\n{context_q}\n\nענה בתמצית:"

        ph_q = st.empty()
        ph_q.info("⏳ מחפש תשובה...")
        try:
            ans_q, used_method_q = call_gemini(api_key, prompt_q, SYSTEM_QUICK)
            ph_q.markdown(
                f'<div class="answer-box-quick">{ans_q}</div>',
                unsafe_allow_html=True
            )
            st.caption(f"✅ הופעל: {used_method_q}")
            st.session_state.quick_ans = ans_q
        except Exception as e:
            ph_q.empty()
            handle_error(str(e), api_key)

# ── היסטוריה ─────────────────────────────────────────────────────
if st.session_state.history:
    st.write("---")
    st.markdown("### 📚 שאלות קודמות:")
    for item in st.session_state.history:
        with st.expander(f"🔹 {item['q'][:70]}{'...' if len(item['q'])>70 else ''}"):
            st.markdown(
                f'<div class="answer-box" style="font-size:14px">{item["a"]}</div>',
                unsafe_allow_html=True
            )