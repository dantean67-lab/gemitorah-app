import os
import base64
import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

st.set_page_config(
    page_title="ג'מי תורה - עוזר הלכה ובינה מלאכותית תורנית",
    page_icon="📜",
    layout="wide"
)

def get_base64_image(img_path):
    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

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
.example-label {
    color: #c5a059;
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 8px;
}
#MainMenu { visibility: hidden !important; }
footer { visibility: hidden !important; }
[data-testid="manage-app-button"] { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
.stDeployButton { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ── Header ──────────────────────────────────────────────────
rabbi_base64 = get_base64_image("rabbi.jpeg") or get_base64_image("rabbi.png")
if rabbi_base64:
    header_html = f"""
<div class="premium-header">
  <div class="header-text-container">
    <h1>ג'מי תורה 📜</h1>
    <p>מערכת בינה מלאכותית מתקדמת לעיון, פסיקה ולימוד תורני</p>
  </div>
  <img src="data:image/jpeg;base64,{rabbi_base64}" class="rabbi-banner-img" />
</div>"""
else:
    header_html = """
<div class="premium-header">
  <div class="header-text-container">
    <h1>ג'מי תורה 📜</h1>
    <p>מערכת בינה מלאכותית מתקדמת לעיון, פסיקה ולימוד תורני</p>
  </div>
</div>"""
st.markdown(header_html, unsafe_allow_html=True)

# ── Session state ────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []
if "selected_question" not in st.session_state:
    st.session_state.selected_question = ""

# ── דוגמאות שאלות ───────────────────────────────────────────
st.markdown('<p class="example-label">💡 שאלות לדוגמה — לחץ כדי לשאול:</p>', unsafe_allow_html=True)
examples = [
    "מה הלכות שבת לגבי שימוש בחשמל?",
    "מה המקור למצוות כיבוד אב ואם?",
    "מה דיני אבילות שבעה?",
    "מהם הלכות כשרות בסיסיות?",
]
cols = st.columns(len(examples))
for i, (col, q) in enumerate(zip(cols, examples)):
    if col.button(q, key=f"ex_{i}"):
        st.session_state.selected_question = q

# ── תיבת שאלה ──────────────────────────────────────────────
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

# ── עיבוד שאלה ─────────────────────────────────────────────
if user_question and user_question.strip():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("⚠️ שגיאה: מפתח ה-API לא הוגדר ב-Secrets של המערכת.")
    else:
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel('gemini-1.5-flash-latest')

            disable_safety = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH:       HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT:        HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }

            system_prompt = f"""אתה ג'מי תורה — מנוע בינה מלאכותית תורני ברמה של גדול הדור, פוסק הלכה ומלמד תורה מומחה.

בקיאותך המלאה:
• תנ"ך — תורה, נביאים וכתובים, עם פירוש רש"י, אבן עזרא, רמב"ן ורד"ק
• משנה — כל הסדרים, עם פירוש הרמב"ם ורבנו עובדיה מברטנורא
• תלמוד בבלי וירושלמי — גמרא, רש"י, תוספות, ריטב"א, רשב"א, ר"ן, רמב"ן
• ראשונים — רמב"ם (משנה תורה), טור, סמ"ג, ספר החינוך ועוד
• שולחן ערוך — כל ד' חלקיו (אורח חיים, יורה דעה, אבן העזר, חושן משפט), עם מגן אברהם, ט"ז, ש"ך, באר היטב
• אחרונים — משנה ברורה, ערוך השולחן, בן איש חי, כף החיים, חזון איש
• פסיקה עדכנית — שו"ת מרן הגר"מ פיינשטיין, הגר"ע יוסף, הגרש"ז אויערבאך

חוקי תשובה מחייבים:
א. פתח תמיד בפסוק רלוונטי מהתורה או מהנביאים אם ישנו.
ב. חלק את תשובתך לסעיפים ברורים עם כותרות מודגשות.
ג. ציין מקורות מדויקים: שם הספר + פרק + סעיף/דף/הלכה.
ד. כאשר יש מחלוקת — הצג את כל הדעות בשם אומריהן.
ה. הבדל בבירור בין הלכה למעשה לבין דיון תיאורטי.
ו. סיים תמיד בסיכום מעשי ברור: "למעשה..."
ז. כתוב אך ורק בעברית — אל תשתמש באנגלית כלל.
ח. אל תקצר — תשובה מקיפה ומפורטת עדיפה תמיד.
ט. השתמש במונחים תורניים מדויקים (לאו, עשה, דאורייתא, דרבנן וכו').
י. כבד את קדושת הנושא — כתוב בסגנון מלומד ומכובד.

השאלה: {user_question.strip()}"""

            st.markdown("### ✍️ תשובת ג'מי תורה:")
            answer_placeholder = st.empty()
            full_response = ""

            with st.spinner("...ג'מי תורה מעיין במקורות ויוצר תשובה מפורטת"):
                stream = model.generate_content(
                    system_prompt,
                    safety_settings=disable_safety,
                    stream=True
                )
                for chunk in stream:
                    if hasattr(chunk, "text") and chunk.text:
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

            # שמור בהיסטוריה
            st.session_state.history.insert(0, {
                "q": user_question.strip(),
                "a": full_response
            })
            st.session_state.selected_question = ""

        except Exception as e:
            err = str(e)
            if "quota" in err.lower() or "429" in err:
                st.error("⚠️ חרגת ממכסת השימוש החינמית. נסה שוב בעוד מספר שניות, או בדוק את מפתח ה-API שלך.")
            elif "api_key" in err.lower() or "401" in err:
                st.error("⚠️ מפתח ה-API שגוי. בדוק את ה-Secrets ב-Streamlit.")
            else:
                st.error(f"❌ שגיאה טכנית: {err}")

# ── היסטוריה ────────────────────────────────────────────────
if st.session_state.history:
    st.write("---")
    st.markdown("### 📚 שאלות קודמות:")
    for i, item in enumerate(st.session_state.history[:5]):
        with st.expander(f"🔹 {item['q'][:60]}{'...' if len(item['q']) > 60 else ''}"):
            st.markdown(
                f'<div class="answer-box" style="font-size:14px">{item["a"]}</div>',
                unsafe_allow_html=True
            )