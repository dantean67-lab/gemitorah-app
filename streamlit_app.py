import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import os

# 1. הגדרות דף - יציב וממורכז
st.set_page_config(
    page_title="ג'מי תורה", 
    page_icon="📜", 
    layout="centered"
)

# 2. עיצוב CSS יוקרתי (זהב וכהה, בלי מסגרות אדומות ובלי חיתוכים)
st.markdown("""
    <style>
    /* כיוון כתיבה מימין לשמאל */
    * {
        direction: rtl;
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    }
    
    /* קופסת כותרת נקייה ומדויקת בדיוק כמו שאהבת */
    .rabbi-header {
        text-align: center;
        padding: 2.5rem 1.5rem;
        background: linear-gradient(180deg, #111b24 0%, #0e1117 100%);
        border: 1px solid #233342;
        border-bottom: 3px solid #c5a059;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    .rabbi-header h1 {
        color: #ffffff !important;
        font-size: 3rem !important;
        font-weight: 800;
        margin: 0 !important;
    }
    .rabbi-header p {
        color: #c5a059 !important;
        font-size: 1.25rem !important;
        margin-top: 8px !important;
        opacity: 0.9;
    }
    
    /* 🔴 העלמה מוחלטת של המסגרת האדומה/כתומה בזמן פוקוס */
    div[data-baseweb="base-input"], div[data-baseweb="input"] {
        border: 1px solid #2c3e50 !important;
        background-color: #141617 !important;
        border-radius: 30px !important; /* תיבה מעוגלת ויפה */
        box-shadow: none !important;
        padding-right: 15px;
    }
    div[data-baseweb="base-input"]:focus-within, div[data-baseweb="input"]:focus-within {
        border-color: #c5a059 !important;
        box-shadow: 0 0 10px rgba(197, 160, 89, 0.25) !important;
    }
    
    /* כיתוב אזהרה קטן ואיכותי בתחתית */
    .disclaimer-text {
        text-align: center;
        color: #888888;
        font-size: 0.88rem;
        margin-top: 12px;
        font-weight: 400;
    }
    
    /* התאמת בועות הצ'אט שלא יחתכו בשוליים */
    .stChatMessage {
        background-color: #181b1c !important;
        border: 1px solid #25292b !important;
        border-radius: 15px !important;
        padding: 1rem !important;
        margin-top: 15px !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. הצגת הכותרת המעוצבת (בדיוק כמו בתמונה הרשמית שלך)
st.markdown("""
    <div class="rabbi-header">
        <h1>הרב הדיגיטלי 📜</h1>
        <p>תשובות ברורות, ישירות והלכה למעשה</p>
    </div>
""", unsafe_allow_html=True)

# 4. שדה הקלט והאזהרה המדויקת שלך
user_question = st.text_input("מה השאלה שלך? 💬")
st.markdown('<div class="disclaimer-text">⚠️ לתשומת ליבך, הרב הדיגיטלי יכול לטעות ובמקרים של ספק או הלכות למעשה תמיד מומלץ לשאול רב.</div>', unsafe_allow_html=True)

st.write("---")

# 5. מנגנון מענה חכם ויציב
if user_question:
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("⚠️ מפתח ה-API חסר בהגדרות ה-Secrets של Streamlit.")
    else:
        try:
            # הגדרת המפתח
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            
            # שימוש במודל הרשמי עם הגנה משגיאות ספציפיות
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            disable_safety = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            
            system_prompt = f"""אתה "הרב הדיגיטלי". השב על השאלה הבאה בצורה הברורה, הפשוטה והישירה ביותר.
            חוקים: פתח בברכת שלום קצרה, תן את התשובה והשורה התחתונה מיד בהתחלה, הסבר קצר בעברית פשוטה, ציין מקור ברור וסיים בברכה.
            השאלה: {user_question}"""
            
            with st.spinner("הרב מעיין במקורות ומנסח תשובה..."):
                response = model.generate_content(system_prompt, safety_settings=disable_safety)
                
                # מציג את השאלה שלך
                with st.chat_message("user"):
                    st.write(f"**השאלה שלי:** {user_question}")
                
                # 🛡️ בדיקה חכמה: אם הקובץ rabbi.jpeg קיים, נשתמש בו. אם לא, נשים אימוג'י יפה כדי שלא יישבר!
                if os.path.exists("rabbi.jpeg"):
                    rabbi_avatar = "rabbi.jpeg"
                else:
                    rabbi_avatar = "📜" 
                
                # מציג את תשובת הרב עם האווטאר המדויק
                with st.chat_message("assistant", avatar=rabbi_avatar):
                    st.write(response.text)
                    
        except Exception as e:
            st.error(f"חלה שגיאה בתקשורת עם השרת: {e}")
            st.info("💡 טיפ פרו: אם מופיעה שגיאת 'Model not found', ודא שקובץ requirements.txt שלך מכיל את השורה: google-generativeai>=0.5.4")