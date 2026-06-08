import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# 1. הגדרות דף
st.set_page_config(
    page_title="ג'מי תורה - עוזר הלכה ובינה מלאכותית תורנית", 
    page_icon="📜", 
    layout="centered"
)

# 2. עיצוב האתר (יישור לימין וצבעים יפים)
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
    .disclaimer-text {
        text-align: center !important;
        color: #888888;
        font-size: 13px;
        margin-top: 30px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. באנר כותרת
st.markdown("""
    <div class="main-title">
        <h1>📜 ג'מי תורה</h1>
        <h3>עוזר תורני דיגיטלי הלכתי וגמרא חכם</h3>
    </div>
    """, unsafe_allow_html=True)

# 4. תיבת השאלה
user_question = st.text_input("🔮 שאל את ג'מי תורה כל שאלה בתורה, בהלכה, בקיצור שולחן ערוך ובגמרא:")

# הוספת הכתב הקטן של האזהרה ישר מתחת לתיבת השאלה
st.markdown('<div class="disclaimer-text">⚠️ ג\'מי תורה עלול לטעות, לכן תמיד מומלץ לבדוק אותו או לשאול רב בעניינים חשובים ולהלכה למעשה.</div>', unsafe_allow_html=True)

st.write("---")

# 5. הפעלת מנוע הבינה המלאכותית באמצעות המפתח המוחבא ב-Secrets
if user_question:
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("⚠️ שגיאה: המפתח לא נקרא בהצלחה מה-Secrets. ודא שלחצת Save changes באתר של Streamlit.")
    else:
        try:
            # חיבור אוטומטי למפתח הסודי
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            
            # עדכון שם המודל לגרסה החדשה והנתמכת (gemini-1.5-flash-latest)
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            
            disable_safety = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            
            # הנחיה לבוט שיהיה תלמיד חכם עצום
            system_prompt = f"""אתה פוסק הלכה ועוזר תורני גאון ובקיא עצום בשם ג'מי תורה.
            תפקידך לענות על שאלות בצורה המפורטת והעשירה ביותר (לא בקצרה!).
            יש לך ידע מוחלט בכל התנ"ך, המשנה, הגמרא (בבלי וירושלמי), השולחן ערוך, וקיצור שולחן ערוך.
            
            חוקים נוקשים:
            1. ענה תמיד בעברית ברורה, מכובדת ומדויקת.
            2. חלק את התשובה לסעיפים או נקודות כדי שתהיה קריאה וברורה.
            3. ציין מקורות מדויקים ככל הניתן (מסכת, דף, סימן, סעיף).
            4. אל תחרטט ואל תמציא שום דבר מהראש.
            
            השאלה של הלומד: {user_question}"""
            
            with st.spinner("ג'מי תורה מעיין במקורות..."):
                response = model.generate_content(system_prompt, safety_settings=disable_safety)
                st.balloons()
                st.success("**תשובת ג'מי תורה המפורטת:**")
                st.write(response.text)
                
        except Exception as e:
            st.error(f"חלה שגיאה בתקשורת עם מנוע ה-AI: {e}")