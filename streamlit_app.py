import os
import re
import time
import base64
import requests
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(
    page_title="ג'מי תורה - עוזר הלכה ובינה מלאכותית תורנית",
    page_icon="📜",
    layout="wide"
)

# ── קבועי תצורה ────────────────────────────────────────────────
MODELS           = ["gemini-2.0-flash"]
SEFARIA_DEEP     = 8
SEFARIA_QUICK    = 3
REQUEST_TIMEOUT  = 7
TEMPERATURE      = 0.65
KITZUR_MAX_CHARS = 2000
KITZUR_SECTIONS  = 4
HISTORY_MAX      = 5

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
.premium-header p  { color:#c5a059 !important; font-size:1.2rem !important; margin:0 !important; }
.rabbi-banner-img  {
    width:200px; border-radius:14px;
    border:3px solid #c5a059; box-shadow:0 6px 25px rgba(0,0,0,0.5); flex-shrink:0;
}
@media (max-width:768px) {
    .block-container { padding-left:1rem !important; padding-right:1rem !important; }
    .premium-header  {
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
.source-box  {
    background:#0d1e2e; border-right:4px solid #c5a059;
    border-radius:8px; padding:12px 16px; margin-bottom:10px;
}
.source-ref  { color:#c5a059; font-weight:700; font-size:14px; margin-bottom:4px; }
.source-text { color:#c8bfa8; font-size:13px; line-height:1.7; }
#MainMenu,footer,header                                    { visibility:hidden !important; }
[data-testid="manage-app-button"],
[data-testid="stToolbarActions"],
[data-testid="stToolbar"],
.stDeployButton                                            { display:none !important; }
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
    h(); setTimeout(h,1000); setTimeout(h,3000);
})();
</script>
"""

# ── עזרים ──────────────────────────────────────────────────────
def get_base64_image(path: str):
    if os.path.exists(path):
        with open(path,"rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def strip_html(text: str) -> str:
    return re.sub(r'<[^>]+>',' ',text).strip()

def clean_query(query: str) -> str:
    return re.sub(
        r'\b(מה|האם|כיצד|למה|מדוע|איך|מתי|היכן|מי|הסבר|פרט|ספר)\b',
        '', query
    ).strip()

def search_local_kitzur(query: str) -> str:
    try:
        if not os.path.exists("kitzur_shulchan_aruch.txt"):
            return ""
        with open("kitzur_shulchan_aruch.txt","r",encoding="utf-8",errors="ignore") as f:
            lines = f.read().split("\n")
        keywords = [w for w in query.split() if len(w) > 2]
        if not keywords:
            return ""
        scored = []
        for i, line in enumerate(lines):
            score = sum(1 for kw in keywords if kw in line)
            if score > 0:
                section = "\n".join(lines[max(0,i-1):min(len(lines),i+6)]).strip()
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
                "https://www.sefaria.org/api/search-wrapper",
                params={"query":q,"type":"text","size":size,"field":"naive_lemmatizer"},
                timeout=REQUEST_TIMEOUT
            )
            for hit in r.json().get("hits",{}).get("hits",[]):
                src = hit.get("_source",{})
                ref = src.get("ref","")
                he  = strip_html(src.get("he",""))
                if ref and he and len(he) > 15 and ref not in seen:
                    seen.add(ref)
                    results.append({
                        "heRef": src.get("heRef", ref),
                        "he":    he[:500] + ("..." if len(he) > 500 else "")
                    })
        except Exception:
            pass
    _fetch(query)
    kw = clean_query(query)
    if kw and kw != query:
        _fetch(kw)
    return results[:size]

def stream_answer(client, prompt: str, system: str, placeholder, box_class="answer-box") -> str:
    """Gemini streaming עם exponential backoff."""
    config = types.GenerateContentConfig(
        system_instruction=system,
        temperature=TEMPERATURE,
        safety_settings=[
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH",       threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT",        threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
        ]
    )
    last_err = ""
    for model_name in MODELS:
        for attempt in range(4):
            try:
                text = ""
                for chunk in client.models.generate_content_stream(
                    model=model_name, contents=prompt, config=config
                ):
                    if chunk.text:
                        text += chunk.text
                        placeholder.markdown(
                            f'<div class="{box_class}">{text}▌</div>',
                            unsafe_allow_html=True
                        )
                placeholder.markdown(
                    f'<div class="{box_class}">{text}</div>',
                    unsafe_allow_html=True
                )
                return text
            except Exception as e:
                last_err = str(e)
                is_rate = any(x in last_err for x in ["429","RESOURCE_EXHAUSTED","quota","503","UNAVAILABLE"])
                if is_rate and attempt < 3:
                    time.sleep(2 ** attempt * 3)   # 3 → 6 → 12 שניות
                else:
                    break
    raise Exception(last_err)

# ── ממשק ─────────────────────────────────────────────────────────
st.markdown(CSS, unsafe_allow_html=True)

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

# ── session state ─────────────────────────────────────────────────
if "history"      not in st.session_state: st.session_state.history      = []
if "deep_q"       not in st.session_state: st.session_state.deep_q       = ""
if "quick_q"      not in st.session_state: st.session_state.quick_q      = ""

# ── בדיקת מפתח ──────────────────────────────────────────────────
if "GEMINI_API_KEY" not in st.secrets:
    st.error("⚠️ מפתח ה-API לא הוגדר ב-Secrets של המערכת.")
    st.stop()

# ✅ ללא http_options — v1beta הוא ברירת המחדל ותומך ב-system_instruction
client = genai.Client(api_key=str(st.secrets["GEMINI_API_KEY"]).strip())

# ── שאלות לדוגמה (גלובליות, מעל הלשוניות) ───────────────────────
st.markdown('<p style="color:#c5a059;font-weight:600;">💡 שאלות לדוגמה:</p>', unsafe_allow_html=True)
EXAMPLES = [
    "מה הלכות שבת לגבי חשמל?",
    "מקור מצוות כיבוד אב ואם",
    "דיני אבילות שבעה",
    "הלכות כשרות בסיסיות",
]
for i, (col, q) in enumerate(zip(st.columns(4), EXAMPLES)):
    if col.button(q, key=f"ex_{i}", use_container_width=True):
        st.session_state.deep_q  = q
        st.session_state.quick_q = q
        st.rerun()

# ── לשוניות ─────────────────────────────────────────────────────
tab_deep, tab_quick = st.tabs([
    "🏛️  עיון מעמיק — תשובה מפורטת",
    "⚡  בירור מהיר — תשובה תמציתית",
])

# ════════════════════════════════════════════════════════════════
# TAB 1 — עיון מעמיק
# ════════════════════════════════════════════════════════════════
with tab_deep:
    st.markdown(
        '<p style="color:#c5a059;font-weight:600;margin-top:8px;">'
        'חיפוש נרחב מ-8 מקורות, תשובה מפורטת עם כל הדעות והמחלוקות</p>',
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

    if q_deep and q_deep.strip():
        with st.spinner("🔍 מחפש מקורות..."):
            kitzur  = search_local_kitzur(q_deep.strip())
            sources = search_sefaria(q_deep.strip(), SEFARIA_DEEP)

        if sources:
            html = "".join(
                f'<div class="source-box">'
                f'<div class="source-ref">📖 {s["heRef"]}</div>'
                f'<div class="source-text">{s["he"]}</div>'
                f'</div>'
                for s in sources
            )
            with st.expander(f"📚 {len(sources)} מקורות ממאגר ספריא", expanded=False):
                st.markdown(html, unsafe_allow_html=True)

        context_parts = []
        if kitzur:
            context_parts.append(f"מתוך קיצור שולחן ערוך:\n{kitzur}")
        if sources:
            src_lines = "\n\n".join(f"[{i+1}] {s['heRef']}: {s['he']}" for i,s in enumerate(sources))
            context_parts.append(f"מקורות ממאגר ספריא:\n{src_lines}")
        if context_parts:
            context_parts.append("התבסס על מקורות אלו וציין אותם.")

        prompt = f"שאלה: {q_deep.strip()}\n\n" + "\n\n".join(context_parts)

        st.markdown("### ✍️ תשובת ג'מי תורה:")
        placeholder = st.empty()
        try:
            answer = stream_answer(client, prompt, SYSTEM_DEEP, placeholder, "answer-box")
            st.balloons()
            st.session_state.history = (
                [{"q": q_deep.strip(), "a": answer}] + st.session_state.history
            )[:HISTORY_MAX]
            st.session_state.deep_q = ""
        except Exception as e:
            err = str(e)
            if any(x in err for x in ["401","UNAUTHENTICATED"]):
                st.error("⚠️ מפתח API שגוי — עדכן ב-Secrets.")
            elif any(x in err for x in ["429","RESOURCE_EXHAUSTED","quota"]):
                st.error(
                    "⚠️ מכסה יומית אזלה.\n\n"
                    "**פתרון:** פתח Gmail חדש → aistudio.google.com → צור מפתח → עדכן Secrets."
                )
            else:
                st.error(f"❌ שגיאה: {err}")

# ════════════════════════════════════════════════════════════════
# TAB 2 — בירור מהיר
# ════════════════════════════════════════════════════════════════
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

    if q_quick and q_quick.strip():
        with st.spinner("⚡ מחפש..."):
            sources_q = search_sefaria(q_quick.strip(), SEFARIA_QUICK)

        if sources_q:
            html = "".join(
                f'<div class="source-box">'
                f'<div class="source-ref">📖 {s["heRef"]}</div>'
                f'<div class="source-text">{s["he"]}</div>'
                f'</div>'
                for s in sources_q
            )
            with st.expander(f"📚 {len(sources_q)} מקורות", expanded=False):
                st.markdown(html, unsafe_allow_html=True)

        context_q = "\n".join(f"- {s['heRef']}: {s['he']}" for s in sources_q)
        prompt_q  = f"שאלה: {q_quick.strip()}\n\nמקורות:\n{context_q}\n\nענה בתמצית:"

        placeholder_q = st.empty()
        try:
            stream_answer(client, prompt_q, SYSTEM_QUICK, placeholder_q, "answer-box-quick")
            st.session_state.quick_q = ""
        except Exception as e:
            st.error(f"❌ שגיאה: {str(e)}")

# ── היסטוריה ─────────────────────────────────────────────────────
if st.session_state.history:
    st.write("---")
    st.markdown("### 📚 שאלות קודמות:")
    for item in st.session_state.history:
        with st.expander(f"🔹 {item['q'][:70]}{'...' if len(item['q']) > 70 else ''}"):
            st.markdown(
                f'<div class="answer-box" style="font-size:14px">{item["a"]}</div>',
                unsafe_allow_html=True
            )