import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# 1. הגדרות דף קבועות - רוחב מלא
st.set_page_config(
    page_title="הרב הדיגיטלי", 
    page_icon="📜", 
    layout="wide"
)

# 2. עיצוב פרימיום נקי ומאוזן (CSS) - מיושר ונוח לקריאה
st.markdown("""
    <style>
    body, p, div, h1, h2, h3, h4, h5, h6, li, span, input, label, .stMarkdown, .stAlert {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    }
    
    /* מרכז את התוכן ברוחב נוח שלא נמתח מדי לצדדים */
    .block-container {
        max-width: 950px !important;
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        margin: 0 auto !important;
    }
    
    /* באנר עליון יוקרתי ומקצועי */
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
    
    /* תיבת הזנת שאלה */
    .stTextInput > div > div > input {
        direction: rtl !important;
        text-align: right !important;
        border: 2px solid #2c3e50 !important;
        border-radius: 25px !important;
        padding: 14px 20px !important;
        font-size: 16.5px !important;
        background-color: #141617 !important;
        color: #ffffff !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #c5a059 !important;
    }
    
    /* בועת השאלה שלי */
    .user-bubble-container {
        display: flex;
        justify-content: flex-end;
        width: 100%;
        margin-top: 20px;
    }
    .user-bubble {
        background-color: #2c3e50;
        color: #ffffff;
        padding: 14px 20px;
        border-radius: 20px 20px 4px 20px;
        max-width: 80%;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        font-size: 16px;
    }
    
    /* בועת התשובה של הרב */
    .rabbi-chat-row {
        display: flex;
        align-items: flex-start;
        gap: 15px;
        width: 100%;
        margin-top: 15px;
    }
    .rabbi-image-circle {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        border: 2px solid #c5a059;
        object-fit: cover;
        background-color: #1a2e40;
    }
    .rabbi-bubble {
        background-color: #141617;
        border: 1px solid #2c3e50;
        border-right: 4px solid #c5a059;
        color: #e0e0e0;
        padding: 22px;
        border-radius: 4px 20px 20px 20px;
        flex-grow: 1;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        font-size: 17px;
        line-height: 1.7;
    }
    
    /* עיצוב כותרות פנימיות של סעיפים */
    .rabbi-bubble h1, .rabbi-bubble h2, .rabbi-bubble h3 {
        color: #c5a059 !important;
        font-size: 1.25rem !important;
        margin-top: 18px !important;
        margin-bottom: 8px !important;
    }
    
    .disclaimer {
        text-align: center !important;
        color: #8a8a8a;
        font-size: 13px;
        margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. באנר עליון נקי לכולם
st.markdown("""
    <div class="chat-header">
        <h1>📜 הרב הדיגיטלי</h1>
        <p>תשובות ברורות, ישירות והלכה למעשה בגובה העיניים</p>
    </div>
    """, unsafe_allow_html=True)

# 4. שדה קלט לשאלה
user_question = st.text_input("💬 כתוב כאן את שאלתך להרב...")
st.markdown('<div class="disclaimer">⚠️ לתשומת לבך: המערכת נועדה ללימוד והבנה עקרונית. למעשה ובמקרים של ספק, תמיד כדאי להתייעץ עם רב הקהילה או פוסק הלכה.</div>', unsafe_allow_html=True)

st.write("---")

# 5. עיבוד והצגת התשובה הברורה והישירה
if user_question:
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("⚠️ שגיאה: מפתח ה-API חסר בהגדרות המערכת.")
    else:
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel('gemini-3-flash-preview')
            
            disable_safety = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            
            # הגדרת פרומפט חדה: תשובה ברורה, פשוטה, שורה תחתונה בהתחלה וללא פלפולים ארוכים
            system_prompt = f"""אתה "הרב הדיגיטלי" - תלמיד חכם המשיב לשאלות הציבור בצורה הברורה, המדויקת והפשוטה ביותר שיש.
            אל תדבר בשום אופן כמו בינה מלאכותית או רובוט. כתוב בצורה אנושית ומכובדת, אך קצרה ולעניין.
            
            חוקי המענה שלך:
            1. פתח בברכה קצרה ומכובדת (למשל: "שלום וברכה", "שאלתך חשובה מאוד").
            2. השורה התחתונה קודם: תן מיד בסעיף הראשון את התשובה הישירה והברורה למעשה (למשל: מה הדין או מה מברכים).
            3. הסבר קצר: תן הסבר תמציתי ופשוט בשפה ברורה ללא מילים בארמית או פלפולים ארוכים.
            4. מקורות: ציין מקור מדויק (כמו גמרא או שולחן ערוך) בצורה פשוטה בעברית.
            5. סיים בברכה קצרה.
            
            השאלה של הפונה: {user_question}"""
            
            with st.spinner("הרב מעיין במקורות ומנסח תשובה ברורה..."):
                response = model.generate_content(system_prompt, safety_settings=disable_safety)
                st.balloons()
                
                # תמונת פרופיל קלאסית ומכובדת
                rabbi_img_url = "https://cdn-icons-png.flaticon.com/512/3404/3404571.png"
                
                # תצוגת התכתבות הצ'אט
                st.markdown(f"""
                    <div class="user-bubble-container">
                        <div class="user-bubble">
                            <strong>השאלה שלי:</strong> {user_question}
                        </div>
                    </div>
                    
                    <div class="rabbi-chat-row">
                        <img class="rabbi-image-circle" src="{rabbi_img_url}">
                        <div class="rabbi-bubble">
                """, unsafe_allow_html=True)
                
                st.write(response.text)
                
                st.markdown("""
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"חלה שגיאה בתקשורת: {e}")