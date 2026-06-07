import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# 1. הגדרות דף ומטא-דאטה בשביל גוגל (SEO)
st.set_page_config(
    page_title="ג'מי תורה - עוזר הלכה ובינה מלאכותית תורנית", 
    page_icon="📜", 
    layout="centered"
)

# 2. עיצוב פרימיום (יישור לימין, תיבת מפתח מעוצבת וקטנה)
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
        background-color: #fafafa !important;
    }
    
    div[data-testid="stAlert"] {
        border-radius: 12px !important;
        border-right: 5px solid #2d5a27 !important;
    }
    
    .examples-box {
        background-color: #f4f7f4;
        border: 1px dashed #2d5a27;
        padding: 12px;
        border-radius: 10px;
        margin-top: 5px;
        font-size: 14px;
    }
    
    .seo-tags {
        display: none;
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

# 4. הדבר הראשי: תיבת השאלה של המשתמש
user_question = st.text_input("🔮 שאל את ג'מי תורה כל שאלה:")

st.markdown("""
<div class="examples-box">
    💡 <strong>אפשר לשאול מיד (בלי מפתח):</strong> הלכות שבת, נטילת ידיים, ציצית, תפילין, כשרות (בשר וחלב), ברכות, מזוזה, לשון הרע.
</div>
""", unsafe_allow_html=True)

st.write("---")

# 5. הרחבה אופציונלית בצד/למטה
with st.expander("🔑 חיבור למוח המלא של גוגל (אופציונלי - לשאלות מורכבות, תנ\"ך וגמרא)"):
    st.write("כדי לשאול שאלות מורכבות מעבר למאגר הבסיסי, יש להדביק מפתח API חינמי מחשבון גוגל של מבוגר.")
    api_key = st.text_input("הדבק כאן את מפתח ה-API שלך:", type="password")
    st.markdown("[לחץ כאן לקבלת מפתח בחינם מגוגל](https://aistudio.google.com/)")

# 6. מאגר המידע המקומי - מיושר ומסודר בלי רווחים שבורים
KNOWLEDGE_BASE = {
    "נטילת ידיים": "מיד כשקמים מהשינה, יש ליטול ידיים 3 פעמים לסירוגין על כל יד. המים צריכים להגיע עד פרק כף היד. לאחר הנטילה והניגוב מברכים 'על נטילת ידיים'.",
    "ציצית": "מצוות עשה מן התורה לשים ציצית בכל בגד שיש לו ארבע כנפות שמתכסים בו. זמן מצוות ציצית הוא ביום ולא בלילה. על טלית קטן מברכים: 'על מצוות ציצית'.",
    "תפילין": "מצווה שיש להניח בכל יום חול (לא בשבת וימים טובים). מניחים קודם תפילין של יד על הזרוע, מברכים 'להניח תפילין' ומהדקים, ואז מניחים תפילין של ראש מעל המצח.",
    "ברכות": "אומרים 'מודה אני' מיד כשמתעוררים. ברכות הנהנין: על לחם מברכים 'המוציא', על מאפים 'מזונות', על פירות העץ 'העץ', על ירקות 'האדמה', ועל משקאות 'שהכל'.",
    "שבת": "יש להימנע מעשיית 39 מלאכות אסורות מהתורה. חובה להדליק נרות לכבוד שבת לפני שקיעת החמה, ומצווה לקדש על כוס יין בכניסת השבת ובצאתה.",
    "מזוזה": "מצוות עשה לקבוע מזוזה בכל פתחי הבית והחדרים המשמשים למגורים. קובעים אותה בשליש העליון של גובה הפתח מצד ימין של הנכנס. יש לבדוק את כשרותה פעמיים ב-7 שנים.",
    "כשרות": "אסור לבשל, לאכול או ליהנות מתערובת של בשר וחלב יחד. לאחר אכילת בשר, יש להמתין 6 שעות מלאות לפני שאוכלים מאכלי חלב, ולהקפיד על מערכות כלים נפרדות.",
    "לשון הרע": "איסור חמור מן התורה לספר בגנותו של חברו, אפילו אם הדברים הם אמת גמורה. אסור לקבל או להאמין ללשון הרע שנאמר על ידי אחרים."
}

# 7. מנוע החיפוש וההפעלה
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
        if 'api_key' not in locals() or not api_key:
            st.warning("⚠️ שאלת שאלה מורכבת! הנושא הזה לא נמצא במאגר הבסיסי שלי. כדי לפתוח את המוח המלא של ג'מי תורה שיודע הכל, פתח את הלשונית למטה והדבק מפתח API.")
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