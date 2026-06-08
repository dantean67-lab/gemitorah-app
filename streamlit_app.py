import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import os

# הגדרות דף 
st.set_page_config(
    page_title="ג'מי תורה - עוזר הלכה ובינה מלאכותית תורנית", 
    page_icon="📜", 
    layout="centered"
)

# עיצוב האתר שלא יהיה לבן על לבן
st.markdown("""
    <style>
    body, p, div, h1, h2, h3, h4, h5, h6, li, span, input, label, .stMarkdown, .stAlert {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .main-title {
        background: linear-gradient(135deg, #1e3f20, #2d5a27);
        color: #f1e4c3 !important;
        padding: 20px;
        border-radius: 15px;
        text-align: center !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        margin-bottom: 20px;
    }
    .main-title h1, .main-title h3 {
        text-align: center !important;
        color: #f1e4c3 !important;
    }
    .stTextInput > div > div > input {
        direction: rtl !important;
        text-align: right !important;
        border: 2px solid #2d5a27 !important;
        border-radius: 12px !important;
        padding: 10px !important;
        font-size: 16px !important;
        background-color: #ffffff !important;
        color: #111111 !important;
    }
    div[data-testid="stAlert"] {
        border-radius: 12px !important;
        border-right: 5px solid #2d5a27 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# כותרת האתר
st.markdown("""
    <div class="main-title">
        <h1>📜 ג'מי תורה</h1>
        <h3>עוזר תורני דיגיטלי והלכתי חכם</h3>
    </div>
    """, unsafe_allow_html=True)

# תיבת השאלה
user_question = st.text_input("🔮 שאל את ג'מי תורה כל שאלה:")
st.caption("💡 נושאים מהירים בלי מפתח: שבת, נטילת ידיים, ציצית, תפילין, כשרות, ברכות, מזוזה, לשון הרע.")

# בדיקה אם קובץ הספר שיצרת מצד שמאל קיים
BOOK_FILE = "kitzur_shulchan_aruch.txt"
if os.path.exists(BOOK_FILE):
    st.info("📚 ספר 'קיצור שולחן ערוך' מחובר בהצלחה לבוט ומגן מפני חרטוטים!")
else:
    st.warning("⚠️ קובץ קיצור שולחן ערוך לא נמצא ברשימה מצד שמאל.")

st.write("---")

# תיבת מפתח אופציונלית
with st.expander("🔑 חיבור למוח המלא של גוגל (אופציונלי - לשאלות מורכבות, תנ\"ך וגמרא)"):
    st.write("להדבקת מפתח API חינמי מחשבון גוגל:")
    api_key = st.text_input("הדבק כאן את מפתח ה-API שלך:", type="password")
    st.markdown("[לחץ כאן לקבלת מפתח בחינם מגוגל](https://aistudio.google.com/)")

# מאגר מידע מהיר בלי מפתח (עם תשובות ארוכות ומפורטות יותר)
KNOWLEDGE_BASE = {
    "נטילת ידיים": """**הלכות נטילת ידיים בבוקר (מפורט):**
* **למה נוטלים?** להעביר רוח רעה ששורה על הידיים בלילה, וכדי להתקדש לקראת תפילת הבוקר.
* **הסדר:** נוטלים כלי עם מים ביד ימין, מעבירים לשמאל, ושופכים קודם על יד ימין. לאחר מכן שופכים על שמאל. חוזרים על כך 3 פעמים לסירוגין.
* **הברכה:** לאחר הנטילה, משפשפים את הידיים, מגביהים אותן ומברכים: *"על נטילת ידיים"* ומנגבים היטב.""",

    "שבת": """**הלכות שבת (מפורט):**
* **כניסת שבת:** יש להדליק נרות שבת כ-20 דקות לפני שקיעת החמה.
* **איסור מלאכה:** התורה אסרה 39 אבות מלאכה בשבת (ל"ט מלאכות). ביניהן: הדלקת אש, בישול, כתיבה, ושימוש במכשירי חשמל.
* **קידוש:** מצווה מהתורה לקדש את השבת על כוס יין בליל שבת לפני הסעודה ובבוקר השבת.""",

    "כשרות": """**הלכות כשרות בשר וחלב (מפורט):**
* **האיסור:** אסור לבשל בשר וחלב יחד, לאכול אותם יחד, או ליהנות מהם.
* **המתנה:** לאחר אכילת בשר, יש להמתין 6 שעות מלאות לפני אכילת מאכלי חלב.
* **כלים:** חובה לשמור על הפרדה מוחלטת במטבח: סירים וסכו"ם נפרדים לבשר ולחלב."""
}

if user_question:
    user_question_lower = user_question.lower()
    found_local = False
    
    for key, response in KNOWLEDGE_BASE.items():
        if key in user_question_lower or (key == "נטילת ידיים" and "ידיים" in user_question_lower) or (key == "כשרות" and ("בשר" in user_question_lower or "חלב" in user_question_lower)):
            st.balloons()
            st.success("**תשובת ג'מי תורה (מאגר מקומי מפורט):**")
            st.markdown(response)
            found_local = True
            break
            
    if not found_local:
        if 'api_key' not in locals() or not api_key:
            st.warning("⚠️ הנושא הזה לא במאגר החינמי. שים מפתח API בלשונית למעלה בשביל לתת לבוט לקרוא מהספר שהעלית.")
        else:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                disable_safety = {
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
                
                # קריאת תוכן הספר שהעלית מצד שמאל
                book_context = ""
                if os.path.exists(BOOK_FILE):
                    with open(BOOK_FILE, "r", encoding="utf-8") as f:
                        book_context = f.read()
                
                system_prompt = "אתה עוזר תורני בשם ג'מי תורה.\n"
                if book_context:
                    system_prompt += f"חובה קשיחה: ענה אך ורק על פי ספר הקיצור שולחן ערוך המצורף כאן. אם זה לא שם, תגיד שזה לא רשום בספר ואל תמציא כלום מהראש: \n{book_context}\n"
                
                system_prompt += f"השאלה: {user_question}"
                
                with st.spinner("ג'מי תורה מעיין בקובץ שהעלית..."):
                    response = model.generate_content(system_prompt, safety_settings=disable_safety)
                    st.balloons()
                    st.success("**תשובת ג'מי תורה (מתוך הספר שהעלית):**")
                    st.write(response.text)
                    
            except Exception as e:
                st.error(f"שגיאה: {e}")