import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# 1. הגדרות דף - רוחב מלא (Wide)
st.set_page_config(
    page_title="שו\"ת - הרב ג'מי הדיגיטלי", 
    page_icon="📜", 
    layout="wide"
)

# 2. ארכיטקטורת עיצוב פרימיום לצ'אט (CSS)
st.markdown("""
    <style>
    /* הגדרת כיוון גלובלי וגופן */
    body, p, div, h1, h2, h3, h4, h5, h6, li, span, input, label, .stMarkdown, .stAlert {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    }
    
    /* הגבלת רוחב אזור העבודה כדי שלא ייראה מתוח מדי בצדדים */
    .block-container {
        max-width: 1000px !important;
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        margin: 0 auto !important;
    }
    
    /* באנר עליון מודרני ונקי - כחול לילה וזהב */
    .chat-header {
        background: linear-gradient(135deg, #0d1b2a, #1b263b);
        border: 1px solid #304563;
        border-right: 5px solid #d4af37;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        margin-bottom: 30px;
        text-align: center !important;
    }
    .chat-header h1 {
        color: #f4ecd8 !important;
        font-size: 2.2rem !important;
        font-weight: 700;
        margin: 0 0 5px 0 !important;
        text-align: center !important;
    }
    .chat-header p {
        color: #e0e1dd !important;
        font-size: 1.1rem !important;
        margin: 0 !important;
        text-align: center !important;
    }
    
    /* עיצוב שדה הקלט של השאלה */
    .stTextInput > div > div > input {
        direction: rtl !important;
        text-align: right !important;
        border: 2px solid #415a77 !important;
        border-radius: 25px !important; /* מעוגל כמו שדה הודעה */
        padding: 14px 20px !important;
        font-size: 16px !important;
        background-color: #0d1b2a !important;
        color: #ffffff !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #d4af37 !important;
        box-shadow: 0 0 10px rgba(212, 175, 55, 0.2);
    }
    
    /* מכולת הצ'אט הכללית */
    .chat-wrapper {
        margin-top: 30px;
        display: flex;
        flex-direction: column;
        gap: 20px;
    }
    
    /* בועת השאלה של המשתמש (מיושרת לשמאל, צבע כחול-אפרפר) */
    .user-bubble-container {
        display: flex;
        justify-content: flex-end;
        width: 100%;
    }
    .user-bubble {
        background-color: #415a77;
        color: #ffffff;
        padding: 15px 20px;
        border-radius: 20px 20px 4px 20px;
        max-width: 75%;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        font-size: 16px;
    }
    
    /* בועת התשובה של הרב (מיושרת לימין, כוללת תמונה) */
    .rabbi-chat-row {
        display: flex;
        align-items: flex-start;
        gap: 15px;
        width: 100%;
        margin-top: 10px;
    }
    .rabbi-image-circle {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        border: 2px solid #d4af37;
        object-fit: cover;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .rabbi-bubble {
        background-color: #1b263b;
        border: 1px solid #304563;
        border-right: 4px solid #d4af37;
        color: #e0e1dd;
        padding: 22px;
        border-radius: 20px 4px 20px 20px;
        flex-grow: 1;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        font-size: 17px;
        line-height: 1.7;
    }
    
    /* צבע זהב לכותרות בתוך דברי הרב */
    .rabbi-bubble h1, .rabbi-bubble h2, .rabbi-bubble h3 {
        color: #d4af37 !important;
        margin-top: 15px !important;
        margin-bottom: 8px !important;
    }
    
    .disclaimer {
        text-align: center !important;
        color: #6c757d;
        font-size: 13px;
        margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. באנר עליון נקי
st.markdown("""
    <div class="chat-header">
        <h1>📜 שאל את הרב ג'מי</h1>
        <p>מערכת שו\"ת דיגיטלית אישית להלכה וללימוד תורני</p>
    </div>
    """, unsafe_allow_html=True)

# 4. הזנת השאלה
user_question = st.text_input("💬 כתוב כאן את שאלתך לרב...")
st.markdown('<div class="disclaimer">⚠️ לתשומת לבך: הרב הדיגיטלי הוא כלי עזר מבוסס AI ועלול לטעות. להלכה למעשה יש לפנות לרב מורה הוראה.</div>', unsafe_allow_html=True)

st.write("---")

# 5. ריצת המודל והצגת חלון הצ'אט
if user_question:
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("⚠️ שגיאה: מפתח ה-API לא מוגדר ב-Secrets.")
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
            
            system_prompt = f"""אתה הרב ג'מי - תלמיד חכם עצום, פוסק הלכה חם ורחב אופקים.
            אל תדבר בשום אופן כמו תוכנה או AI. התשובות שלך צריכות להיות אנושיות, מכובדות ומאירות פנים.
            
            מבנה התשובה:
            1. פתח בברכה לבבית המותאמת לשאלה (למשל: "שלום וברכה ללומד היקר והחשוב", "שאלתך נפלאה ויסודית").
            2. השתמש בשפה תורנית עשירה ומכובדת, וחלק את הנושא לסעיפים ברורים (א., ב., ג.) עם כותרות.
            3. הבא מקורות מדויקים מהפסוקים, מהגמרא, מהשולחן ערוך או מהפוסקים האחרונים.
            4. חתום תמיד בברכת תורה חמה (למשל: "בברכה להצלחה בכל מעשי ידיך ובתלמודך, הרב ג'מי").
            
            השאלה של הלומד: {user_question}"""
            
            with st.spinner("הרב מעיין במקורות ומנסח תשובה..."):
                response = model.generate_content(system_prompt, safety_settings=disable_safety)
                st.balloons()
                
                # יצירת אזור הצ'אט המשולב
                st.markdown('<div class="chat-wrapper">', unsafe_allow_html=True)
                
                # 1. הצגת השאלה של המשתמש בבועה שמאלית
                st.markdown(f"""
                    <div class="user-bubble-container">
                        <div class="user-bubble">
                            <strong>השאלה שלי:</strong><br>{user_question}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # 2. הצגת התשובה של הרב בבועה ימנית עם תמונת אווטאר אמיתית
                # השתמשנו כאן בתמונה ציבורית ואיכותית של דמות רב מאוירת/דיגיטלית מכובדת
                rabbi_img_url = "https://cdn-icons-png.flaticon.com/512/3404/3404571.png" 
                
                st.markdown(f"""
                    <div class="rabbi-chat-row">
                        <img class="rabbi-image-circle" src="{rabbi_img_url}" alt="הרב ג'מי">
                        <div class="rabbi-bubble">
                """, unsafe_allow_html=True)
                
                # הדפסת טקסט התשובה בתוך הבועה
                st.write(response.text)
                
                # סגירת תגיות ה-HTML של הצ'אט
                st.markdown("""
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"חלה שגיאה: {e}")