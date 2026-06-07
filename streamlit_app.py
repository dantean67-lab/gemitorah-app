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

# 5. הרחבה אופציונלית בצד/למטה - תיקון הזחה קריטי כאן!
with st.expander("🔑 חיבור למוח המלא של גוגל (אופציונלי - לשאלות מורכבות, תנ\"ך וגמרא)"):
    st.write("כדי לשאול שאלות מורכבות מעבר למאגר הבסיסי, יש להדביק מפתח API חינמי מחשבון גוגל של מבוגר.")
    api_key = st.text_input("הדבק כאן את מפתח ה-API שלך:", type="password")
    st.markdown("[לחץ כאן לקבלת מפתח בחינם מגוגל](https://aistudio.google.com/)")

# 6. מאגר המידע המקומי
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
3. יש לבדוק את כשרות המזוזות אצל סופר סת"ם פעמיים ב-