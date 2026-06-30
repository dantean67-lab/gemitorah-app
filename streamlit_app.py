import os
import re
import base64
import requests
import streamlit as st

st.set_page_config(
    page_title="ג'מי תורה - עוזר הלכה ומקורות תורניים",
    page_icon="📜",
    layout="wide"
)

VERSION_TAG      = "v2026-06-30-SEFARIA-ONLY"
SEFARIA_DEEP     = 10
SEFARIA_QUICK    = 4
KITZUR_MAX_CHARS = 2000
KITZUR_SECTIONS  = 5
HISTORY_MAX      = 5
SEFARIA_URL      = "https://www.sefaria.org/api/search-wrapper"

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
.source-card {
    background:#0f1923; border:1px solid #223446; border-radius:14px;
    border-right:5px solid #c5a059; padding:22px 28px; margin-bottom:16px;
    color:#f0e6d3; direction:rtl; text-align:right;
}
.source-card-title {
    color:#c5a059; font-weight:700; font-size:17px; margin-bottom:10px;
}
.source-card-text {
    color:#e0d5c0; font-size:15px; line-height:2;
}
.kitzur-card {
    background:#0d1e2e; border:1px solid #2a4060; border-radius:14px;
    border-right:5px solid #4a90d9; padding:22px 28px; margin-bottom:16px;
    color:#f0e6d3; direction:rtl; text-align:right;
}
.kitzur-card-title {
    color:#4a90d9; font-weight:700; font-size:17px; margin-bottom:10px;
}
.kitzur-card-text {
    color:#c8d8e8; font-size:15px; line-height:2;
}
.no-results {
    background:#1a1410; border:2px solid #c5a059; border-radius:12px;
    padding:24px; text-align:center; color:#c5a059; font-size:16px;
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

HALACHIC_PATHS = ("Halakhah/Shulchan Arukh", "Halakhah/Mishneh Torah",
                  "Halakhah/Arukh HaShulchan", "Halakhah/Mishnah Berurah",
                  "Halakhah/Rishonim", "Halakhah/")

def _halachic_rank(path: str) -> int:
    for i, prefix in enumerate(HALACHIC_PATHS):
        if path.startswith(prefix):
            return i
    return len(HALACHIC_PATHS)

def search_sefaria(query: str, size: int) -> list:
    seen, results = set(), []
    def _fetch(q):
        try:
            r = requests.post(
                SEFARIA_URL,
                headers={"Content-Type": "application/json"},
                json={"query": q, "type": "text", "size": size,
                      "field": "naive_lemmatizer", "slop": 10,
                      "source_proj": ["heRef", "ref", "path"]},
                timeout=7
            )
            for hit in r.json().get("hits", {}).get("hits", []):
                src      = hit.get("_source", {})
                ref      = src.get("ref") or re.sub(r'\s*\([^)]*\)\s*$', '', hit.get("_id", "")).strip()
                he_ref   = src.get("heRef") or ref
                path     = src.get("path", "")
                snippets = hit.get("highlight", {}).get("naive_lemmatizer", [])
                he       = strip_html(" ... ".join(snippets))
                if ref and he and len(he) > 15 and ref not in seen:
                    seen.add(ref)
                    results.append({
                        "heRef": he_ref,
                        "he":    he[:600] + ("..." if len(he) > 600 else ""),
                        "_rank": _halachic_rank(path),
                    })
        except Exception:
            pass
    _fetch(query)
    kw = clean_query(query)
    if kw and kw != query:
        _fetch(kw)
    results.sort(key=lambda x: x["_rank"])
    return [{k: v for k, v in r.items() if k != "_rank"} for r in results[:size]]

def search_local_kitzur(query: str) -> list:
    try:
        if not os.path.exists("kitzur_shulchan_aruch.txt"):
            return []
        with open("kitzur_shulchan_aruch.txt", "r", encoding="utf-8", errors="ignore") as f:
            lines = f.read().split("\n")
        keywords = [w for w in query.split() if len(w) > 2]
        if not keywords:
            return []
        scored = []
        for i, line in enumerate(lines):
            score = sum(1 for kw in keywords if kw in line)
            if score > 0:
                section = "\n".join(lines[max(0, i-1):min(len(lines), i+6)]).strip()
                if len(section) > 20:
                    scored.append((score, section))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in scored[:KITZUR_SECTIONS]]
    except Exception:
        return []

def render_results(query, size):
    with st.spinner("🔍 מחפש במקורות..."):
        sources = search_sefaria(query, size)
        kitzur  = search_local_kitzur(query)

    if not sources and not kitzur:
        st.markdown(
            '<div class="no-results">לא נמצאו מקורות לשאלה זו. נסה ניסוח אחר.</div>',
            unsafe_allow_html=True
        )
        return

    if kitzur:
        st.markdown("### 📘 קיצור שולחן ערוך")
        for section in kitzur:
            st.markdown(
                f'<div class="kitzur-card">'
                f'<div class="kitzur-card-title">📘 קיצור שולחן ערוך</div>'
                f'<div class="kitzur-card-text">{section}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    if sources:
        st.markdown(f"### 📚 מקורות שנמצאו ({len(sources)})")
        for s in sources:
            st.markdown(
                f'<div class="source-card">'
                f'<div class="source-card-title">📖 {s["heRef"]}</div>'
                f'<div class="source-card-text">{s["he"]}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

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
    <p>חיפוש מקורות הלכה מספריא וקיצור שולחן ערוך</p>
  </div>
  {img_tag}
</div>""", unsafe_allow_html=True)

for k in ["history", "deep_q", "quick_q", "_last_deep", "_last_quick"]:
    if k not in st.session_state:
        st.session_state[k] = [] if k == "history" else ""

st.markdown('<p style="color:#c5a059;font-weight:600;">💡 שאלות לדוגמה:</p>', unsafe_allow_html=True)
EXAMPLES = [
    "חשמל בשבת",
    "כיבוד הורים",
    "אבילות",
    "כשרות",
]
for i, (col, q) in enumerate(zip(st.columns(4), EXAMPLES)):
    if col.button(q, key=f"ex_{i}", use_container_width=True):
        st.session_state.update({
            "deep_q": q, "quick_q": q,
            "_last_deep": "", "_last_quick": "",
        })
        st.rerun()

tab_deep, tab_quick = st.tabs([
    "🏛️   עיון מעמיק — 10 מקורות",
    "⚡   בירור מהיר — 4 מקורות",
])

with tab_deep:
    st.markdown(
        '<p style="color:#c5a059;font-weight:600;margin-top:8px;">'
        'חיפוש נרחב — 10 מקורות מספריא + קיצור שולחן ערוך</p>',
        unsafe_allow_html=True
    )
    col_input, col_btn = st.columns([5, 1])
    with col_input:
        q_deep = st.text_input(
            "🔍 חפש נושא או מושג (לדוגמה: שבת, כשרות, תפילין) — לא שאלות מלאות:",
            value=st.session_state.deep_q,
            key="input_deep"
        )
    with col_btn:
        st.markdown("<div style='padding-top:28px'>", unsafe_allow_html=True)
        if st.button("🆕 חדש", key="clear_deep", use_container_width=True,
                     disabled=not st.session_state.deep_q):
            st.session_state.update({"deep_q": "", "_last_deep": ""})
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<div style="color:#7a7a7a;font-size:12px;font-style:italic;">'
        '⚠️ לעניין הלכה למעשה — יש להיוועץ ברב מורה הוראה.</div>',
        unsafe_allow_html=True
    )

    if q_deep.strip() and q_deep.strip() != st.session_state._last_deep:
        st.session_state._last_deep = q_deep.strip()
        st.session_state.deep_q     = q_deep.strip()
        st.session_state.history    = (
            [q_deep.strip()] + st.session_state.history
        )[:HISTORY_MAX]
        render_results(q_deep.strip(), SEFARIA_DEEP)

with tab_quick:
    st.markdown(
        '<p style="color:#c5a059;font-weight:600;margin-top:8px;">'
        'חיפוש ממוקד — 4 מקורות מספריא</p>',
        unsafe_allow_html=True
    )
    col_input_q, col_btn_q = st.columns([5, 1])
    with col_input_q:
        q_quick = st.text_input(
            "🔍 חפש נושא או מושג (לדוגמה: שבת, כשרות, תפילין) — לא שאלות מלאות:",
            value=st.session_state.quick_q,
            key="input_quick"
        )
    with col_btn_q:
        st.markdown("<div style='padding-top:28px'>", unsafe_allow_html=True)
        if st.button("🆕 חדש", key="clear_quick", use_container_width=True,
                     disabled=not st.session_state.quick_q):
            st.session_state.update({"quick_q": "", "_last_quick": ""})
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    if q_quick.strip() and q_quick.strip() != st.session_state._last_quick:
        st.session_state._last_quick = q_quick.strip()
        st.session_state.quick_q     = q_quick.strip()
        render_results(q_quick.strip(), SEFARIA_QUICK)

if st.session_state.history:
    st.write("---")
    st.markdown("### 📚 שאלות קודמות:")
    for q in st.session_state.history:
        st.markdown(f"🔹 {q}")
