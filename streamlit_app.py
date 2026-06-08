import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# 1. הגדרות דף - השם הרשמי שלך כפי שהוא בכתובת האתר
st.set_page_config(
    page_title="ג'מי תורה", 
    page_icon="📜", 
    layout="wide"
)

# 2. עיצוב CSS נקי - העלמת טבעות אדומות וסידור מרווחים (בלי רקע ירוק!)
st.markdown("""
    <style>
    /* כיוון טקסט גלובלי לימין */
    body, p, div, h1, h2, h3, h4, h5, h6, li, span, input, label, .stMarkdown {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    }
    
    /* מרכוז נקי של התוכן במסך */
    .block-container {
        max-width: 800px !important;
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        margin: 0 auto !important;
    }
    
    /* באנר עליון כהה ונקי התואם לעיצוב המקורי */
    .main-title-box {
        text-align: center !important;
        margin-bottom: 40px;
        padding: 20px;
    }
    .main-title-box h1 {
        font-size: 3rem !important;
        color: #ffffff !important;
        font-weight: 700;
        margin-bottom: 10px !important;
        text-align: center !important;
    }
    .main-title-box p {
        font-size: 1.3rem !important;
        color: #c5a059 !important;
        text-align: center !important;
    }
    
    /* 🔴 ביטול מוחלט של המסגרת האדומה/כתומה בזמן לחיצה על שדה הכתיבה */
    div[data-baseweb="base-input"], div[data-baseweb="input"] {
        border: 1px solid #2c3e50 !important;
        border-radius: 12px !important;
        background-color: #141617 !important;
        box-shadow: none !important;
    }
    div[data-baseweb="base-input"]:focus-within, div[data-baseweb="input"]:focus-within {
        border-color: #c5a059 !important;
        box-shadow: 0 0 8px rgba(197, 160, 89, 0.2) !important;
    }
    
    /* עיצוב משפט האזהרה הקבוע שלך בתחתית */
    .custom-disclaimer {
        text-align: center !important;
        color: #888888;
        font-size: 14px;
        margin-top: 12px;
        direction: rtl !important;
    }
    
    /* התאמת בועות הצ'אט הרשמיות שלא יחתכו */
    .stChatMessage {
        direction: rtl !important;
        background-color: #181b1c !important;
        border: 1px solid #2c3e50 !important;
        border-radius: 12px !important;
        padding: 15px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. כותרת האתר הרשמית (בלי תיבות צבעוניות)
st.markdown("""
    <div class="main-title-box">
        <h1>ג'מי תורה 📜</h1>
        <p>עוזר תורני דיגיטלי הלכתי וגמרא חכם</p>
    </div>
    """, unsafe_allow_html=True)

# 4. שדה הקלט והאזהרה המדויקת שביקשת (בלי שינויים ובלי סימני קריאה מיותרים)
user_question = st.text_input("שאל את ג'מי תורה כל שאלה בתורה, בהלכה ובגמרא:")
st.markdown('<div class="custom-disclaimer">לתשומת ליבך, הרב הדיגיטלי יכול לטעות ובמקרים של ספק או הלכות למעשה תמיד מומלץ לשאול רב.</div>', unsafe_allow_html=True)

st.write("---")

# 5. מנוע הפעלה ומענה באמצעות המודל היציב
if user_question:
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("⚠️ מפתח ה-API חסר בהגדרות המערכת.")
    else:
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            
            # שימוש במודל העדכני והרשמי למניעת שגיאות 404
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            disable_safety = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            
            system_prompt = f"""אתה "הרב הדיגיטלי" הפועל באתר "ג'מי תורה". תפקידך להשיב לשאלות בצורה הברורה והפשוטה ביותר.
            
            חוקים:
            1. פתח בברכת שלום מכובדת וקצרה ("שלום וברכה").
            2. תן את התשובה הישירה והברורה מיד בהתחלה.
            3. הסבר קצר בעברית פשוטה ללא מילים קשות בארמית.
            4. ציין מקור הלכתי או תורני ברור.
            5. חתום בברכה קצרה.
            
            השאלה: {user_question}"""
            
            with st.spinner("מנסח תשובה..."):
                response = model.generate_content(system_prompt, safety_settings=disable_safety)
                
                # בועת משתמש רשמית ויציבה
                with st.chat_message("user"):
                    st.write(f"**השאלה שלי:** {user_question}")
                
                # בועת הרב הרשמית - משתמשת באימוג'י קבוע של ספר תורה/רב שלא יכול להישבר או להיחתך במסך
                with st.chat_message("assistant", avatar="📜"):
                    st.write(response.text)
                    
        except Exception as e:
            st.error(f"חלה שגיאה: {e}")