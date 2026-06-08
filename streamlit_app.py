import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# 1. הגדרות דף קבועות לכל האתר
st.set_page_config(
    page_title="ג'מי תורה", 
    page_icon="📜", 
    layout="wide"
)

# 2. חבילת עיצוב פרימיום (CSS) - תיקון הטבעת האדומה, יציבות הבועות ואנימציה חיה
st.markdown("""
    <style>
    /* כיוון טקסט גלובלי לימין */
    body, p, div, h1, h2, h3, h4, h5, h6, li, span, input, label, .stMarkdown, .stAlert {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    }
    
    /* מרכז את אזור העבודה בצורה נקייה */
    .block-container {
        max-width: 900px !important;
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        margin: 0 auto !important;
    }
    
    /* באנר כותרת עליון מעודכן */
    .chat-header {
        background: linear-gradient(135deg, #0f1d2a, #1a2e40);
        border: 1px solid #2c3e50;
        border-right: 5px solid #c5a059;
        padding: 30px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        margin-bottom: 30px;
        text-align: center !important;
    }
    .chat-header h1 {
        color: #f4edd8 !important;
        font-size: 2.4rem !important;
        font-weight: 700;
        margin: 0 0 8px 0 !important;
        text-align: center !important;
    }
    .chat-header p {
        color: #c5a059 !important;
        font-size: 1.15rem !important;
        margin: 0 !important;
        text-align: center !important;
    }
    
    /* תיקון והעלמת המסגרת האדומה בזמן לחיצה */
    div[data-baseweb="input"] {
        border: 2px solid #2c3e50 !important;
        border-radius: 25px !important;
        background-color: #141617 !important;
        transition: all 0.3s ease !important;
    }
    div[data-baseweb="input"]:focus-within {
        border-color: #c5a059 !important; /* הופך לזהב יוקרתי בלחיצה */
        box-shadow: 0 0 12px rgba(197, 160, 89, 0.4) !important;
    }
    .stTextInput input {
        color: #ffffff !important;
        font-size: 16.5px !important;
        padding: 12px 20px !important;
        background-color: transparent !important;
    }
    
    /* אזהרה קבועה ויחידה בתחתית */
    .disclaimer-fixed {
        text-align: center !important;
        color: #8a8a8a;
        font-size: 14px;
        margin-top: 12px;
    }
    
    /* אנימציית "נשימה" לאווטאר של הרב */
    @keyframes avatarPulse {
        0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(197, 160, 89, 0.4); }
        50% { transform: scale(1.04); box-shadow: 0 0 15px rgba(197, 160, 89, 0.7); }
        100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(197, 160, 89, 0.4); }
    }
    
    /* החלת האנימציה על תמונת הרב בצ'אט */
    img[alt="chat avatar"] {
        animation: avatarPulse 3s infinite ease-in-out !important;
        border: 2px solid #c5a059 !important;
        padding: 2px;
    }
    
    /* התאמת צבעי טקסט בתוך בועות הצ'אט */
    .stChatMessage {
        background-color: #141617 !important;
        border: 1px solid #2c3e50 !important;
        border-radius: 12px !important;
        margin-top: 15px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. הבאנר העליון - עודכן חזרה ל"ג'מי תורה"
st.markdown("""
    <div class="chat-header">
        <h1>📜 ג'מי תורה</h1>
        <p>תשובות ברורות, ישירות והלכה למעשה בגובה העיניים</p>
    </div>
    """, unsafe_allow_html=True)

# 4. שדה הזנת השאלה והאזהרה הקבועה
user_question = st.text_input("💬 מה השאלה שלך?")
st.markdown('<div class="disclaimer-fixed">לתשומת ליבך, הרב הדיגיטלי יכול לטעות ובמקרים של ספק או הלכות למעשה תמיד מומלץ לשאול רב.</div>', unsafe_allow_html=True)

st.write("---")

# 5. מנוע הפעלה ומענה חכם
if user_question:
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("⚠️ שגיאה: מפתח ה-API חסר בהגדרות המערכת.")
    else:
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            
            # הגדרות המערכת הפנימיות למודל
            rabbi_instructions = """אתה "הרב הדיגיטלי" הפועל בתוך מערכת "ג'מי תורה". תפקידך להשיב לשאלות הציבור בצורה הברורה, הפשוטה והישירה ביותר.
            חוקי ברזל:
            1. אתה רב אנושי, חם ומסביר פנים. אל תזכיר בשום אופן מילים כמו "בינה מלאכותית", "AI", "מודל" או "תוכנה".
            2. פתח תמיד בברכת שלום קצרה ומכובדת (למשל: "שלום וברכה").
            3. תן את השורה התחתונה (ההלכה למעשה או הברכה) מיד על ההתחלה, בצורה הכי ברורה וחדה שיש.
            4. תן הסבר קצר ופשוט בשפה ברורה, ללא מילים קשות בארמית או פלפולים מסובכים.
            5. ציין מקור בעברית פשוטה (למשל: "כך נפסק בשולחן ערוך").
            6. חתום בברכה קצרה ומכובדת."""
            
            model = genai.GenerativeModel(
                model_name='gemini-3-flash-preview',
                system_instruction=rabbi_instructions
            )
            
            disable_safety = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            
            with st.spinner("הרב מעיין במקורות ומנסח תשובה ברורה..."):
                response = model.generate_content(user_question, safety_settings=disable_safety)
                st.balloons()
                
                # השאלה של המשתמש
                with st.chat_message("user"):
                    st.write(f"**השאלה שלי:** {user_question}")
                
                # תמונת פרופיל של הרב שתקבל את אפקט התנועה מה-CSS
                rabbi_avatar_url = "https://cdn-icons-png.flaticon.com/512/3404/3404571.png"
                
                # תשובת הרב
                with st.chat_message("assistant", avatar=rabbi_avatar_url):
                    st.write(response.text)
                    
        except Exception as e:
            st.error(f"חלה שגיאה בתקשורת: {e}")