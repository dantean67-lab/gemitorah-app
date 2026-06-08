import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# 1. הגדרות דף קבועות
st.set_page_config(
    page_title="ג'מי תורה - עוזר הלכה ובינה מלאכותית תורנית", 
    page_icon="📜", 
    layout="centered"
)

# 2. עיצוב ה-CSS החדש - נקי, ממורכז ומתאים לרקע
st.markdown("""
    <style>
    /* הגדרות כיוון וגופן לכל האתר */
    body, p, div, h1, h2, h3, h4, h5, h6, li, span, input, label, .stMarkdown, .stAlert {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    }
    
    /* כותרת ראשית - באנר ירוק תורני עמוק עם מסגרת זהב */
    .main-title {
        background: linear-gradient(135deg, #112814, #1c3f1f);
        color: #f4ecd8 !important;
        padding: 35px 20px;
        border-radius: 16px;
        text-align: center !important;
        box-shadow: 0 8px 20px rgba(0,0,0,0.3);
        margin-bottom: 30px;
        border: 1.5px solid #d4af37;
    }
    .main-title h1 {
        text-align: center !important;
        color: #f4ecd8 !important;
        font-size: 2.4rem !important;
        font-weight: 700;
        margin: 0 0 8px 0 !important;
    }
    .main-title h3 {
        text-align: center !important;
        color: #d4af37 !important;
        font-size: 1.15rem !important;
        font-weight: 400;
        margin: 0 !important;
    }
    
    /* עיצוב תיבת קלט השאלה */
    .stTextInput > div > div > input {
        direction: rtl !important;
        text-align: right !important;
        border: 2px solid #1c3f1f !important;
        border-radius: 12px !important;
        padding: 12px 15px !important;
        font-size: 16px !important;
        background-color: #1e1e1e !important;
        color: #ffffff !important;
        transition: border-color 0.3s ease;
    }
    .stTextInput > div > div > input:focus {
        border-color: #d4af37 !important;
        box-shadow: 0 0 10px rgba(212, 175, 55, 0.2);
    }
    
    /* כרטיס תשובה חדש - משתלב בצורה חלקה ברקע, בלי שבירת שוליים */
    .torah-response {
        background-color: #181a1b;
        border-right: 4px solid #d4af37;
        padding: 20px;
        border-radius: 4px 12px 12px 4px;
        margin-top: 15px;
        box-shadow: inset 0 1px 3px rgba(0,0,0,0.2);
    }
    
    /* עיצוב כותרות בתוך התשובה (א, ב, ג) */
    .torah-response h1, .torah-response h2, .torah-response h3 {
        color: #d4af37 !important;
        margin-top: 15px !important;
        margin-bottom: 8px !important;
    }
    
    /* טקסט אזהרה קטן בתחתית השדה */
    .disclaimer-text {
        text-align: center !important;
        color: #8a8a8a;
        font-size: 13px;
        margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. הצגת הבאנר העליון
st.markdown("""
    <div class="main-title">
        <h1>📜 ג'מי תורה</h1>
        <h3>בינה מלאכותית בשירות עולם התורה וההלכה</h3>
    </div>
    """, unsafe_allow_html=True)

# 4. שדה השאלה והערת האזהרה
user_question = st.text_input("🔮 שאל את ג'מי תורה כל שאלה בתורה, בהלכה ובגמרא:")
st.markdown('<div class="disclaimer-text">⚠️ ג\'מי תורה עלול לטעות, לכן תמיד מומלץ לבדוק אותו או לשאול רב בעניינים חשובים ולהלכה למעשה.</div>', unsafe_allow_html=True)

st.write("---")

# 5. ריצה מול ה-AI ושליפת התשובה
if user_question:
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("⚠️ שגיאה: המפתח לא נקרא בהצלחה מה-Secrets.")
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
            
            system_prompt = f"""אתה פוסק הלכה ועוזר תורני גאון ובקיא עצום בשם ג'מי תורה.
            תפקידך לענות על שאלות בצורה המפורטת והעשירה ביותר (לא בקצרה!).
            יש לך ידע מוחלט בכל התנ"ך, המשנה, הגמרא (בבלי וירושלמי), השולחן ערוך, וקיצור שולחן ערוך.
            
            חוקים נוקשים:
            1. ענה תמיד בעברית ברורה, מכובדת ומדויקת.
            2. חלק את התשובה לסעיפים או נקודות כדי שתהיה קריאה וברורה.
            3. השתמש בכותרות ברורות עבור סעיפים (למשל: א. כותרת, ב. כותרת).
            4. ציין מקורות מדויקים ככל הניתן (מסכת, דף, סימן, סעיף).
            5. אל תחרטט ואל תמציא שום דבר מהראש.
            
            השאלה של הלומד: {user_question}"""
            
            with st.spinner("ג'מי תורה מעיין במקורות..."):
                response = model.generate_content(system_prompt, safety_settings=disable_safety)
                st.balloons()
                
                st.markdown("### ✍️ תשובת ג'מי תורה המפורטת:")
                
                # יצירת המכולה המעוצבת החדשה שמתאימה בול לרקע הכהה
                st.markdown(f'<div class="torah-response">', unsafe_allow_html=True)
                st.write(response.text)
                st.markdown('</div>', unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"חלה שגיאה בתקשורת עם מנוע ה-AI: {e}")