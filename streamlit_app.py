import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# 1. הגדרות דף - רוחב מלא (Wide)
st.set_page_config(
    page_title="שאל את הרב ג'מי - עוזר תורני אישי", 
    page_icon="📜", 
    layout="wide"
)

# 2. ארכיטקטורת עיצוב (CSS) - הוספת אלמנטים של דמות וצ'אט
st.markdown("""
    <style>
    /* הגדרת כיוון גלובלי ויישור לימין */
    body, p, div, h1, h2, h3, h4, h5, h6, li, span, input, label, .stMarkdown, .stAlert {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    }
    
    /* שוליים בצדדים */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 6rem !important;
        padding-right: 6rem !important;
    }
    
    /* כותרת עליונה רחבה ומלכותית */
    .premium-header {
        background: linear-gradient(135deg, #0b151f, #142436);
        border-bottom: 3px solid #c5a059;
        padding: 40px;
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        margin-bottom: 35px;
        width: 100%;
        text-align: center !important;
    }
    .premium-header h1 {
        color: #f4ecd8 !important;
        font-size: 3rem !important;
        font-weight: 800;
        margin: 0 0 10px 0 !important;
        text-align: center !important;
    }
    .premium-header p {
        color: #c5a059 !important;
        font-size: 1.25rem !important;
        margin: 0 !important;
        text-align: center !important;
    }
    
    /* עיצוב שדה הקלט */
    .stTextInput > div > div > input {
        direction: rtl !important;
        text-align: right !important;
        border: 2px solid #223446 !important;
        border-radius: 12px !important;
        padding: 16px 20px !important;
        font-size: 18px !important;
        background-color: #111314 !important;
        color: #ffffff !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #c5a059 !important;
    }
    
    /* אזהרה קטנה בתחתית השדה */
    .disclaimer-text {
        color: #8a8a8a;
        font-size: 13.5px;
        margin-top: 12px;
        font-style: italic;
    }
    
    /* מבנה מכולת הרב - הדמות לצד הטקסט */
    .rabbi-chat-container {
        display: flex;
        align-items: flex-start;
        gap: 20px;
        background-color: #141617;
        padding: 25px;
        border-radius: 12px;
        border-right: 5px solid #c5a059;
        margin-top: 20px;
    }
    
    /* עיצוב האווטאר העגול של הרב */
    .rabbi-avatar {
        width: 70px;
        height: 70px;
        background-color: #1d2e40;
        border: 2px solid #c5a059;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 35px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        flex-shrink: 0; /* מונע מהאווטאר להתכווץ */
    }
    
    /* תוכן התשובה של הרב */
    .rabbi-text-box {
        flex-grow: 1;
        font-size: 18px !important;
        line-height: 1.8 !important;
        color: #e0e0e0 !important;
    }
    
    /* צבע זהב לכותרות בתוך דברי הרב */
    h1, h2, h3 {
        color: #c5a059 !important;
        font-weight: 600 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. הבאנר העליון המשודרג בסגנון אישי
st.markdown("""
    <div class="premium-header">
        <h1>📜 שאל את הרב ג'מי</h1>
        <p>עוזר תורני אישי להלכה, גמרא ועיון במקורות חז"ל</p>
    </div>
    """, unsafe_allow_html=True)

# 4. מרחב העבודה הראשי
user_question = st.text_input("✍️ כתוב כאן את שאלתך לרב (למשל: מה מברכים על סושי? או ביאור לסוגיה בגמרא):")
st.markdown('<div class="disclaimer-text">⚠️ לתשומת לבך: הרב הדיגיטלי הוא כלי עזר ללימוד ועלול לטעות. לעניין הלכה למעשה ובמקרים של ספק יש להיוועץ ברב מורה הוראה בשר ודם.</div>', unsafe_allow_html=True)

st.write("---")

# 5. ריצת המודל והצגת התוצאה כדמות
if user_question:
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("⚠️ שגיאה: מפתח ה-API לא הוגדר ב-Secrets של המערכת.")
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
            
            # כאן שינינו לחלוטין את האישיות של הבוט לרב אנושי, חם ומכובד
            system_prompt = f"""אתה הרב ג'מי - תלמיד חכם עצום, פוסק הלכה בעל מאור פנים, ומורה דרך רוחני.
            אל תדבר כמו תוכנת מחשב או בינה מלאכותית בשום אופן. תתנהג כמו רב אמיתי שיושב מול השואל.
            
            הנחיות לניסוח ולמבנה:
            1. פתח תמיד בברכה חמה ומכובדת (למשל: "שלום רב וברכה ללומד היקר", "שאלתך חשובה ויפה מאוד", וכדומה).
            2. כתוב בשפה תורנית עשירה, חמה וברורה.
            3. חלק את התשובה בצורה מסודרת לסעיפים (א., ב., ג.) עם כותרות מודגשות.
            4. הבא מקורות מדויקים מהתנ"ך, הגמרא, השולחן ערוך והפוסקים (ציין מסכת, דף, סימן, או סעיף).
            5. בסוף דבריך, חתום בברכה קצרה (למשל: "בברכת התורה", "עלה והצלח בלימודך").
            
            השאלה שהופנתה אליך מהלומד: {user_question}"""
            
            with st.spinner("הרב מעיין במקורות ומנסח את התשובה..."):
                response = model.generate_content(system_prompt, safety_settings=disable_safety)
                st.balloons()
                
                st.markdown("### 🧔 תשובת הרב:")
                
                # יצירת תיבת צ'אט שמציגה את דמות הרב (אמוג'י זקן מכובד) לצד התשובה
                st.markdown("""
                    <div class="rabbi-chat-container">
                        <div class="rabbi-avatar">🧔</div>
                        <div class="rabbi-text-box">
                """, unsafe_allow_html=True)
                
                # הדפסת התשובה עצמה
                st.write(response.text)
                
                # סגירת המכולה של ה-HTML
                st.markdown("""
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"חלה שגיאה בתקשורת: {e}")