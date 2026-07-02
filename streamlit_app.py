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

# ── Sefaria search ──────────────────────────────────────────────────
SEFARIA_DEEP               = 100
SEFARIA_QUICK              = 30
SEFARIA_TIMEOUT_SECONDS    = 7
SEFARIA_MIN_SNIPPET_CHARS  = 100
SEARCH_EXPANSION_THRESHOLD = 8
SEFARIA_URL                = "https://www.sefaria.org/api/search-wrapper"

# ── Kitzur Shulchan Arukh (local file, shown in full in the UI) ────
KITZUR_MAX_CHARS = 2000
KITZUR_SECTIONS  = 5

# ── Groq — source trimming (the UI shows every source found, but only
# a hard-trimmed top slice is ever sent to Groq, to stay well under its
# free-tier daily token budget) ─────────────────────────────────────
GROQ_DEEP_SOURCES           = 6
GROQ_QUICK_SOURCES          = 3
GROQ_SOURCE_MAX_CHARS       = 120   # per source, deep tab
GROQ_QUICK_SOURCE_MAX_CHARS = 100   # per source, quick tab
GROQ_KITZUR_SOURCES         = 2
GROQ_KITZUR_MAX_CHARS       = 200
GROQ_BUDGET_CHARS           = 3000  # hard safety net on the assembled prompt (~4 chars/token)

# ── Groq — response length & sampling ───────────────────────────────
GROQ_DEEP_MAX_TOKENS     = 800
GROQ_QUICK_MAX_TOKENS    = 300
GROQ_GENERAL_MAX_TOKENS  = 600
GROQ_SOURCE_TEMPERATURE  = 0.2
GROQ_GENERAL_TEMPERATURE = 0.4
GROQ_TIMEOUT_SECONDS     = 30
GROQ_CACHE_TTL_SECONDS   = 3600

# ── Groq — answer completeness (deep tab retries once; quick tab never does) ─
MIN_ANSWER_WORDS_DEEP  = 80
MIN_ANSWER_WORDS_QUICK = 30

# ── Groq — rough session-scoped usage estimate (not a persisted daily
# counter — Streamlit session_state doesn't survive across sessions/days,
# so this is a "how much have I used this session" indicator, not a
# true quota tracker) ───────────────────────────────────────────────
GROQ_DAILY_TOKEN_LIMIT           = 100_000
GROQ_EST_TOKENS_PER_SOURCE_CALL  = 500
GROQ_EST_TOKENS_PER_GENERAL_CALL = 800
GROQ_TOKEN_WARNING_RATIO         = 0.8

# ── UI ───────────────────────────────────────────────────────────────
HISTORY_MAX             = 5
VISIBLE_SOURCES_DEFAULT = 5
MAX_QUERY_CHARS         = 200

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
    .stTabs [data-baseweb="tab-list"] {
        overflow-x:auto !important; flex-wrap:nowrap !important;
    }
    .stTabs [data-baseweb="tab"] {
        font-size:12px !important; padding:8px 10px !important; white-space:nowrap !important;
    }
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
def get_base64_image(path: str) -> str | None:
    """Base64-encode a local image file for inlining into an <img> tag."""
    abs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
    if os.path.exists(abs_path):
        with open(abs_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def strip_html(text: str) -> str:
    """Strip HTML tags and collapse whitespace — used on both Sefaria snippets and user input."""
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

def clean_query(query: str) -> str:
    """Strip common Hebrew question words so the Sefaria search gets a bare topic/keyword."""
    return re.sub(
        r'\b(מה|האם|כיצד|למה|מדוע|איך|מתי|היכן|מי|הסבר|פרט|ספר)\b',
        '', query
    ).strip()

def sanitize_query(raw: str) -> str:
    """Input-boundary hardening: strip any HTML/script tags and cap length before use."""
    return strip_html(raw)[:MAX_QUERY_CHARS]

HALACHIC_PATHS = ("Halakhah/Shulchan Arukh", "Halakhah/Mishneh Torah",
                  "Halakhah/Arukh HaShulchan", "Halakhah/Mishnah Berurah",
                  "Halakhah/Rishonim", "Halakhah/")

def _halachic_rank(path: str) -> int:
    """Ordinal rank used as a tie-breaker: more specific/authoritative halachic works rank lower."""
    for i, prefix in enumerate(HALACHIC_PATHS):
        if path.startswith(prefix):
            return i
    return len(HALACHIC_PATHS)

PREFERRED_PATH_PREFIXES     = ("Halakhah/", "Responsa/", "Mishnah/", "Talmud/")
DEPRIORITIZED_PATH_PREFIXES = ("Liturgy/", "Poetry/", "Philosophy/")

def _relevance_score(result: dict, query_words: list) -> int:
    """Score a Sefaria hit for topical relevance so unrelated matches (e.g. tzaraat
    texts matching a כשרות root-word search) sink instead of crowding out real hits."""
    he_ref = result["heRef"]
    he_head = result["he"][:100]
    path = result["_path"]
    score, matched_words = 0, 0
    for w in query_words:
        matched = False
        if w in he_ref:
            score += 3
            matched = True
        if w in he_head:
            score += 2
            matched = True
        if matched:
            matched_words += 1
    if path.startswith(PREFERRED_PATH_PREFIXES):
        score += 1
    if "Aggadah" in path:
        score -= 2
    elif path.startswith(DEPRIORITIZED_PATH_PREFIXES):
        score -= 1
    if len(query_words) > 1 and matched_words >= 2:
        score += 2
    return score

def trim_to_token_budget(sources: list, budget_chars: int = GROQ_BUDGET_CHARS) -> list:
    """Safety net beyond the fixed per-tab source counts: drop trailing sources
    once their combined length would exceed budget_chars (~budget_chars/4 tokens)."""
    kept, total = [], 0
    for s in sources:
        length = len(s.get("he", "")) + len(s.get("heRef", ""))
        if total + length > budget_chars:
            break
        kept.append(s)
        total += length
    return kept

def _format_sources_for_groq(sources: list, kitzur: list, quick: bool = False) -> str:
    """Build the Groq prompt's source blob from only the top few, hard-trimmed, sources."""
    n = GROQ_QUICK_SOURCES if quick else GROQ_DEEP_SOURCES
    char_limit = GROQ_QUICK_SOURCE_MAX_CHARS if quick else GROQ_SOURCE_MAX_CHARS
    picked = [
        {"heRef": s["heRef"], "he": s["he"][:char_limit]}
        for s in sources[:n]
    ]
    picked = trim_to_token_budget(picked, GROQ_BUDGET_CHARS)
    parts = []
    if kitzur:
        parts.append("מקור ראשי - קיצור שולחן ערוך:")
        for section in kitzur[:GROQ_KITZUR_SOURCES]:
            parts.append(section[:GROQ_KITZUR_MAX_CHARS])
    for i, s in enumerate(picked, 1):
        parts.append(f"[{i}] {s['heRef']}:\n{s['he']}")
    return "\n\n".join(parts)

def _is_rate_limit_error(e: Exception) -> bool:
    """True if the Groq exception represents an HTTP 429 rate-limit response."""
    if getattr(e, "status_code", None) == 429:
        return True
    if type(e).__name__ == "RateLimitError":
        return True
    msg = str(e).lower()
    return "429" in msg or "rate_limit" in msg or "rate limit" in msg

GROQ_RATE_LIMIT_FALLBACK_MSG = (
    "⏳ מכסת Groq היומית אזלה. נסה שוב בעוד כמה שעות.\n"
    "המקורות למטה זמינים לעיונך גם ללא תשובת AI."
)

def _format_rate_limit_message(e: Exception) -> str:
    """Best-effort: pull the wait duration out of Groq's 429 (header or message text)
    and phrase it in Hebrew; falls back to a generic message if it can't be parsed."""
    total_seconds = None
    resp = getattr(e, "response", None)
    if resp is not None:
        try:
            retry_after = resp.headers.get("retry-after")
            if retry_after:
                total_seconds = float(retry_after)
        except Exception:
            total_seconds = None
    if total_seconds is None:
        # Groq's message reads e.g. "Please try again in 1h2m3.4s" — anchor on the
        # mandatory seconds component rather than the exact surrounding phrase,
        # since h/m are optional and wording can vary.
        m = re.search(r'(?:([\d.]+)\s*h\s*)?(?:([\d.]+)\s*m\s*)?([\d.]+)\s*s',
                       str(e), re.IGNORECASE)
        if m:
            h, mnt, s = (float(g) if g else 0.0 for g in m.groups())
            total_seconds = h * 3600 + mnt * 60 + s
    if total_seconds is None:
        return GROQ_RATE_LIMIT_FALLBACK_MSG
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    if hours == 0 and minutes == 0:
        minutes = 1
    return (
        f"⏳ מכסת Groq אזלה. תחזור בעוד {hours} שעות ו-{minutes} דקות.\n"
        "המקורות למטה זמינים לעיונך גם ללא תשובת AI."
    )

def _groq_client():
    """Returns (client_or_None, error_or_None)."""
    api_key = st.secrets.get("GROQ_API_KEY", "")
    if not api_key:
        return None, "⚠️ שגיאת Groq: מפתח GROQ_API_KEY לא הוגדר בהגדרות."
    try:
        from groq import Groq
        return Groq(api_key=api_key, timeout=GROQ_TIMEOUT_SECONDS), None
    except Exception as e:
        print(f"Groq client init error: {e}")
        return None, f"⚠️ שגיאת Groq: שגיאת אתחול ({e})."

def _groq_chat(client, system: str, user: str, max_tokens: int = 1024,
               temperature: float = 0.3) -> tuple:
    """Single Groq chat completion call. Returns (content_or_None, error_or_None)."""
    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip(), None
    except Exception as e:
        print(f"Groq chat error: {e}")
        if _is_rate_limit_error(e):
            return None, _format_rate_limit_message(e)
        return None, f"⚠️ שגיאת Groq: {e}"

_SENTENCE_END_CHARS = (".", "!", "?", ":", "״")

def _looks_complete(answer: str | None, min_words: int) -> bool:
    """Cheap signal that Groq finished its thought rather than getting cut off."""
    if not answer:
        return False
    if len(answer.split()) < min_words:
        return False
    return answer.rstrip().endswith(_SENTENCE_END_CHARS)

def _complete_if_needed(client, system: str, user: str, answer: str | None,
                        min_words: int, max_tokens: int, temperature: float) -> str | None:
    """Deep-tab only: a single retry asking Groq to finish an incomplete/short answer."""
    if not answer or _looks_complete(answer, min_words):
        return answer
    with st.spinner("✍️ מנסח תשובה..."):
        continued, _err = _groq_chat(
            client, system,
            f"{user}\n\nהתשובה הקודמת שכתבת (לא הושלמה):\n{answer}\n\n"
            f"התשובה לא הושלמה. המשך מהמקום שעצרת ותסיים במשפט שלם.",
            max_tokens=max_tokens,
            temperature=temperature,
        )
    return continued or answer

_GROQ_SYSTEM_PROMPT = """אתה גמי תורה — עוזר תורני מומחה ברמת פוסק הלכה, המשיב בעברית שוטפת וברורה.

כללי תשובה מחייבים:
א. פתח בציון המקור העיקרי (שם ספר בלבד, ללא ציטוט ישיר).
ב. הבחן בין דעת רוב הפוסקים לדעת מיעוט.
ג. ציין הבדלי מנהג אשכנזים/ספרדים רק כשברור שיש.
ד. הזכר שמות פוסקים מוכרים: משנה ברורה, בן איש חי, שולחן ערוך הרב, ערוך השולחן.
ה. סיים תמיד ב"למעשה:" עם הנחיה מעשית ברורה וקצרה.
ו. אם יש מחלוקת גדולה בין הפוסקים — ציין זאת ואמור "יש להתייעץ עם רב".
ז. כתוב בפסקאות זורמות — לא רשימות ממוספרות.
ח. אל תמציא מקורות — השתמש רק במה שניתן לך.
ט. אל תפסיק באמצע משפט — סיים תמיד תשובה שלמה.
י. בסוף כתוב תמיד: "לעניין הלכה למעשה יש להיוועץ עם רב מורה הוראה."""

QUICK_INSTRUCTION = (
    f"ענה בדיוק ב-5-6 משפטים (לפחות {MIN_ANSWER_WORDS_QUICK} מילים), "
    f"כולל דוגמה מעשית אחת. אל תרחיב מעבר לכך."
)

class _GroqCallFailed(Exception):
    """Raised so st.cache_data never caches a failed Groq call (only successes are cached)."""

def _track_groq_tokens(estimate: int) -> None:
    """Bump the session-scoped usage estimate — only called on a real cache-miss API call."""
    st.session_state.groq_tokens_used = st.session_state.get("groq_tokens_used", 0) + estimate

@st.cache_data(show_spinner=False, ttl=GROQ_CACHE_TTL_SECONDS)
def _ask_groq_cached(query: str, sources: list, kitzur: list, quick: bool) -> str:
    """Cached core of ask_groq; raises _GroqCallFailed (never cached) on any Groq error."""
    client, err = _groq_client()
    if not client:
        raise _GroqCallFailed(err)
    blob = _format_sources_for_groq(sources, kitzur, quick)
    user = (
        f"נושא: {query}\n\n"
        f"השתמש רק במקורות הרלוונטיים ישירות לנושא \"{query}\" — "
        f"התעלם לחלוטין ממקורות העוסקים בנושאים אחרים.\n\n"
        + (f"{QUICK_INSTRUCTION}\n\n" if quick else "")
        + f"מקורות:\n{blob}"
    )
    if quick:
        answer, err = _groq_chat(client, _GROQ_SYSTEM_PROMPT, user,
                                  max_tokens=GROQ_QUICK_MAX_TOKENS,
                                  temperature=GROQ_SOURCE_TEMPERATURE)
        if err:
            raise _GroqCallFailed(err)
        _track_groq_tokens(GROQ_EST_TOKENS_PER_SOURCE_CALL)
        return answer
    answer, err = _groq_chat(client, _GROQ_SYSTEM_PROMPT, user,
                              max_tokens=GROQ_DEEP_MAX_TOKENS,
                              temperature=GROQ_SOURCE_TEMPERATURE)
    if err:
        raise _GroqCallFailed(err)
    answer = _complete_if_needed(client, _GROQ_SYSTEM_PROMPT, user, answer,
                                  MIN_ANSWER_WORDS_DEEP, GROQ_DEEP_MAX_TOKENS,
                                  GROQ_SOURCE_TEMPERATURE)
    _track_groq_tokens(GROQ_EST_TOKENS_PER_SOURCE_CALL)
    return answer

def ask_groq(query: str, sources: list, kitzur: list, quick: bool = False) -> tuple:
    """Ask Groq to answer using the given Sefaria/kitzur sources. Returns (answer, error)."""
    if not sources and not kitzur:
        return None, None
    try:
        return _ask_groq_cached(query, sources, kitzur, quick), None
    except _GroqCallFailed as e:
        return None, str(e)

_GROQ_GENERAL_SYSTEM_PROMPT = (
    "אתה גמי תורה — רב מלומד המסביר תורה בעברית שוטפת, ברורה ומדויקת. "
    "לא נמצאו מקורות ספציפיים בספריא עבור השאלה — ענה מתוך ידיעותיך הכלליות בתורה. "
    "ציין באילו ספרי הלכה מרכזיים (שולחן ערוך, משנה ברורה, משנה תורה וכדומה) הנושא נדון, "
    "מבלי לצטט סימן/סעיף מדויק אם אינך בטוח בו. "
    "היה ספציפי לגבי דעת רוב הפוסקים, וציין הבדלי מנהג אשכנז/ספרד רק כשברור שיש. "
    "כתוב בפסקאות זורמות, לא רשימות ממוספרות, באורך של כ-150–200 מילים. "
    "סיים בפסקת סיכום מעשי קצרה תחת הכותרת \"למעשה:\". "
    "אל תפסיק באמצע משפט — סיים תמיד תשובה שלמה. "
    "בסוף כתוב תמיד: 'לעניין הלכה למעשה יש להיוועץ עם רב מורה הוראה.'"
)

@st.cache_data(show_spinner=False, ttl=GROQ_CACHE_TTL_SECONDS)
def _ask_groq_general_cached(query: str, quick: bool) -> str:
    """Cached core of ask_groq_general; raises _GroqCallFailed (never cached) on error."""
    client, err = _groq_client()
    if not client:
        raise _GroqCallFailed(err)
    user = f"נושא: {query}\n\n{QUICK_INSTRUCTION}" if quick else f"נושא: {query}"
    if quick:
        answer, err = _groq_chat(client, _GROQ_GENERAL_SYSTEM_PROMPT, user,
                                  max_tokens=GROQ_QUICK_MAX_TOKENS,
                                  temperature=GROQ_GENERAL_TEMPERATURE)
        if err:
            raise _GroqCallFailed(err)
        _track_groq_tokens(GROQ_EST_TOKENS_PER_GENERAL_CALL)
        return answer
    answer, err = _groq_chat(client, _GROQ_GENERAL_SYSTEM_PROMPT, user,
                              max_tokens=GROQ_GENERAL_MAX_TOKENS,
                              temperature=GROQ_GENERAL_TEMPERATURE)
    if err:
        raise _GroqCallFailed(err)
    answer = _complete_if_needed(client, _GROQ_GENERAL_SYSTEM_PROMPT, user, answer,
                                  MIN_ANSWER_WORDS_DEEP, GROQ_GENERAL_MAX_TOKENS,
                                  GROQ_GENERAL_TEMPERATURE)
    _track_groq_tokens(GROQ_EST_TOKENS_PER_GENERAL_CALL)
    return answer

def ask_groq_general(query: str, quick: bool = False) -> tuple:
    """Fallback: no Sefaria/kitzur results — answer from general Torah knowledge.
    Returns (answer_or_None, error_or_None)."""
    try:
        return _ask_groq_general_cached(query, quick), None
    except _GroqCallFailed as e:
        return None, str(e)

@st.cache_data(show_spinner=False, ttl=300)
def search_sefaria(query: str, size: int) -> tuple:
    """Search Sefaria, score results for topical relevance, and return (results_list, error)."""
    seen, seen_he_refs, results = set(), set(), []
    last_error = None

    def _fetch(q: str) -> None:
        nonlocal last_error
        try:
            r = requests.post(
                SEFARIA_URL,
                headers={"Content-Type": "application/json"},
                json={"query": q, "type": "text", "size": size,
                      "field": "naive_lemmatizer", "slop": 10,
                      "source_proj": ["heRef", "ref", "path"]},
                timeout=SEFARIA_TIMEOUT_SECONDS,
            )
            r.raise_for_status()
            for hit in (r.json().get("hits", {}).get("hits") or []):
                try:
                    src      = hit.get("_source", {})
                    ref      = src.get("ref") or re.sub(r'\s*\([^)]*\)\s*$', '', hit.get("_id", "")).strip()
                    he_ref   = strip_html(src.get("heRef") or ref)
                    path     = src.get("path", "")
                    snippets = hit.get("highlight", {}).get("naive_lemmatizer", [])
                    he       = strip_html(" ... ".join(snippets))
                    if (ref and he and len(he) > SEFARIA_MIN_SNIPPET_CHARS
                            and ref not in seen and he_ref not in seen_he_refs):
                        seen.add(ref)
                        seen_he_refs.add(he_ref)
                        results.append({
                            "heRef": he_ref,
                            "he":    he[:600] + ("..." if len(he) > 600 else ""),
                            "_path": path,
                        })
                except Exception:
                    continue
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

    words = [w for w in primary.split() if len(w) > 1]
    tried = {primary, query}
    if len(words) >= 2:
        # Multi-word query: also search each word alone, so results matching
        # BOTH words (rewarded in _relevance_score) can be found and ranked up.
        for w in words[:3]:
            if w not in tried:
                tried.add(w)
                _fetch(w)

    if len(results) < SEARCH_EXPANSION_THRESHOLD:
        for w in [w for w in words if w not in tried][:3]:
            if len(results) >= SEARCH_EXPANSION_THRESHOLD:
                break
            tried.add(w)
            _fetch(w)

    for r in results:
        r["_score"] = _relevance_score(r, words)
    results.sort(key=lambda r: (-r["_score"], _halachic_rank(r["_path"])))

    # No cap on the number of results returned — callers get everything found.
    final_error = last_error if len(results) < size else None
    return (
        [{"heRef": r["heRef"], "he": r["he"]} for r in results],
        final_error,
    )

@st.cache_data(show_spinner=False)
def _load_kitzur_lines() -> list:
    """Load and cache the local Kitzur Shulchan Arukh text file, split into lines."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kitzur_shulchan_aruch.txt")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read().split("\n")

@st.cache_data(show_spinner=False)
def search_local_kitzur(query: str) -> list:
    """Keyword-match the query against the local Kitzur text and return the top-scoring sections."""
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

SOURCE_TYPE_EMOJI = (
    (("קיצור שולחן ערוך",), "📔"),
    (("שולחן ערוך",), "📘"),
    (("משנה תורה",), "📗"),
    (("תלמוד", "בבלי", "ירושלמי"), "📜"),
    (('שו"ת', "שו״ת", "תשובות"), "📙"),
)

def _source_emoji(he_ref: str) -> str:
    """Pick a small emoji hinting at the source's type, based on keywords in its title."""
    for keywords, emoji in SOURCE_TYPE_EMOJI:
        if any(k in he_ref for k in keywords):
            return emoji
    return "📖"

def _render_source_card(s: dict) -> None:
    """Render a single Sefaria source card with a type-based emoji."""
    emoji = _source_emoji(s["heRef"])
    st.markdown(
        f'<div class="source-card">'
        f'<div class="source-card-title">{emoji} {html.escape(s["heRef"])}</div>'
        f'<div class="source-card-text">{html.escape(s["he"])}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

def _render_groq_error(groq_error: str, margin: bool = False) -> None:
    """Render a Groq error/rate-limit message (already carries its own icon/prefix)."""
    style = ' style="margin-bottom:12px"' if margin else ''
    msg = html.escape(groq_error).replace("\n", "<br>")
    st.markdown(f'<div class="sefaria-error"{style}>{msg}</div>', unsafe_allow_html=True)

NO_RESULTS_MSG = "לא נמצא מידע על נושא זה. נסה: שבת, כשרות, תפילה, ציצית, תפילין, אבילות"

def render_results(sources: list, kitzur: list, error: str | None = None,
                   ai_answer: str | None = None, ai_general: bool = False,
                   groq_error: str | None = None) -> None:
    """Render the full results panel: AI answer/error, kitzur sections, and source cards."""
    if error and not sources and not kitzur and not ai_answer:
        st.markdown(
            f'<div class="sefaria-error">⚠️ {html.escape(error)}</div>',
            unsafe_allow_html=True,
        )
        return

    if not sources and not kitzur and not ai_answer:
        if groq_error:
            _render_groq_error(groq_error)
            return
        st.markdown(
            f'<div class="no-results">{html.escape(NO_RESULTS_MSG)}</div>',
            unsafe_allow_html=True,
        )
        return

    st.caption(f"נמצאו {len(sources)} מקורות בספריא + {len(kitzur)} קטעים בקיצור שולחן ערוך")

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
    elif groq_error:
        _render_groq_error(groq_error, margin=True)

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
        for s in sources[:VISIBLE_SOURCES_DEFAULT]:
            _render_source_card(s)
        hidden = sources[VISIBLE_SOURCES_DEFAULT:]
        if hidden:
            with st.expander(f"הצג עוד {len(hidden)} מקורות"):
                for s in hidden:
                    _render_source_card(s)

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

if not st.secrets.get("GROQ_API_KEY", ""):
    st.warning("מפתח Groq חסר — תשובות AI לא יעבדו, אך חיפוש במקורות עדיין זמין.")

_defaults = {
    "history": [], "deep_q": "", "quick_q": "",
    "_last_deep": "", "_last_quick": "",
    "deep_input_v": 0, "quick_input_v": 0,
    "deep_sources": [], "deep_kitzur": [], "deep_error": None,
    "deep_ai_answer": None, "deep_ai_general": False, "deep_groq_error": None,
    "quick_sources": [], "quick_kitzur": [], "quick_error": None,
    "quick_ai_answer": None, "quick_ai_general": False, "quick_groq_error": None,
    "groq_tokens_used": 0,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

if st.session_state.groq_tokens_used > GROQ_DAILY_TOKEN_LIMIT * GROQ_TOKEN_WARNING_RATIO:
    st.caption(
        f"⚠️ צריכת Groq גבוהה בסשן זה: כ-{st.session_state.groq_tokens_used:,} "
        f"טוקנים משוערים מתוך מכסה יומית של כ-{GROQ_DAILY_TOKEN_LIMIT:,}."
    )

def _set_query_and_rerun(q: str) -> None:
    """Populate both tabs with q, clear cached results, and rerun — shared by the
    example buttons and clickable history entries."""
    st.session_state.update({
        "deep_q": q, "quick_q": q,
        "_last_deep": "", "_last_quick": "",
        "deep_sources": [], "deep_kitzur": [], "deep_error": None,
        "deep_ai_answer": None, "deep_ai_general": False, "deep_groq_error": None,
        "quick_sources": [], "quick_kitzur": [], "quick_error": None,
        "quick_ai_answer": None, "quick_ai_general": False, "quick_groq_error": None,
    })
    # bump the widget key version to force the text_input to remount with the new value
    st.session_state.deep_input_v  += 1
    st.session_state.quick_input_v += 1
    st.rerun()

st.markdown('<p style="color:#c5a059;font-weight:600;">💡 דוגמאות לחיפוש:</p>', unsafe_allow_html=True)
EXAMPLES = ["חשמל בשבת", "כיבוד הורים", "אבילות", "כשרות"]
for i, (col, q) in enumerate(zip(st.columns(4), EXAMPLES)):
    if col.button(q, key=f"ex_{i}", use_container_width=True):
        _set_query_and_rerun(q)

tab_deep, tab_quick = st.tabs([
    "🏛️   עיון מעמיק — כמה שיותר מקורות",
    f"⚡   בירור מהיר — עד {SEFARIA_QUICK} מקורות",
])

with tab_deep:
    st.markdown(
        '<p style="color:#c5a059;font-weight:600;margin-top:8px;">'
        'חיפוש נרחב — כמה שיותר מקורות מספריא + קיצור שולחן ערוך</p>',
        unsafe_allow_html=True,
    )
    col_input, col_btn = st.columns([5, 1])
    _deep_key = f"input_deep_{st.session_state.deep_input_v}"
    with col_input:
        q_deep = st.text_input(
            "🔍 חפש נושא, מושג או שאלה תורנית:",
            value=st.session_state.deep_q,
            key=_deep_key,
        )
    q_deep = sanitize_query(q_deep)
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
                    "deep_ai_answer": None, "deep_ai_general": False, "deep_groq_error": None,
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
        with st.spinner(f"🔍 מחפש ב-{SEFARIA_DEEP} מקורות תורניים..."):
            sources, err = search_sefaria(q_deep.strip(), SEFARIA_DEEP)
            kitzur       = search_local_kitzur(q_deep.strip())
        ai_general = not sources and not kitzur and not err
        with st.spinner("🤖 גמי תורה לומד את המקורות..."):
            if ai_general:
                ai_answer, groq_err = ask_groq_general(q_deep.strip())
            else:
                ai_answer, groq_err = ask_groq(q_deep.strip(), sources, kitzur)
        st.session_state.deep_sources    = sources
        st.session_state.deep_kitzur     = kitzur
        st.session_state.deep_error      = err
        st.session_state.deep_ai_answer  = ai_answer
        st.session_state.deep_ai_general = ai_general
        st.session_state.deep_groq_error = groq_err

    # render cached results — survives tab switches
    if (st.session_state.deep_sources or st.session_state.deep_kitzur
            or st.session_state.deep_error or st.session_state.deep_ai_answer
            or st.session_state.deep_groq_error):
        render_results(
            st.session_state.deep_sources,
            st.session_state.deep_kitzur,
            st.session_state.deep_error,
            st.session_state.deep_ai_answer,
            st.session_state.deep_ai_general,
            st.session_state.deep_groq_error,
        )
    elif st.session_state._last_deep:
        render_results([], [], None)

with tab_quick:
    st.markdown(
        '<p style="color:#c5a059;font-weight:600;margin-top:8px;">'
        f'חיפוש ממוקד — עד {SEFARIA_QUICK} מקורות מספריא</p>',
        unsafe_allow_html=True,
    )
    col_input_q, col_btn_q = st.columns([5, 1])
    _quick_key = f"input_quick_{st.session_state.quick_input_v}"
    with col_input_q:
        q_quick = st.text_input(
            "🔍 חפש נושא, מושג או שאלה תורנית:",
            value=st.session_state.quick_q,
            key=_quick_key,
        )
    q_quick = sanitize_query(q_quick)
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
                    "quick_ai_answer": None, "quick_ai_general": False, "quick_groq_error": None,
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
        with st.spinner(f"🔍 מחפש ב-{SEFARIA_QUICK} מקורות תורניים..."):
            sources_q, err_q = search_sefaria(q_quick.strip(), SEFARIA_QUICK)
            kitzur_q         = search_local_kitzur(q_quick.strip())
        ai_general_q = not sources_q and not kitzur_q and not err_q
        with st.spinner("🤖 גמי תורה לומד את המקורות..."):
            if ai_general_q:
                ai_answer_q, groq_err_q = ask_groq_general(q_quick.strip(), quick=True)
            else:
                ai_answer_q, groq_err_q = ask_groq(q_quick.strip(), sources_q, kitzur_q, quick=True)
        st.session_state.quick_sources     = sources_q
        st.session_state.quick_kitzur      = kitzur_q
        st.session_state.quick_error       = err_q
        st.session_state.quick_ai_answer   = ai_answer_q
        st.session_state.quick_ai_general  = ai_general_q
        st.session_state.quick_groq_error  = groq_err_q

    if (st.session_state.quick_sources or st.session_state.quick_kitzur
            or st.session_state.quick_error or st.session_state.quick_ai_answer
            or st.session_state.quick_groq_error):
        render_results(
            st.session_state.quick_sources,
            st.session_state.quick_kitzur,
            st.session_state.quick_error,
            st.session_state.quick_ai_answer,
            st.session_state.quick_ai_general,
            st.session_state.quick_groq_error,
        )
    elif st.session_state._last_quick:
        render_results([], [], None)

if st.session_state.history:
    st.write("---")
    st.markdown("### 📚 שאלות קודמות:")
    for i, q in enumerate(st.session_state.history):
        if st.button(f"🔹 {q}", key=f"hist_{i}"):
            _set_query_and_rerun(q)
