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

# ── עזרים ───────────────────────────────────────────────────────
def get_base64_image(img_path):
    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def strip_html(text: str) -> str:
    """הסרת תגיות HTML מטקסט."""
    return re.sub(r'<[^>]+>', ' ', text).strip()

def search_sefaria(query: str, num_results: int = 5) -> list:
    """
    חיפוש מקורות רלוונטיים במאגר ספריא.
    מחזיר רשימת מקורות עם הפנייה והטקסט העברי.
    """
    try:
        resp = requests.get(
            "https://www.sefaria.org/api/search-wrapper",
            params={
                "query": query,
                "type": "text",
                "size": num_results,
                "field": "naive_lemmatizer"
            },
            timeout=8
        )
        data = resp.json()
        results = []
        for hit in data.get("hits", {}).get("hits", []):
            src = hit.get("_source", {})
            ref    = src.get("ref", "")
            he_ref = src.get("heRef", ref)
            he_text = strip_html(src.get("he", ""))
            if ref and he_text and len(he_text) > 15:
                results.append({
                    "ref":   ref,
                    "heRef": he_ref,
                    "he":    he_text[:600] + ("..." if len(he_text) > 600 else "")
                })
        return results
    except Exception:
        return []

# ── CSS ──────────────────────────────────────────────────────────
st.markdown("""
<style>
body, p, div, h1, h2, h3, h4, h5, h6, li, span, input, label,
textarea, .stMarkdown, .stAlert, .stTextInput label {
    direction: rtl !important;
    text-align: right !important;
    font-family: 'Segoe UI', Arial, sans-serif;
}
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
    padding-left: 5rem !important;
    padding-right: 5rem !important;
    max-width: 1100px !important;
}
.premium-header {
    background: linear-gradient(135deg, #0b151f, #142436);
    border-bottom: 3px solid #c5a059;
    padding: 36px 40px;
    border-radius: 16px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    margin-bottom: 30px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 30px;
}
.header-text-container { flex: 1; }
.premium-header h1 {
    color: #f4ecd8 !important;
    font-size: 2.8rem !important;
    font-weight: 800;
    margin: 0 0 8px 0 !important;
}
.premium-header p {
    color: #c5a059 !important;
    font-size: 1.2rem !important;
    margin: 0 !important;
}
.rabbi-banner-img {
    width: 220px;
    height: auto;
    border-radius: 14px;
    border: 3px solid #c5a059;
    box-shadow: 0 6px 25px rgba(0,0,0,0.5);
}
.stTextInput > div > div > input {
    direction: rtl !important;
    text-align: right !important;
    border: 2px solid #223446 !important;
    border-radius: 12px !important;
    padding: 16px 20px !important;
    font-size: 17px !important;
    background-color: #0f1923 !important;
    color: #ffffff !important;
    transition: border-color 0.3s;
}
.stTextInput > div > div > input:focus {
    border-color: #c5a059 !important;
    box-shadow: 0 0 12px rgba(197,160,89,0.2) !important;
}
.stButton > button {
    direction: rtl !important;
    border-radius: 10px !important;
    border: 1.5px solid #c5a059 !important;
    background: transparent !important;
    color: #c5a059 !important;
    font-size: 13px !important;
    padding: 6px 14px !important;
    width: 100% !important;
    transition: all 0.2s;
}
.stButton > button:hover {
    background: #c5a059 !important;
    color: #0b151f !important;
}
.disclaimer-text {
    color: #7a7a7a;
    font-size: 13px;
    margin-top: 8px;
    font-style: italic;
}
h1, h2, h3 { color: #c5a059 !important; font-weight: 600 !important; }
.answer-box {
    background: #0f1923;
    border: 1px solid #223446;
    border-radius: 14px;
    padding: 28px 32px;
    color: #f0e6d3;
    font-size: 16px;
    line-height: 2;
    direction: rtl;
    text-align: right;
}
.source-box {
    background: #0d1e2e;
    border-right: 4px solid #c5a059;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 12px;
    direction: rtl;
    text-align: right;
}
.source-ref {
    color: #c5a059;
    font-weight: 700;
    font-size: 15px;
    margin-bottom: 6px;
}
.source-text {
    color: #c8bfa8;
    font-size: 14px;
    line-height: 1.8;
}
.example-label {
    color: #c5a059;
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 8px;
}
#MainMenu { visibility: hidden !important; }
footer { visibility: hidden !important; }
header { visibility: hidden !important; }
[data-testid="manage-app-button"]  { display: none !important; }
[data-testid="stToolbarActions"]   { display: none !important; }
[data-testid="stToolbar"]          { display: none !important; }
.stDeployButton                    { display: none !important; }
</style>

<script>
(function() {
    const hide = () => {
        ['[data-testid="manage-app-button"]','[data-testid="stToolbarActions"]',
         '[data-testid="stToolbar"]','.stDeployButton','footer']
        .forEach(s => document.querySelectorAll(s).forEach(
            el => el.style.setProperty('display','none','important')
        ));
    };
    new MutationObserver(hide).observe(document.documentElement,{childList:true,subtree:true});
    hide(); setTimeout(hide,1000); setTimeout(hide,3000);
})();
</script>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────
rabbi_base64 = get_base64_image("rabbi.jpeg") or get_base64_image("rabbi.png")
header_html = f"""
<div class="premium-header">
  <div class="header-text-container">
    <h1>ג'מי תורה 📜</h1>
    <p>מערכת בינה מלאכותית מתקדמת לעיון, פסיקה ולימוד תורני</p>
  </div>
  {'<img src="data:image/jpeg;base64,' + rabbi_base64 + '" class="rabbi-banner-img" />' if rabbi_base64 else ''}
</div>"""
st.markdown(header_html, unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────
if "history"           not in st.session_state: st.session_state.history           = []
if "selected_question" not in st.session_state: st.session_state.selected_question = ""

# ── שאלות לדוגמה ─────────────────────────────────────────────────
st.markdown('<p class="example-label">💡 שאלות לדוגמה — לחץ כדי לשאול:</p>', unsafe_allow_html=True)
examples = ["מה הלכות שבת לגבי חשמל?", "מקור מצוות כיבוד אב ואם", "דיני אבילות שבעה", "הלכות כשרות בסיסיות"]
for i, (col, q) in enumerate(zip(st.columns(4), examples)):
    if col.button(q, key=f"ex_{i}", use_container_width=True):
        st.session_state.selected_question = q
        st.rerun()

# ── תיבת שאלה ────────────────────────────────────────────────────
user_question = st.text_input(
    "🔮 שאל שאלה בתנ\"ך, בגמרא, בהלכה או בקיצור שולחן ערוך:",
    value=st.session_state.selected_question,
    key="main_input"
)
st.markdown(
    '<div class="disclaimer-text">⚠️ ג\'מי תורה הוא כלי עזר ללימוד ועלול לטעות. לעניין הלכה למעשה — יש להיוועץ ברב מורה הוראה.</div>',
    unsafe_allow_html=True
)
st.write("---")

# ── עיבוד שאלה ───────────────────────────────────────────────────
if user_question and user_question.strip():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("⚠️ מפתח ה-API לא הוגדר ב-Secrets של המערכת.")
    else:
        # שלב א׳ — חיפוש מקורות בספריא
        with st.spinner("🔍 מחפש מקורות רלוונטיים במאגר ספריא..."):
            sources = search_sefaria(user_question.strip())

        # הצגת המקורות שנמצאו
        if sources:
            sources_html = "".join(
                f'<div class="source-box">'
                f'<div class="source-ref">📖 {s["heRef"]}</div>'
                f'<div class="source-text">{s["he"]}</div>'
                f'</div>'
                for s in sources
            )
            with st.expander(f"📚 {len(sources)} מקורות שנמצאו ממאגר ספריא — לחץ לצפייה", expanded=False):
                st.markdown(sources_html, unsafe_allow_html=True)
        else:
            st.info("לא נמצאו מקורות ישירים בספריא — ג'מי תורה ישתמש בידיעותיו הרחבות.")

        # שלב ב׳ — בניית הפרומפט עם המקורות
        context_block = ""
        if sources:
            context_block = "\n\n---\nמקורות שנמצאו עבור שאלה זו:\n"
            for i, s in enumerate(sources, 1):
                context_block += f"[{i}] {s['heRef']}: {s['he']}\n\n"
            context_block += "---\nהתבסס על מקורות אלו ועל ידיעותיך. ציין אותם לפי שמם בתשובה."

        system_instruction = """אתה ג'מי תורה — מנוע בינה מלאכותית תורני ברמה של גדול הדור.

בקיאותך: תנ"ך, משנה, תלמוד בבלי וירושלמי, רש"י, תוספות, רמב"ם, שולחן ערוך וכל נושאי הכלים, ראשונים ואחרונים, שו"ת מרן הגר"מ פיינשטיין, הגר"ע יוסף, הגרש"ז אויערבאך.

כללי תשובה:
א. פתח בפסוק רלוונטי אם ישנו.
ב. חלק לסעיפים ברורים עם כותרות מודגשות.
ג. ציין מקורות מדויקים: שם הספר + פרק + סעיף.
ד. הצג דעות שונות כשיש מחלוקת.
ה. הבדל בין הלכה למעשה לדיון תיאורטי.
ו. סיים ב"למעשה..." — סיכום מעשי ברור.
ז. כתוב בעברית בלבד. תשובה מקיפה — אל תקצר."""

        # שלב ג׳ — קריאה ל-Gemini עם ניסיון חוזר
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.65,
            safety_settings=[
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH",       threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT",        threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
            ]
        )
        full_prompt = user_question.strip() + context_block

        st.markdown("### ✍️ תשובת ג'מי תורה:")
        answer_placeholder = st.empty()
        full_response      = ""
        max_retries        = 3

        for attempt in range(max_retries):
            try:
                full_response = ""
                with st.spinner("...ג'מי תורה מעיין במקורות ויוצר תשובה מפורטת"):
                    for chunk in client.models.generate_content_stream(
                        model="gemini-1.5-flash",
                        contents=full_prompt,
                        config=config
                    ):
                        if chunk.text:
                            full_response += chunk.text
                            answer_placeholder.markdown(
                                f'<div class="answer-box">{full_response}▌</div>',
                                unsafe_allow_html=True
                            )
                answer_placeholder.markdown(
                    f'<div class="answer-box">{full_response}</div>',
                    unsafe_allow_html=True
                )
                st.balloons()
                st.session_state.history.insert(0, {"q": user_question.strip(), "a": full_response})
                st.session_state.selected_question = ""
                break  # הצליח — יוצא מהלולאה

            except Exception as e:
                err = str(e)
                is_overload = "503" in err or "UNAVAILABLE" in err or "high demand" in err.lower()
                if is_overload and attempt < max_retries - 1:
                    wait = 3 * (attempt + 1)
                    st.toast(f"⏳ השרת עמוס, מנסה שוב בעוד {wait} שניות... ({attempt+1}/{max_retries})")
                    time.sleep(wait)
                    continue
                elif "quota" in err.lower() or "429" in err:
                    st.error("⚠️ חרגת ממכסת השימוש. נסה שוב בעוד מספר שניות.")
                elif "401" in err or "api_key" in err.lower():
                    st.error("⚠️ מפתח ה-API שגוי. בדוק את ה-Secrets ב-Streamlit.")
                elif is_overload:
                    st.error("⚠️ השרת של גוגל עמוס כרגע. נסה שוב בעוד דקה.")
                else:
                    st.error(f"❌ שגיאה: {err}")
                break

# ── היסטוריה ─────────────────────────────────────────────────────
if st.session_state.history:
    st.write("---")
    st.markdown("### 📚 שאלות קודמות:")
    for item in st.session_state.history[:5]:
        with st.expander(f"🔹 {item['q'][:70]}{'...' if len(item['q']) > 70 else ''}"):
            st.markdown(f'<div class="answer-box" style="font-size:14px">{item["a"]}</div>', unsafe_allow_html=True)