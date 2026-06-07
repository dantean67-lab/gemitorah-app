import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# 1. הגדרות דף ומטא-דאטה בשביל גוגל (SEO)
st.set_page_config(
    page_title="ג'מי תורה - עוזר הלכה ובינה מלאכותית תורנית", 
    page_icon="📜", 
    layout="centered"
)

# 2. עיצוב פרימיום ותיקון צבע הפונט בתיבות הטקסט
st.markdown("""
    <style>
    /* יישור כללי לימין */
    body, p, div, h1, h2, h3, h4, h5, h6, li, span, input, label, .stMarkdown, .stAlert {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* כותרת ראשית מעוצבת */
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
    
    /* תיקון קריטי: רקע לבן וכתב שחור ברור שלא נעלם */
    .stTextInput > div > div > input {
        direction: rtl !important;
        text-align: right !important;
        border: 2px solid #2d5a27 !important;
        border-radius: 12px !important;
        padding: 10px !important;
        font-size: 16px !important;
        background-color: #ffffff !important;
        color: #111111 !important; /* מונע כתב לבן על רקע לבן */
    }
    
    /* עיצוב תיבות התשובה */
    div[data-testid="stAlert"] {
        border-radius: 12px !important;
        border-right: 5px solid #2d5a27 !important;
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

# 4. תיבת השאלה (הכתב כאן עכשיו שחור וקריא במאה אחוז)
user_question = st.text_input("🔮 שאל את ג'מי תורה כל שאלה:")

# כתובית הסבר נקייה ומקצועית במקום התיבה המציקה עם המנורה
st.caption("💡 נושאים הזמינים מיד בלי מפתח: שבת, נטילת ידיים, ציצית, תפילין, כשרות, ברכות, מזוזה, לשון הרע.")

st.write("---")

# 5. לשונית מפתח ה-API (סגורה כברירת מחדל, למי שרוצה להרחיב לתנ\"ך וגמרא)
with st.expander("🔑 חיבור למוח המלא של גוגל (אופציונלי - לשאלות מורכבות, תנ\"ך וגמרא)"):
    st.write("כדי לשאול שאלות מורכבות מעבר למאגר הבסיסי, יש להדביק מפתח API חינמי מחשבון גוגל של מבוגר.")
    api_key = st.text_input("הדבק כאן את מפתח ה-API שלך:", type="password")
    st.markdown("[לחץ כאן לקבלת מפתח בחינם מגוגל](https://aistudio.google.com/)")

# 6. מאגר המידע המקומי
KNOWLEDGE_BASE = {
    "נטילת ידיים": "מיד כשקמים מהשינה, יש ליטול ידיים 3翻 לסירוגין על כל יד. המים צריכים להגיע עד פרק כף היד. לאחר הנטילה והניגוב מברכים 'על נטילת ידיים'.",
    "ציצית": "מצוות עשה מן התורה לשים ציצית בכל בגד שיש לו ארבע כנפות שמתכסים בו. זמן מצוות ציצית הוא ביום ולא בלילה. על טלית קטן מברכים: 'על מצוות ציצית'.",
    "תפילין": "מצווה שיש להניח בכל יום חול (לא בשבת וימים טובים). מניחים קודם תפילין של יד על הזרוע, מברכים 'להניח תפילין' ומהדקים, ואז מניחים תפילין של ראש מעל המצח.",
    "ברכות": "אומרים 'מודה אני' מיד כשמתעוררים. ברכות הנהנין: על לחם מברכים 'המוציא', על מאפים 'מזונות', על פירות העץ 'העץ', על ירקות 'האדמה', ועל משקאות 'שהכל'.",
    "שבת": "יש להימנע מעשיית 39 מלאכות אסורות מהתורה. חובה להדליק נרות לכבוד שבת לפני שקיעת החמה, ומצווה לקדש על כוס יין בכניסת השבת ובצאתה.",
    "מזוזה": "מצוות עשה לקבוע מזוזה בכל פתחי הבית והחדרים המשמשים למגורים. קובעים אותה בשליש העליון של גובה הפתח מצד ימין של הנכנס. יש לבדוק את כשרותה פעמיים ב-7 שנים.",
    "כשרות": "אסור לבשל, לאכול או ליהנות מתערובת של בשר וחלב יחד. לאחר אכילת בשר, יש להמתין 6 שעות מלאות לפני שאוכלים מאכלי חלב, ולהקפיד על מערכות כלים נפרדות.",
    "לשון הרע": "איסור חמור מן התורה לספר בגנותו של חברו, אפילו אם הדברים הם אמת גמורה. אס