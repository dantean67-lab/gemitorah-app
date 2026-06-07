import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# 1. הגדרות דף ומטא-דאטה בשביל גוגל (SEO)
st.set_page_config(
    page_title="ג'מי תורה - עוזר הלכה ובינה מלאכותית תורנית", 
    page_icon="📜", 
    layout="centered"
)

# 2. עיצוב פרימיום (צבעי ירוק תורני, זהב, צללים ורדיוסים מודרניים)
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
        padding: 25px;
        border-radius: 15px;
        text-align: center !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        margin-bottom: 25px;
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
        padding: 12px !important;
        font-size: 16px !important;
        background-color: #fafafa !important;
        box-shadow: inset 0 1px 3px rgba(0,0,0,0.1) !important;
    }
    
    div[data-testid="stAlert"] {
        border-radius: 12px !important;
        border-right: 5px solid #2d5a27 !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05) !important;
    }
    
    .seo-tags {
        display: none;
    }
    
    /* עיצוב מיוחד לתיבת ההסבר על ה-API */
    .api-explanation {
        background-color: #f9f6f0;
        border-right: 4px solid #d4af37;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
        font-size: 14px;
        line-height: 1.5;
    }
    </style>
    
    <div class="seo-tags">
        ג'מי תורה, ג'מיתורה, גמי תורה, גמיתורה, gemitorah, gemi torah, תנך, הלכה, שולחן ערוך
    </div>
    """, unsafe_allow_html=True)

# 3. באנר כותרת מעוצב
st.markdown("""
    <div class="main-title">
        <h1>📜 ג'מי תורה</h1>
        <h3>עוזר תורני דיגיטלי והלכתי חכם</h3>
    </div>
    """, unsafe_allow_html=True)

st.write("---")

# 4. הסבר על מפתח ה-API ותיבת הקלט
st.markdown("### 🔑 שלב א': חיבור למוח המלא של ג'מי תורה")

# תיבת ההסבר החדשה בשביל המשתמשים שלך!
st.markdown("""
<div class="api-explanation">
    <strong>מה זה מפתח API (API Key)?</strong><br>
    בלי המפתח, ג'מי תורה פועל על מאגר עצמאי ומכיר רק הלכות בסיסיות (כמו שבת, כשרות, ציצית ותפילין). <br>
    כדי לשאול שאלות מורכבות יותר, לחפש פסוקים בתנ"ך או לבקש מקורות מכל הספרים שבעולם, האתר צריך להתחבר למוח של גוגל (Gemini AI). <br>
    המפתח הוא קוד סודי וחינמי שמקשר בין האתר לבינה המלאכותית ומאפשר לו לדעת הכל מכל כל.
</div>
""", unsafe_allow_html=True)

api_key = st.text_input("הדבק כאן את מפתח ה-API שלך (אופציונלי לשאלות בסיס):", type="password")
st.markdown("[לחץ כאן לקבלת מפתח בחינם מגוגל (בחשבון מבוגר)](https://aistudio.google.com/)")
st.write("---")

# 5. תיבת השאלה של המשתמש
st.markdown("### 🔮 שלב ב': שאל שאלה")
user_question = st.text_input("מה תרצה לשאול את ג'מי תורה היום?")

# 6. מאגר המידע המקומי (לדברים הבסיסיים)
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

if user_question:
    user_question_lower = user_question.lower()
    found_local = False
    
    for key, response in KNOWLEDGE_BASE.items():
        if key in user_question_lower or (key == "נטילת ידיים" and ("ידיים" in user_question_lower or "בוקר" in user_question_lower or "נטיל" in user_question_lower)) or (key == "כשרות" and ("בשר" in user_question_lower or "חלב" in user_question_lower or "אוכל" in user_question_lower)) or (key == "ברכות" and ("ברכ" in user_question_lower or "אוכלים" in user_question_lower or "לברך" in user_question_lower)):
            st.balloons()
            st.success("**תשובת ג'מי תורה:**")
            st.markdown(response)
            found_local = True
            break
            
    if not found_local:
        if not api_key:
            st.warning("⚠️ שאלת שאלה מורכבת! הנושא הזה לא נמצא במאגר הבסיסי שלי. כדי לפתוח את המוח המלא של ג'מי תורה שיודע הכל מכל כל, אנא הדבק את מפתח ה-API בתיבה למעלה.")
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
                
                system_prompt = f"אתה עוזר תורני גאון בשם ג'מי תורה. ענה בעברית עם מקורות מדויקים על השאלה: {user_question}"
                
                with st.spinner("ג'מי תורה מעיין בכל הספרים שבעולם..."):
                    response = model.generate_content(system_prompt, safety_settings=disable_safety)
                    st.balloons()
                    st.success("**תשובת ג'מי תורה (בינה מלאכותית):**")
                    st.write(response.text)
                    
            except Exception as e:
                st.error(f"שגיאה בהפעלת ה-AI: {e}")