import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# 1. הגדרות דף - השם הרשמי שלך
st.set_page_config(
    page_title="ג'מי תורה", 
    page_icon="📜", 
    layout="wide"
)

# 2. עיצוב חסין לחיתוכים והעלמת מסגרות אדומות
st.markdown("""
    <style>
    /* הגדרות כיוון טקסט לימין */
    body, p, div, h1, h2, h3, h4, h5, h6, li, span, input, label, .stMarkdown {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    }
    
    .block-container {
        max-width: 850px !important;
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        margin: 0 auto !important;
    }
    
    /* באנר עליון ירוק כהה ויוקרתי (כמו בתמונות שלך) */
    .chat-header {
        background: linear-gradient(135deg, #1e3f20, #142a16);
        border: 1px solid #2d5a30;
        border-right: 6px solid #c5a059;
        padding: 35px;
        border-radius: 14px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
        margin-bottom: 30px;
        text-align: center !important;
    }
    .chat-header h1 {
        color: #ffffff !important;
        font-size: 2.6rem !important;
        font-weight: 700;
        margin: 0 0 10px 0 !important;
        text-align: center !important;
    }
    .chat-header p {
        color: #c5a059 !important;
        font-size: 1.2rem !important;
        margin: 0 !important;
        text-align: center !important;
    }
    
    /* 🔴 מחיקה מוחלטת של המסגרת האדומה / כתומה בזמן פוקוס */
    div[data-baseweb="base-input"], div[data-baseweb="input"] {
        border: 2px solid #2c3e50 !important;
        border-radius: 20px !important;
        background-color: #141617 !important;
        box-shadow: none !important;
    }
    div[data-baseweb="base-input"]:focus-within, div[data-baseweb="input"]:focus-within {
        border-color: #c5a059 !important;
        box-shadow: 0 0 10px rgba(197, 160, 89, 0.3) !important;
    }
    .stTextInput input {
        color: #ffffff !important;
        background-color: transparent !important;
    }
    
    /* אזהרה קבועה ללא שינויים */
    .disclaimer-fixed {
        text-align: center !important;
        color: #a0a0a0;
        font-size: 14px;
        margin-top: 15px;
        font-weight: 500;
    }
    
    /* --- עיצוב הבועות המותאם אישית (בלי חיתוכים) --- */
    .custom-chat-row {
        display: flex;
        align-items: flex-start;
        gap: 15px;
        width: 100%;
        margin-top: 25px;
        margin-bottom: 25px;
    }
    
    /* ✨ אנימציית נשימה עדינה לאווטאר של הרב */
    @keyframes avatarPulse {
        0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(197, 160, 89, 0.4); }
        50% { transform: scale(1.05); box-shadow: 0 0 15px rgba(197, 160, 89, 0.6); }
        100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(197, 160, 89, 0.4); }
    }
    
    .custom-avatar {
        width: 65px;
        height: 65px;
        border-radius: 50%;
        border: 2px solid #c5a059;
        background-color: #1a2e40;
        flex-shrink: 0;
        animation: avatarPulse 3s infinite ease-in-out;
        object-fit: contain;
    }
    
    .custom-bubble {
        background-color: #181b1c;
        border: 1px solid #2c3e50;
        border-right: 4px solid #c5a059;
        color: #e5e5e5 !important;
        padding: 20px;
        border-radius: 4px 18px 18px 18px;
        flex-grow: 1;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        font-size: 16.5px;
        line-height: 1.7;
    }
    
    .user-bubble-box {
        background-color: #263849;
        color: #ffffff !important;
        padding: 15px 20px;
        border-radius: 18px 18px 4px 18px;
        margin-right: auto;
        max-width: 80%;
        box-shadow: 0 3px 10px rgba(0,0,0,0.2);
    }
    </style>
    """, unsafe_allow_html=True)

# 3. באנר עליון רשמי
st.markdown("""
    <div class="chat-header">
        <h1>📜 ג'מי תורה</h1>
        <p>עוזר תורני דיגיטלי הלכתי וגמרא חכם</p>
    </div>
    """, unsafe_allow_html=True)

# 4. קלט משתמש ואזהרה קבועה
user_question = st.text_input("💬 שאל את ג'מי תורה כל שאלה בתורה, בהלכה, בקיצור שולחן ערוך ובגמרא:")
st.markdown('<div class="disclaimer-fixed">לתשומת ליבך, הרב הדיגיטלי יכול לטעות ובמקרים של ספק או הלכות למעשה תמיד מומלץ לשאול רב.</div>', unsafe_allow_html=True)

st.write("---")

# 5. מענה ויצירת התשובה במודל המעודכן
if user_question:
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("⚠️ שגיאה: מפתח ה-API חסר בהגדרות המערכת.")
    else:
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            
            # הגדרת המודל הנכון והעדכני ביותר למניעת שגיאת 404
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            disable_safety = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            
            system_prompt = f"""אתה "הרב הדיגיטלי" במערכת "ג'מי תורה". השב על השאלה הבאה בצורה הברורה, הפשוטה והישירה ביותר לכל אדם.
            
            חוקים:
            1. פתח בברכת שלום קצרה ומכובדת ("שלום וברכה").
            2. תן את השורה התחתונה והתשובה הישירה מיד בסעיף הראשון.
            3. הסבר קצר ופשוט ללא מילים בארמית או סיבוכים.
            4. ציין מקור בעברית בצורה פשוטה.
            5. סיים בברכה קצרה.
            
            השאלה: {user_question}"""
            
            with st.spinner("הרב מעיין במקורות ומנסח תשובה ברורה..."):
                response = model.generate_content(system_prompt, safety_settings=disable_safety)
                st.balloons()
                
                # הצגת שאלת המשתמש בבועה נקייה
                st.markdown(f"""
                    <div style="display: flex; justify-content: flex-end; width: 100%;">
                        <div class="user-bubble-box">
                            <strong>השאלה שלי:</strong> {user_question}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # אווטאר וקטורי מונפש של חכם תורני (לא נחתך ויציב)
                rabbi_avatar = "https://img.icons8.com/color/120/rabbi.png"
                
                # הצגת בועת הרב המעוצבת והמונפשת
                st.markdown(f"""
                    <div class="custom-chat-row">
                        <img class="custom-avatar" src="{rabbi_avatar}" alt="רב">
                        <div class="custom-bubble">
                            {response.text.replace('\n', '<br>')}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"חלה שגיאה בתקשורת עם מנוע ה-AI: {e}")