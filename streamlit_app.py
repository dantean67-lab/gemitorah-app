import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# 1. הגדרות דף - השם שונה באופן סופי ל"הרב הדיגיטלי" בכל מקום
st.set_page_config(
    page_title="הרב הדיגיטלי", 
    page_icon="📜", 
    layout="wide"
)

# 2. עיצוב CSS - תיקון הבועות ויצירת אנימציה
st.markdown("""
    <style>
    body, p, div, h1, h2, h3, h4, h5, h6, li, span, input, label, .stMarkdown, .stAlert {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    }
    
    .block-container {
        max-width: 950px !important;
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        margin: 0 auto !important;
    }
    
    /* באנר עליון */
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
    
    /* שדה קלט */
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
    
    /* אזהרה קבועה ויחידה */
    .disclaimer {
        text-align: center !important;
        color: #8a8a8a;
        font-size: 13.5px;
        margin-top: 10px;
        font-style: normal;
    }
    
    /* בועת המשתמש */
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
    
    /* בועת הרב והאווטאר - סידור מחדש ליציבות מירבית */
    .rabbi-chat-row {
        display: flex;
        align-items: flex-start;
        gap: 15px;
        width: 100%;
        margin-top: 15px;
        margin-bottom: 30px; /* מרווח לתחתית כדי שלא ייתקע */
    }
    
    /* האווטאר המונפש (GIF) */
    .rabbi-image-circle {
        width: 65px;
        height: 65px;
        border-radius: 50%;
        border: 2px solid #c5a059;
        object-fit: cover;
        background-color: #1a2e40;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        flex-shrink: 0; /* מונע מהתמונה להתכווץ */
    }
    
    /* התשובה עצמה */
    .rabbi-content-box {
        background-color: #141617;
        border: 1px solid #2c3e50;
        border-right: 4px solid #c5a059;
        padding: 22px;
        border-radius: 4px 20px 20px 20px;
        flex-grow: 1;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    
    /* עיצוב הטקסט והכותרות בתוך דברי הרב */
    .rabbi-content-box p, .rabbi-content-box li, .rabbi-content-box div {
        color: #e0e0e0 !important;
        font-size: 17px !important;
        line-height: 1.7 !important;
    }
    .rabbi-content-box h1, .rabbi-content-box h2, .rabbi-content-box h3 {
        color: #c5a059 !important;
        font-size: 1.25rem !important;
        margin-top: 18px !important;
        margin-bottom: 8px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. באנר עליון (השם ג'מי תורה הוסר לחלוטין)
st.markdown("""
    <div class="chat-header">
        <h1>📜 הרב הדיגיטלי</h1>
        <p>תשובות ברורות, ישירות והלכה למעשה</p>
    </div>
    """, unsafe_allow_html=True)

# 4. שדה הקלט והאזהרה הקבועה (בדיוק לפי הניסוח שלך)
user_question = st.text_input("💬 מה השאלה שלך?")
st.markdown('<div class="disclaimer">⚠️ לתשומת ליבך, הרב הדיגיטלי יכול לטעות ובמקרים של ספק או הלכה למעשה תמיד מומלץ לשאול רב.</div>', unsafe_allow_html=True)

st.write("---")

# 5. עיבוד והצגת הצ'אט
if user_question:
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("⚠️ שגיאה: מפתח ה-API חסר.")
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
            
            system_prompt = f"""אתה "הרב הדיגיטלי" - משיב לשאלות בצורה הכי פשוטה, קצרה וברורה.
            אל תדבר בשום אופן כמו בינה מלאכותית, ואל תציג את עצמך בשמות אחרים (כמו ג'מי).
            
            חוקים:
            1. פתח בברכה קצרה.
            2. תן את התשובה לשאלה (השורה התחתונה) מיד בהתחלה.
            3. הסבר קצר פשוט (בלי ארמית או פלפולים).
            4. ציין מקור בעברית פשוטה.
            5. חתום בברכה קצרה.
            
            השאלה: {user_question}"""
            
            with st.spinner("מעיין במקורות..."):
                response = model.generate_content(system_prompt, safety_settings=disable_safety)
                st.balloons()
                
                # תמונת GIF מונפשת (אנימציה של איש דת/רב חושב/מדבר)
                # זו אנימציה עדינה שתיתן תחושה חיה ולא סתם תמונה קפואה
                rabbi_gif_url = "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExM3AyNW5wZmVnZnh6ZXEzb2Z1ZWpqZnFqejQ3Z3pmaXZqZXV6dzV4eiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/l0HlHFRbmaZtBRhXG/giphy.gif"
                
                # הצגת השאלה
                st.markdown(f"""
                    <div class="user-bubble-container">
                        <div class="user-bubble">
                            <strong>השאלה שלי:</strong> {user_question}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # הצגת התשובה עם האווטאר הזז - בנוי בצורה שלא "תיתקע"
                # פיצלנו את ה-HTML כדי שStreamlit יוכל לצייר את הטקסט שלו בבטחה בפנים
                st.markdown(f"""
                    <div class="rabbi-chat-row">
                        <img class="rabbi-image-circle" src="{rabbi_gif_url}" alt="הרב">
                        <div class="rabbi-content-box">
                """, unsafe_allow_html=True)
                
                # כאן המודל כותב, והטקסט מעוצב לפי ההגדרות למעלה בלי לשבור את המכולה
                st.write(response.text)
                
                st.markdown("""
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"חלה שגיאה: {e}")