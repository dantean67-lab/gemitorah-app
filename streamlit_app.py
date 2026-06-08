import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# 1. הגדרות דף קבועות
st.set_page_config(
    page_title="ג'מי תורה - עוזר הלכה ובינה מלאכותית תורנית", 
    page_icon="📜", 
    layout="centered"
)

# 2. שדרגנו את חבילת העיצוב (CSS) לרמה הגבוהה ביותר
st.markdown("""
    <style>
    /* הגדרת כיוון האתר מימין לשמאל וגופן נקי */
    body, p, div, h1, h2, h3, h4, h5, h6, li, span, input, label, .stMarkdown, .stAlert {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    }
    
    /* כותרת האפליקציה - אפקט זכוכית מעוצב עם גרדיאנט מלכותי */
    .main-title {
        background: linear-gradient(135deg, #163019, #234920);
        color: #f5edd6 !important;
        padding: 30px;
        border-radius: 20px;
        text-align: center !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        margin-bottom: 25px;
        border: 2px solid #d4af37; /* מסגרת זהב עדינה */
    }
    .main-title h1 {
        text-align: center !important;
        color: #f5edd6 !important;
        font-size: 2.5rem !important;
        font-weight: 700;
        margin-bottom: 5px;
    }
    .main-title h3 {
        text-align: center !important;
        color: #d4af37 !important;
        font-size: 1.2rem !important;
        font-weight: 400;
    }
    
    /* עיצוב שדה הזנת השאלה */
    .stTextInput > div > div > input {
        direction: rtl !important;
        text-align: right !important;
        border: 2px solid #2d5a27 !important;
        border-radius: 15px !important;
        padding: 14px 20px !important;
        font-size: 17px !important;
        background-color: #fdfbf7 !important;
        color: #222222 !important;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .stTextInput > div > div > input:focus {
        border-color: #d4af37 !important; /* הופך לזהב כשלוחצים עליו */
        box-shadow: 0 4px 12px rgba(212, 175, 55, 0.3);
    }
    
    /* עיצוב כרטיס התשובה - נראה כמו דף מספר מעוצב */
    .response-card {
        background-color: #fdfbf7;
        border-right: 6px solid #2d5a27;
        border-left: 1px solid #e0dcd3;
        border-top: 1px solid #e0dcd3;
        border-bottom: 1px solid #e0dcd3;
        padding: 25px;
        border-radius: 4px 16px 16px 4px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.06);
        margin-top: 20px;
        line-height: 1.7;
        color: #2b2b2b;
    }
    
    /* עיצוב הטקסט הקטן של האזהרה */
    .disclaimer-text {
        text-align: center !important;
        color: #777777;
        font-size: 13px;
        margin-top: 12px;
        font-style: italic;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. באנר כותרת
st.markdown("""
    <div class="main-title">
        <h1>📜 ג'מי תורה</h1>
        <h3>בינה מלאכותית בשירות עולם התורה וההלכה</h3>
    </div>
    """, unsafe_allow_html=True)

# 4. תיבת השאלה והאזהרה
user_question = st.text_input("🔮 שאל את ג'מי תורה כל שאלה בתורה, בהלכה ובגמרא:")
st.markdown('<div class="disclaimer-text">⚠️ ג\'מי תורה עלול לטעות, לכן תמיד מומלץ לבדוק אותו או לשאול רב בעניינים חשובים ולהלכה למעשה.</div>', unsafe_allow_html=True)

st.write("---")

# 5. הפעלת מנוע הבינה המלאכותית
if user_question:
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("⚠️ שגיאה: המפתח לא נקרא בהצלחה מה-Secrets. ודא שלחצת Save changes באתר של Streamlit.")
    else:
        try:
            # חיבור אוטומטי למפתח הסודי מה-Secrets
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
            3. ציין מקורות מדויקים ככל הניתן (מסכת, דף, סימן, סעיף).
            4. אל תחרטט ואל תמציא שום דבר מהראש.
            
            השאלה של הלומד: {user_question}"""
            
            with st.spinner("ג'מי תורה מעיין במקורות..."):
                response = model.generate_content(system_prompt, safety_settings=disable_safety)
                st.balloons()
                
                # כותרת מעוצבת לתשובה
                st.markdown("### ✍️ תשובת ג'מי תורה המפורטת:")
                
                # הדפסת התשובה בתוך "כרטיס הספר" המעוצב שלנו
                st.markdown(f'<div class="response-card">{response.text}</div>', unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"חלה שגיאה בתקשורת עם מנוע ה-AI: {e}")