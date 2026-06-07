import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# 1. הגדרת העמוד
st.set_page_config(page_title="ג'מיתורה והלכה", page_icon="📜", layout="centered")

# 2. עיצוב לעברית (RTL) ותיבות טקסט נקיות
st.markdown("""
    <style>
    body, p, div, h1, h2, h3, h4, h5, h6, li, span, input, label, .stMarkdown, .stAlert {
        direction: rtl !important;
        text-align: right !important;
    }
    .stTextInput > div > div > input {
        direction: rtl !important;
        text-align: right !important;
        border: 2px solid #4CAF50;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. כותרות האתר
st.title("📜 ג'מיתורה והלכה")
st.subheader("גרסת ה-Pro ההיברידית: חכם, מהיר ומחובר")
st.write("---")

# 4. תיבת מפתח ה-API (אופציונלית למתקדמים!)
api_key = st.text_input("🔑 מפתח API לגישה לכל הידע בעולם (אופציונלי לבסיס):", type="password")
st.markdown("[קישור לקבלת מפתח בחינם מגוגל](https://aistudio.google.com/)")
st.write("---")

# 5. תיבת השאלה של המשתמש
user_question = st.text_input("🔮 שאל את ג'מיתורה כל שאלה שקיימת בעולם:")

# 6. מאגר המידע המקומי (לדברים הבסיסיים - עובד תמיד בלי מפתח!)
KNOWLEDGE_BASE = {
    "נטילת ידיים": """**הלכות נטילת ידיים בבוקר:**
1. מיד כשקמים מהשינה, יש ליטול ידיים 3 פעמים לסירוגין על כל יד.
2. המים צריכים להגיע עד פרק כף היד (שורש היד).
3. **אופן הברכה:** לאחר הנטילה והניגוב, מגביהים את הידיים למעלה כנגד הפנים או הראש, ומברכים על נטילת ידיים.""",

    "ציצית": """**הלכות ציצית:**
1. מצוות עשה מן התורה לשים ציצית בכל בגד שיש לו ארבע כנפות שמתכסים בו.
2. זמן מצוות ציצית הוא ביום ולא בלילה.
3. על טלית קטן מברכים: 'על מצוות ציצית'.""",

    "תפילין": """**הלכות תפילין:**
1. מצווה שיש להניח בכל יום חול (לא בשבת וימים טובים).
2. סדר ההנחה: מניחים קודם תפילין של יד על הזרוע, מברכים 'להניח תפילין' ומהדקים. לאחר מכן מניחים תפילין של ראש מעל המצח באמצע.
3. אסור להסיח את הדעת מהתפילין כל זמן שהן עליך.""",

    "ברכות": """**הלכות ברכות:**
1. מודה אני: אומרים מיד כשמתעוררים בבוקר.
2. ברכות הנהנין: על לחם מברכים 'המוציא', על מאפים 'מזונות', על פירות העץ 'בורא פרי העץ', על ירקות 'בורא פרי האדמה', ועל מים/משקאות 'שהכל נהיה בדברו'.""",

    "שבת": """**הלכות שבת:**
1. יש להימנע מעשיית 39 מלאכות אסורות מהתורה (כמו הבערת אש, בישול, כתיבה ועוד - אלו נקראות ל"ט מלאכות).
2. הדלקת נרות: חובה להדליק נרות לכבוד שבת לפני שקיעת החמה.
3. קידוש: מצווה מהתורה לקדש את השבת על כוס יין בכניסתה (בליל שבת) וביציאתה (בהבדלה).""",

    "מזוזה": """**הלכות מזוזה:**
1. מצוות עשה לקבוע מזוזה בכל פתחי הבית והחדרים המשמשים למגורים.
2. קובעים את המזוזה בשליש העליון של גובה הפתח, מצד ימין של הנכנס.
3. יש לבדוק את כשרות המזוזות אצל סופר סת"ם פעמיים ב-7 שנים.""",

    "כשרות": """**הלכות בשר וחלב:**
1. אסור לבשל, לאכול או ליהנות מתערובת של בשר וחלב יחד.
2. המתנה: לאחר אכילת בשר, יש להמתין 6 שעות מלאות לפני שאוכלים מאכלי חלב.
3. יש להקפיד על מערכות כלים וכיורים נפרדים לחלוטין לבשר ולחלב.""",

    "לשון הרע": """**הלכות שמירת הלשון:**
1. איסור חמור מן התורה לספר בגנותו של חברו, אפילו אם הדברים הם אמת גמורה.
2. אסור לקבל או להאמין ללשון הרע שנאמר על ידי אחרים.
3. אסור לרגל או ללכת רכיל (איסור 'לא תלך רכיל בעמיך')."""
}

# 7. מנוע החיפוש וההפעלה
if user_question:
    user_question_lower = user_question.lower()
    found_local = False
    
    # שלב א': בדיקה במאגר הבסיסי
    for key, response in KNOWLEDGE_BASE.items():
        if key in user_question_lower or (key == "נטילת ידיים" and ("ידיים" in user_question_lower or "בוקר" in user_question_lower or "נטיל" in user_question_lower)) or (key == "כשרות" and ("בשר" in user_question_lower or "חלב" in user_question_lower or "אוכל" in user_question_lower)) or (key == "ברכות" and ("ברכ" in user_question_lower or "אוכלים" in user_question_lower or "לברך" in user_question_lower)):
            st.balloons()
            st.success("**תשובת ג'מיתורה (מתוך המאגר המהיר):**")
            st.markdown(response)
            found_local = True
            break
            
    # שלב ב': אם הנושא לא בסיסי, עוברים לבינה המלאכותית של גוגל
    if not found_local:
        if not api_key:
            st.warning("⚠️ שאלת שאלה מורכבת! הנושא הזה לא נמצא במאגר הבסיסי שלי. כדי לפתוח את המוח המלא של ג'מיתורה שיודע הכל מכל כל, אנא הדבק את מפתח ה-API בתיבה למעלה.")
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
                
                system_prompt = f"אתה עוזר תורני גאון בשם ג'מיתורה. ענה בעברית עם מקורות מדויקים על השאלה: {user_question}"
                
                with st.spinner("ג'מיתורה מעיין בכל הספרים שבעולם..."):
                    response = model.generate_content(system_prompt, safety_settings=disable_safety)
                    st.balloons()
                    st.success("**תשובת ג'מיתורה (בינה מלאכותית):**")
                    st.write(response.text)
                    
            except Exception as e:
                st.error(f"שגיאה בהפעלת ה-AI: {e}")