from __future__ import annotations

import os
import re
import html
import base64
import requests
import streamlit as st

st.set_page_config(
    page_title="ג'מי תורה - עוזר הלכה ומקורות תורניים",
    page_icon="📜",
    layout="wide"
)

SEFARIA_DEEP     = 20
SEFARIA_QUICK    = 8
SEARCH_EXPANSION_THRESHOLD = 8
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
    color:#c8d8e8; font-size:15px; line-height:2; white-space:pre-wrap;
}
.ai-answer-card {
    background:linear-gradient(135deg,#071a0d,#0d2614);
    border:1px solid #2a5c35; border-right:5px solid #4caf72;
    border-radius:14px; padding:24px 28px; margin-bottom:20px;
    color:#e0f0e5; direction:rtl; text-align:right;
}
.ai-answer-title {
    color:#4caf72; font-weight:700; font-size:17px; margin-bottom:12px;
}
.ai-answer-text {
    color:#d0ead8; font-size:15px; line-height:2; white-space:pre-wrap;
}
.no-results {
    background:#1a1410; border:2px solid #c5a059; border-radius:12px;
    padding:24px; text-align:center; color:#c5a059; font-size:16px;
}
.sefaria-error {
    background:#1a0f0f; border:2px solid #8b2020; border-radius:12px;
    padding:16px 20px; color:#e07070; font-size:14px; direction:ltr;
}
.disclaimer-box {
    background:#2a1f08; border:2px solid #e0a030; border-radius:12px;
    padding:16px 22px; margin-bottom:24px; color:#ffcc66;
    font-size:14px; font-weight:600; text-align:center; line-height:1.6;
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

@st.cache_data(show_spinner=False)
def get_base64_image(path):
    abs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
    if os.path.exists(abs_path):
        with open(abs_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def strip_html(text):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', text)).strip()

def strip_markdown(text: str) -> str:
    """The AI answer is rendered in a plain styled <div>, not st.markdown, so
    strip any markdown syntax the model added rather than showing raw asterisks/hashes."""
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'\1', text)
    text = re.sub(r'^\s*[-*•]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+[.)]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\[(\d+)\]', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

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

def _format_sources_for_groq(sources: list, kitzur: list) -> str:
    parts = []
    if kitzur:
        parts.append("מקור ראשי - קיצור שולחן ערוך:")
        for section in kitzur[:3]:
            parts.append(section[:400])
    for i, s in enumerate(sources, 1):
        parts.append(f"[{i}] {s['heRef']}:\n{s['he']}")
    return "\n\n".join(parts)

def _groq_client():
    api_key = st.secrets.get("GROQ_API_KEY", "")
    if not api_key:
        return None
    try:
        from groq import Groq
        return Groq(api_key=api_key)
    except Exception:
        return None

def _groq_chat(client, system: str, user: str, max_tokens: int = 1024) -> str | None:
    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.3,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return None

MIN_ANSWER_WORDS = 150

def _expand_if_short(client, system: str, user: str, answer: str | None) -> str | None:
    """If the answer is under MIN_ANSWER_WORDS, ask Groq to expand the same answer
    with more detail rather than re-deriving a new, shorter one."""
    if not answer or len(answer.split()) >= MIN_ANSWER_WORDS:
        return answer
    expanded = _groq_chat(
        client,
        system,
        f"{user}\n\nהתשובה הקודמת שכתבת:\n{answer}\n\n"
        f"התשובה קצרה מדי. הרחב עם יותר פרטים, מקורות ודוגמאות מעשיות.",
        max_tokens=2000,
    )
    return expanded or answer

_GROQ_SYSTEM_PROMPT = """אתה עוזר תורני מומחה ברמת פוסק הלכה.
תפקידך לענות על שאלות תורניות בצורה מדויקת, מקיפה ומבוססת מקורות.

כללי תשובה מחייבים:
א. פתח תמיד בציון המקור העיקרי (שם ספר + פרק/סעיף).
ב. הבחן בין דעת רוב הפוסקים לדעת מיעוט.
ג. ציין במפורש: אשכנזים vs ספרדים כשיש הבדל.
ד. ציין שמות פוסקים מרכזיים (משנה ברורה, בן איש חי, שולחן ערוך הרב, ערוך השולחן).
ה. סיים תמיד ב"למעשה:" עם הנחיה ברורה ופשוטה.
ו. אם יש מחלוקת גדולה — כתוב "יש להתייעץ עם רב".
ז. כתוב בעברית בלבד. פסקאות קצרות וברורות.
ח. השתמש בכל המקורות שניתנו לך."""

QUICK_INSTRUCTION = "ענה בדיוק ב-5-6 משפטים, כולל דוגמה מעשית אחת. אל תרחיב מעבר לכך."

def ask_groq(query: str, sources: list, kitzur: list, quick: bool = False) -> str | None:
    if not sources and not kitzur:
        return None
    client = _groq_client()
    if not client:
        return None
    blob = _format_sources_for_groq(sources, kitzur)
    user = (
        f"נושא: {query}\n\n"
        f"השתמש רק במקורות הרלוונטיים ישירות לנושא \"{query}\" — "
        f"התעלם לחלוטין ממקורות העוסקים בנושאים אחרים.\n\n"
        + (f"{QUICK_INSTRUCTION}\n\n" if quick else "")
        + f"מקורות:\n{blob}"
    )
    if quick:
        return _groq_chat(client, _GROQ_SYSTEM_PROMPT, user, max_tokens=500)
    answer = _groq_chat(client, _GROQ_SYSTEM_PROMPT, user, max_tokens=2000)
    return _expand_if_short(client, _GROQ_SYSTEM_PROMPT, user, answer)

def ask_groq_general(query: str, quick: bool = False) -> str | None:
    """Fallback: no Sefaria/kitzur results — answer from general Torah knowledge."""
    client = _groq_client()
    if not client:
        return None
    system = (
        "אתה רב מלומד המסביר תורה בעברית שוטפת וברורה, בסגנון חם, בהיר וחינוכי — "
        "כמו רב הנותן שיעור תורה מלא ומקיף, לא סיכום קצר. "
        "לא נמצאו מקורות ספציפיים בספריא עבור השאלה — ענה מתוך ידיעותיך הכלליות בתורה, "
        "בפסקאות רציפות וזורמות, כאילו אתה מסביר לשואל פנים אל פנים. "
        "אל תמספר ואל תעשה רשימה. "
        "תן תשובה מעמיקה ומפורטת הכוללת: את פסק ההלכה המרכזי; מחלוקות מוכרות בין הפוסקים אם ידועות לך "
        "(למשל בין מנהג אשכנז למנהג ספרד); דוגמאות מעשיות כשרלוונטי; ושמות ספרים מוכרים (כגון שולחן ערוך, "
        "משנה ברורה, בן איש חי) רק אם אתה בטוח בהם, בלי ציטוטים או מראי מקום מדויקים (סימן/סעיף) שאינך בטוח בהם. "
        "סיים בפסקת סיכום מעשי וברור. כתוב לפחות 150 מילה. "
        "הקפד לסיים את התשובה במלואה — לעולם אל תפסיק באמצע משפט. "
        "בסוף כתוב: 'לעניין הלכה למעשה יש להיוועץ ברב מורה הוראה.'"
    )
    user = f"נושא: {query}\n\n{QUICK_INSTRUCTION}" if quick else f"נושא: {query}"
    if quick:
        return _groq_chat(client, system, user, max_tokens=500)
    answer = _groq_chat(client, system, user, max_tokens=2000)
    return _expand_if_short(client, system, user, answer)

@st.cache_data(show_spinner=False, ttl=300)
def search_sefaria(query: str, size: int) -> tuple:
    """Returns (results_list, error_str_or_None)."""
    seen, results = set(), []
    last_error = None

    def _fetch(q):
        nonlocal last_error
        try:
            r = requests.post(
                SEFARIA_URL,
                headers={"Content-Type": "application/json"},
                json={"query": q, "type": "text", "size": size * 3,
                      "field": "naive_lemmatizer", "slop": 10,
                      "source_proj": ["heRef", "ref", "path"]},
                timeout=7,
            )
            r.raise_for_status()
            for hit in (r.json().get("hits", {}).get("hits") or []):
                src      = hit.get("_source", {})
                ref      = src.get("ref") or re.sub(r'\s*\([^)]*\)\s*$', '', hit.get("_id", "")).strip()
                he_ref   = strip_html(src.get("heRef") or ref)
                path     = src.get("path", "")
                snippets = hit.get("highlight", {}).get("naive_lemmatizer", [])
                he       = strip_html(" ... ".join(snippets))
                if ref and he and len(he) > 80 and ref not in seen:
                    seen.add(ref)
                    results.append({
                        "heRef": he_ref,
                        "he":    he[:600] + ("..." if len(he) > 600 else ""),
                        "_rank": _halachic_rank(path),
                    })
        except requests.exceptions.Timeout:
            last_error = "ספריא לא הגיבה בזמן (timeout). נסה שוב."
        except requests.exceptions.HTTPError as e:
            status = getattr(e.response, "status_code", "?")
            last_error = f"ספריא החזירה שגיאה: {status}"
        except Exception as e:
            last_error = f"שגיאת חיבור לספריא: {str(e)[:80]}"

    kw = clean_query(query)
    primary = kw if kw else query
    _fetch(primary)
    if primary != query:
        _fetch(query)

    if len(results) < SEARCH_EXPANSION_THRESHOLD:
        tried = {primary, query}
        keywords = [w for w in primary.split() if len(w) > 1 and w not in tried]
        for w in keywords[:3]:
            if len(results) >= SEARCH_EXPANSION_THRESHOLD:
                break
            tried.add(w)
            _fetch(w)

    results.sort(key=lambda x: x["_rank"])
    # Suppress the error if we recovered a full result set from a later fetch
    final_error = last_error if len(results) < size else None
    return (
        [{k: v for k, v in r.items() if k != "_rank"} for r in results[:size]],
        final_error,
    )

@st.cache_data(show_spinner=False)
def _load_kitzur_lines():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kitzur_shulchan_aruch.txt")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read().split("\n")

@st.cache_data(show_spinner=False)
def search_local_kitzur(query: str) -> list:
    try:
        lines = _load_kitzur_lines()
        if not lines:
            return []
        keywords = [w for w in query.split() if len(w) > 2]
        if not keywords:
            return []
        # Collect all matches first, then sort by score so high-scored sections
        # win over overlapping low-scored ones regardless of document position.
        matches = []
        for i, line in enumerate(lines):
            score = sum(1 for kw in keywords if kw in line)
            if score > 0:
                window = range(max(0, i - 1), min(len(lines), i + 6))
                section = "\n".join(lines[w] for w in window).strip()
                if len(section) > 20:
                    matches.append((score, i, window, section[:KITZUR_MAX_CHARS]))
        matches.sort(key=lambda x: x[0], reverse=True)
        covered, results = set(), []
        for score, i, window, section in matches:
            if any(j in covered for j in window):
                continue
            results.append(section)
            covered.update(window)
            if len(results) >= KITZUR_SECTIONS:
                break
        return results
    except Exception:
        return []

def render_results(sources: list, kitzur: list, error: str | None = None,
                   ai_answer: str | None = None, ai_general: bool = False):
    if error and not sources and not kitzur and not ai_answer:
        st.markdown(
            f'<div class="sefaria-error">⚠️ {html.escape(error)}</div>',
            unsafe_allow_html=True,
        )
        return

    if not sources and not kitzur and not ai_answer:
        st.markdown(
            '<div class="no-results">לא נמצאו מקורות. נסה ניסוח אחר.</div>',
            unsafe_allow_html=True,
        )
        return

    if ai_answer:
        title = (
            "🤖 תשובה מידע כללי — ללא מקורות (Groq AI)"
            if ai_general else
            "🤖 תשובה מבוססת מקורות (Groq AI)"
        )
        st.markdown(
            f'<div class="ai-answer-card">'
            f'<div class="ai-answer-title">{title}</div>'
            f'<div class="ai-answer-text">{html.escape(strip_markdown(ai_answer))}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    if error:
        st.markdown(
            f'<div class="sefaria-error" style="margin-bottom:12px">⚠️ {html.escape(error)} — מציג תוצאות חלקיות.</div>',
            unsafe_allow_html=True,
        )

    if kitzur:
        st.markdown("### 📘 קיצור שולחן ערוך")
        for section in kitzur:
            # html.escape prevents any HTML/script in the text file from executing
            st.markdown(
                f'<div class="kitzur-card">'
                f'<div class="kitzur-card-title">📘 קיצור שולחן ערוך</div>'
                f'<div class="kitzur-card-text">{html.escape(section)}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    if sources:
        st.markdown(f"### 📚 מקורות שנמצאו ({len(sources)})")
        for s in sources:
            # heRef is already strip_html'd; he is strip_html'd in search_sefaria
            st.markdown(
                f'<div class="source-card">'
                f'<div class="source-card-title">📖 {html.escape(s["heRef"])}</div>'
                f'<div class="source-card-text">{html.escape(s["he"])}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

# ── ממשק ─────────────────────────────────────────────────────────
st.markdown(CSS, unsafe_allow_html=True)

_rabbi_jpeg = get_base64_image("rabbi.jpeg")
_rabbi_png  = get_base64_image("rabbi.png")
if _rabbi_jpeg:
    rabbi_base64, rabbi_mime = _rabbi_jpeg, "image/jpeg"
elif _rabbi_png:
    rabbi_base64, rabbi_mime = _rabbi_png, "image/png"
else:
    rabbi_base64, rabbi_mime = None, ""
img_tag = (
    f'<img src="data:{rabbi_mime};base64,{rabbi_base64}" class="rabbi-banner-img" />'
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

st.markdown(
    '<div class="disclaimer-box">⚠️ ג\'מי תורה הוא כלי עזר ללימוד בלבד ועלול לטעות. '
    'לכל שאלה הלכתית חובה להתייעץ עם רב מוסמך.</div>',
    unsafe_allow_html=True,
)

_defaults = {
    "history": [], "deep_q": "", "quick_q": "",
    "_last_deep": "", "_last_quick": "",
    "deep_input_v": 0, "quick_input_v": 0,
    "deep_sources": [], "deep_kitzur": [], "deep_error": None,
    "deep_ai_answer": None, "deep_ai_general": False,
    "quick_sources": [], "quick_kitzur": [], "quick_error": None,
    "quick_ai_answer": None, "quick_ai_general": False,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.markdown('<p style="color:#c5a059;font-weight:600;">💡 דוגמאות לחיפוש:</p>', unsafe_allow_html=True)
EXAMPLES = ["חשמל בשבת", "כיבוד הורים", "אבילות", "כשרות"]
for i, (col, q) in enumerate(zip(st.columns(4), EXAMPLES)):
    if col.button(q, key=f"ex_{i}", use_container_width=True):
        st.session_state.update({
            "deep_q": q, "quick_q": q,
            "_last_deep": "", "_last_quick": "",
            "deep_sources": [], "deep_kitzur": [], "deep_error": None,
            "deep_ai_answer": None, "deep_ai_general": False,
            "quick_sources": [], "quick_kitzur": [], "quick_error": None,
            "quick_ai_answer": None, "quick_ai_general": False,
        })
        # bump the widget key version to force the text_input to remount with the new value
        st.session_state.deep_input_v  += 1
        st.session_state.quick_input_v += 1
        st.rerun()

tab_deep, tab_quick = st.tabs([
    f"🏛️   עיון מעמיק — {SEFARIA_DEEP} מקורות",
    f"⚡   בירור מהיר — {SEFARIA_QUICK} מקורות",
])

with tab_deep:
    st.markdown(
        '<p style="color:#c5a059;font-weight:600;margin-top:8px;">'
        f'חיפוש נרחב — {SEFARIA_DEEP} מקורות מספריא + קיצור שולחן ערוך</p>',
        unsafe_allow_html=True,
    )
    col_input, col_btn = st.columns([5, 1])
    _deep_key = f"input_deep_{st.session_state.deep_input_v}"
    with col_input:
        q_deep = st.text_input(
            "🔍 חפש נושא או מושג (לדוגמה: שבת, כשרות, תפילין) — לא שאלות מלאות:",
            value=st.session_state.deep_q,
            key=_deep_key,
        )
    with col_btn:
        st.markdown("<div style='padding-top:28px'>", unsafe_allow_html=True)
        _has_deep = bool(st.session_state.get(_deep_key, "") or st.session_state.deep_q)
        _has_hist = bool(st.session_state.history)
        if st.button("🆕 חדש", key="clear_deep", use_container_width=True,
                     disabled=not (_has_deep or _has_hist)):
            if _has_deep:
                st.session_state.update({
                    "deep_q": "", "_last_deep": "",
                    "deep_sources": [], "deep_kitzur": [], "deep_error": None,
                    "deep_ai_answer": None, "deep_ai_general": False,
                })
                # bump the widget key version to force the text_input to remount empty
                st.session_state.deep_input_v += 1
            else:
                st.session_state.history = []
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    if q_deep.strip() and q_deep.strip() != st.session_state._last_deep:
        st.session_state._last_deep = q_deep.strip()
        st.session_state.deep_q     = q_deep.strip()
        hist = st.session_state.history
        if not hist or hist[0] != q_deep.strip():
            hist = [q_deep.strip()] + hist
        st.session_state.history = hist[:HISTORY_MAX]
        with st.spinner("🔍 מחפש במקורות..."):
            sources, err = search_sefaria(q_deep.strip(), SEFARIA_DEEP)
            kitzur       = search_local_kitzur(q_deep.strip())
        ai_general = not sources and not kitzur and not err
        with st.spinner("🤖 מנתח מקורות עם Groq AI..."):
            if ai_general:
                ai_answer = ask_groq_general(q_deep.strip())
            else:
                ai_answer = ask_groq(q_deep.strip(), sources, kitzur)
        st.session_state.deep_sources    = sources
        st.session_state.deep_kitzur     = kitzur
        st.session_state.deep_error      = err
        st.session_state.deep_ai_answer  = ai_answer
        st.session_state.deep_ai_general = ai_general

    # render cached results — survives tab switches
    if (st.session_state.deep_sources or st.session_state.deep_kitzur
            or st.session_state.deep_error or st.session_state.deep_ai_answer):
        render_results(
            st.session_state.deep_sources,
            st.session_state.deep_kitzur,
            st.session_state.deep_error,
            st.session_state.deep_ai_answer,
            st.session_state.deep_ai_general,
        )
    elif st.session_state._last_deep:
        render_results([], [], None)

with tab_quick:
    st.markdown(
        '<p style="color:#c5a059;font-weight:600;margin-top:8px;">'
        f'חיפוש ממוקד — {SEFARIA_QUICK} מקורות מספריא</p>',
        unsafe_allow_html=True,
    )
    col_input_q, col_btn_q = st.columns([5, 1])
    _quick_key = f"input_quick_{st.session_state.quick_input_v}"
    with col_input_q:
        q_quick = st.text_input(
            "🔍 חפש נושא או מושג (לדוגמה: שבת, כשרות, תפילין) — לא שאלות מלאות:",
            value=st.session_state.quick_q,
            key=_quick_key,
        )
    with col_btn_q:
        st.markdown("<div style='padding-top:28px'>", unsafe_allow_html=True)
        _has_quick  = bool(st.session_state.get(_quick_key, "") or st.session_state.quick_q)
        _has_hist_q = bool(st.session_state.history)
        if st.button("🆕 חדש", key="clear_quick", use_container_width=True,
                     disabled=not (_has_quick or _has_hist_q)):
            if _has_quick:
                st.session_state.update({
                    "quick_q": "", "_last_quick": "",
                    "quick_sources": [], "quick_kitzur": [], "quick_error": None,
                    "quick_ai_answer": None, "quick_ai_general": False,
                })
                # bump the widget key version to force the text_input to remount empty
                st.session_state.quick_input_v += 1
            else:
                st.session_state.history = []
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    if q_quick.strip() and q_quick.strip() != st.session_state._last_quick:
        st.session_state._last_quick = q_quick.strip()
        st.session_state.quick_q     = q_quick.strip()
        hist = st.session_state.history
        if not hist or hist[0] != q_quick.strip():
            hist = [q_quick.strip()] + hist
        st.session_state.history = hist[:HISTORY_MAX]
        with st.spinner("🔍 מחפש במקורות..."):
            sources_q, err_q = search_sefaria(q_quick.strip(), SEFARIA_QUICK)
            kitzur_q         = search_local_kitzur(q_quick.strip())
        ai_general_q = not sources_q and not kitzur_q and not err_q
        with st.spinner("🤖 מנתח מקורות עם Groq AI..."):
            if ai_general_q:
                ai_answer_q = ask_groq_general(q_quick.strip(), quick=True)
            else:
                ai_answer_q = ask_groq(q_quick.strip(), sources_q, kitzur_q, quick=True)
        st.session_state.quick_sources     = sources_q
        st.session_state.quick_kitzur      = kitzur_q
        st.session_state.quick_error       = err_q
        st.session_state.quick_ai_answer   = ai_answer_q
        st.session_state.quick_ai_general  = ai_general_q

    if (st.session_state.quick_sources or st.session_state.quick_kitzur
            or st.session_state.quick_error or st.session_state.quick_ai_answer):
        render_results(
            st.session_state.quick_sources,
            st.session_state.quick_kitzur,
            st.session_state.quick_error,
            st.session_state.quick_ai_answer,
            st.session_state.quick_ai_general,
        )
    elif st.session_state._last_quick:
        render_results([], [], None)

if st.session_state.history:
    st.write("---")
    st.markdown("### 📚 שאלות קודמות:")
    for q in st.session_state.history:
        # use st.text to avoid markdown injection from user-supplied query strings
        st.text(f"🔹 {q}")
