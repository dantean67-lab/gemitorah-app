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
    return re.sub(r'<[^>]+>', ' ', text).strip()
 
def search_sefaria(query: str, num_results: int = 6) -> list:
    """חיפוש מקורות במאגר ספריא — מספר ניסיונות עם שיטות שונות."""
    seen, results = set(), []
 
    def _fetch(q, n):
        try:
            r = requests.get(
                "https://www.sefaria.org/api/search-wrapper",
                params={"query": q, "type": "text", "size": n, "field": "naive_lemmatizer"},
                timeout=8
            )
            for hit in r.json().get("hits", {}).get("hits", []):
                src = hit.get("_source", {})
                ref  = src.get("ref", "")
                he_r = src.get("heRef", ref)
                he   = strip_html(src.get("he", ""))
                if ref and he and len(he) > 15 and ref not in seen:
                    seen.add(ref)
                    results.append({
                        "ref":   ref,
                        "heRef": he_r,
                        "he":    he[:600] + ("..." if len(he) > 600 else "")
                    })
        except Exception:
            pass
 
    # חיפוש 1 — השאלה המלאה
    _fetch(query, num_results)
    # חיפוש 2 — מילות מפתח (ללא מילות שאלה)
    keywords = re.sub(r'\b(מה|האם|כיצד|למה|מדוע|איך|מתי|היכן|מי|הסבר|פרט|ספר)\b', '', query).strip()
    if keywords and keywords != query:
        _fetch(keywords, num_results)
 
    return results[:num_results]
 
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
    padding-top: 2rem !important; padding-bottom: 2rem !important;
    padding-left: 5rem !important; padding-right: 5rem !important;
    max-width: 1100px !important;
}
.premium-header {
    background: linear-gradient(135deg, #0b151f, #142436);
    border-bottom: 3px solid #c5a059;
    padding: 36px 40px; border-radius: 16px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    margin-bottom: 30px;
    display: flex; justify-content: space-between; align-items: center; gap: 30px;
}
.header-text-container { flex: 1; }
.premium-header h1 {
    color: #f4ecd8 !important; font-size: 2.8rem !important;
    font-weight: 800; margin: 0 0 8px 0 !important;
}
.premium-header p { color: #c5a059 !important; font-size: 1.2rem !important; margin: 0 !important; }
.rabbi-banner-img {
    width: 220px; height: auto; border-radius: 14px;
    border: 3px solid #c5a059; box-shadow: 0 6px 25px rgba(0,0,0,0.5);
}
.stTextInput > div > div > input {
    direction: rtl !important; text-align: right !important;
    border: 2px solid #223446 !important; border-radius: 12px !important;
    padding: 16px 20px !important; font-size: 17px !important;
    background-color: #0f1923 !important; color: #ffffff !important;
    transition: border-color 0.3s;
}
.stTextInput > div > div > input:focus {
    border-color: #c5a059 !important;
    box-shadow: 0 0 12px rgba(197,160,89,0.2) !important;
}
.stButton > button {
    direction: rtl !important; border-radius: 10px !important;
    border: 1.5px solid #c5a059 !important; background: transparent !important;
    color: #c5a059 !important; font-size: 13px !important;
    padding: 6px 14px !important; width: 100% !important; transition: all 0.2s;
}
.stButton > button:hover { background: #c5a059 !important; color: #0b151f !important; }
.disclaimer-text { color: #7a7a7a; font-size: 13px; margin-top: 8px; font-style: italic; }
h1, h2, h3 { color: #c5a059 !important; font-weight: 600 !important; }
.answer-box {
    background: #0f1923; border: 1px solid #223446; border-radius: 14px;
    padding: 28px 32px; color: #f0e6d3; font-size: 16px;
    line-height: 2; direction: rtl; text-align: right;
}
.source-box {
    background: #0d1e2e; border-right: 4px solid #c5a059;
    border-radius: 8px; padding: 12px 16px; margin-bottom: 12px;
    direction: rtl; text-align: right;
}
.source-ref  { color: #c5a059; font-weight: 700; font-size: 15px; margin-bottom: 6px; }
.source-text { color: #c8bfa8; font-size: 14px; line-height: 1.8; }
.example-label { color: #c5a059; font-size: 14px; font-weight: 600; margin-bottom: 8px; }
#MainMenu { visibility: hidden !important; }
footer    { visibility: hidden !important; }
header    { visibility: hidden !important; }
[data-testid="manage-app-button"] { display: none !important; }
[data-testid="stToolbarActions"]  { display: none !important; }
[data-testid="stToolbar"]         { display: none !important; }
.stDeployButton                   { display: none !important; }
</style>
<script>
(function(){
    const hide=()=>{
        ['[data-testid="manage-app-button"]','[data-testid="stToolbarActions"]',
         '[data-testid="stToolbar"]','.stDeployButton','footer']
        .forEach(s=>document.querySelectorAll(s).forEach(
            el=>el.style.setProperty('display','none','important')
        ));
    };
    new MutationObserver(hide).observe(document.documentElement,{childList:true,subtree:true});
    hide(); setTimeout(hide,1000); setTimeout(hide,3000);
})();
</script>
""", unsafe_allow_html=True)
 
# ── Header ───────────────────────────────────────────────────────
rabbi_base64 = get_base64_image("rabbi.jpeg") or get_base64_image("rabbi.png")
img_tag = f'<img src="data:image/jpeg;base64,{rabbi_base64}" class="rabbi-banner-img" />' if rabbi_base64 else ''
st.markdown(f"""
<div class="premium-header">
  <div class="header-text-container">
    <h1>ג'מי תורה 📜</h1>
    <p>מערכת בינה מלאכותית מתקדמת לעיון, פסיקה ולימוד תורני</p>
  </div>
  {img_tag}
</div>""", unsafe_allow_html=True)
 
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
    value=st.session_state.selected_question, key="main_input"
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
        # שלב א׳ — חיפוש מקורות בספריא (בשקט, ללא הודעות שגיאה)
        with st.spinner("🔍 מחפש מקורות ממאגר ספריא..."):
            sources = search_sefaria(user_question.strip())
 
        # הצגת מקורות — רק אם נמצאו, ובלי שום הודעה אם לא נמצאו
        if sources:
            sources_html = "".join(
                f'<div class="source-box">'
                f'<div class="source-ref">📖 {s["heRef"]}</div>'
                f'<div class="source-text">{s["he"]}</div>'
                f'</div>'
                for s in sources
            )
            with st.expander(f"📚 {len(sources)} מקורות ממאגר ספריא", expanded=False):
                st.markdown(sources_html, unsafe_allow_html=True)
 
        # שלב ב׳ — בניית הפרומפט
        context_block = ""
        if sources:
            context_block = "\n\n---\nמקורות שנמצאו:\n"
            for i, s in enumerate(sources, 1):
                context_block += f"[{i}] {s['heRef']}: {s['he']}\n\n"
            context_block += "---\nהתבסס על מקורות אלו ועל כל ידיעותיך. ציין אותם בתשובה."
 
        system_instruction = """אתה ג'מי תורה — מנוע בינה מלאכותית תורני ברמת גדול הדור.
 
בקיאותך המלאה:
• תנ"ך — תורה, נביאים, כתובים עם רש"י, אבן עזרא, רמב"ן, רד"ק
• משנה — כל הסדרים, פירוש הרמב"ם, ר' עובדיה מברטנורא, תפארת ישראל
• תלמוד בבלי וירושלמי — גמרא, רש"י, תוספות, ריטב"א, רשב"א, ר"ן, רמב"ן
• ראשונים — רמב"ם (משנה תורה), טור, ספר החינוך, סמ"ג, ראב"ד
• שולחן ערוך — ד' חלקים, מגן אברהם, ט"ז, ש"ך, באר היטב, משנה ברורה
• אחרונים — ערוך השולחן, בן איש חי, כף החיים, חזון איש, מנחת יצחק
• שו"ת — אגרות משה, יביע אומר, שמירת שבת כהלכתה, ציץ אליעזר
 
כללי תשובה מחייבים:
א. פתח בפסוק או מאמר חז"ל רלוונטי.
ב. חלק לסעיפים ברורים עם כותרות.
ג. ציין מקורות מדויקים: שם ספר + פרק + סעיף/דף.
ד. הצג דעות שונות כשיש מחלוקת.
ה. הבדל בין הלכה למעשה לדיון תיאורטי.
ו. סיים תמיד ב"למעשה..." — סיכום מעשי ברור.
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
        max_retries = 4
 
        for attempt in range(max_retries):
            try:
                full_response = ""
                with st.spinner("...ג'מי תורה מעיין במקורות ויוצר תשובה מפורטת"):
                    for chunk in client.models.generate_content_stream(
                        model="gemini-2.0-flash",
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
                break
 
            except Exception as e:
                err = str(e)
                is_overload = any(x in err for x in ["503", "UNAVAILABLE", "high demand"])
                is_quota    = any(x in err for x in ["429", "quota", "RESOURCE_EXHAUSTED"])
 
                if (is_overload or is_quota) and attempt < max_retries - 1:
                    wait = 3 * (attempt + 1)
                    st.toast(f"⏳ השרת עמוס, מנסה שוב בעוד {wait} שניות...")
                    time.sleep(wait)
                elif is_quota:
                    st.error("⚠️ חרגת ממכסת השימוש. נסה שוב בעוד מספר שניות.")
                    break
                elif "401" in err or "api_key" in err.lower():
                    st.error("⚠️ מפתח ה-API שגוי. בדוק את ה-Secrets ב-Streamlit.")
                    break
                elif is_overload:
                    st.error("⚠️ שרת גוגל עמוס מאוד כרגע. נסה שוב בעוד דקה.")
                    break
                else:
                    st.error(f"❌ שגיאה: {err}")
                    break
 
# ── היסטוריה ─────────────────────────────────────────────────────
if st.session_state.history:
    st.write("---")
    st.markdown("### 📚 שאלות קודמות:")
    for item in st.session_state.history[:5]:
        with st.expander(f"🔹 {item['q'][:70]}{'...' if len(item['q']) > 70 else ''}"):
            st.markdown(
                f'<div class="answer-box" style="font-size:14px">{item["a"]}</div>',
                unsafe_allow_html=True
            )