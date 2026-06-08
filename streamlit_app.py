import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# 1. הגדרות דף - העברה לרוחב מלא (Wide)
st.set_page_config(
    page_title="ג'מי תורה - עוזר הלכה ובינה מלאכותית תורנית", 
    page_icon="📜", 
    layout="wide"  # כאן פתחנו את כל המסך מצד לצד!
)

# 2. ארכיטקטורת עיצוב פרימיום רחבה (CSS)
st.markdown("""
    <style>
    /* הגדרת כיוון גלובלי ויישור לימין */
    body, p, div, h1, h2, h3, h4, h5, h6, li, span, input, label, .stMarkdown, .stAlert {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    }
    
    /* מכולה ראשית שדואגת לשוליים אנושיים בצדדים ולא דוחסת הכל לאמצע */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 5rem !important;
        padding-right: 5rem !important;
    }
    
    /* כותרת עליונה רחבה ומלכותית - כחול נייבי עמוק משולב בזהב */
    .premium-header {
        background: linear-gradient(135deg, #0f1d2a, #1a2e40);
        border-bottom: 3px solid #c5a059; /* פס זהב עתיק בתחתית */
        padding: 40px;
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.25);
        margin-bottom: 35px;
        width: 100%;
    }
    .premium-header h1 {
        color: #f4edd8 !important;
        font-size: 3rem !important;
        font-weight: 800;
        margin: 0 0 10px 0 !important;
    }
    .premium-header p {
        color: #c5a059 !important;
        font-size: 1.3rem !important;
        margin: 0 !important;
    }
    
    /* עיצוב שדה הקלט - רחב ומודרני */
    .stTextInput > div > div > input {
        direction: rtl !important;
        text-align: right !important;
        border: 2px solid #2c3e50 !important;
        border-radius: 12px !important;
        padding: 16px 20px !important;
        font-size: 18px !important;
        background-color: #141617 !important;
        color: #ffffff !important;
        transition: all 0.3s ease;
    }
    .stTextInput > div > div > input:focus {
        border-color: #c5a059 !important;
        box-shadow: 0 0 15px rgba(197, 160, 89, 0.2);
    }
    
    /* תצוגת התשובה התורנית - רחבה, נקייה וברורה בלי רקעים מציקים שנחתכים */
    .torah-content-box {
        background-color: #141617;
        border-right: 5px solid #c5a059;
        padding: 30px;
        border-radius: 4px 16px 16px 4px;
        margin-top: 25px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        font-size: 17.5px !important;
        line-height: 1.8 !important;
        color: #e0e0e0 !important;
    }
    
    /* צבע זהב ייעודי לכותרות של הסעיפים שהבוט מייצר */
    .torah-content-box h1, .torah-content-box h2, .torah-content-box h3 {
        color: #c5a059 !important;
        font-weight: 600 !important;
        margin-top: 25px !important;
        margin-bottom: 12px !important;
    }
    
    /* אזהרה קטנה בתחתית השדה */
    .disclaimer-text {
        color: #8a8a8a;
        font-size: 13.5px;
        margin-top: 12px;
        font-style: italic;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. הבאנר העליון המשודרג
st.markdown("""
    <div class="premium-header">
        <h1>📜 ג'מי תורה</h1>
        <p>מערכת בינה מלאכותית מתקדמת לעיון, פסיקה ולימוד תורני</p>
    </div>
    """, unsafe_allow_html=True)

# 4. מרחב העבודה הראשי
user_question = st.text_input("🔮 שאל שאלה מפורטת בתנ\"ך, בגמרא, בהלכה או בקיצור שולחן ערוך:")
st.markdown('<div class="disclaimer-text">⚠️ לתשומת לבך: ג\'מי תורה הוא כלי עזר ללימוד ועלול לטעות. לעניין הלכה למעשה יש להיוועץ ברב מורה הוראה.</div>', unsafe_allow_html=True)

st.write("---")

# 5. ריצת המודל והצגת התוצאה
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
            
            # שדרוג ה-Prompt כדי לקבל תשובות עשירות, עמוקות ומאורגנות בהרבה
            system_prompt = f"""אתה ג'מי תורה - מנוע בינה מלאכותית תורני, פוסק הלכה ועוזר לימוד גאון ובקיא עצום.
            תפקידך להעניק תשובות מקיפות, מלומדות, עמוקות ומפורטות ביותר. אל תענה בקצרה בשום אופן.
            
            מבנה התשובה הנדרש:
            1. פתיחה מכובדת המציגה בקצרה את מהות הנושא.
            2. חלוקה לסעיפים ברורים עם כותרות בולטות (א., ב., ג. וכו').
            3. הבאת מקורות מדויקים מהתנ"ך, משנה, גמרא, ראשונים, שולחן ערוך ואחרונים (כולל מסכת, דף, סימן וסעיף במידת האפשר).
            4. סיכום קצר או מסקנה עולה בסוף הדברים.
            
            השאלה של הלומד: {user_question}"""
            
            with st.spinner("ג'מי תורה מעיין במקורות ויוצר תשובה מפורטת..."):
                response = model.generate_content(system_prompt, safety_settings=disable_safety)
                st.balloons()
                
                st.markdown("### ✍️ תשובת המערכת המורחבת:")
                
                # הצגת התשובה ברוחב מלא בתוך התיבה המלכותית החדשה
                st.markdown('<div class="torah-content-box">', unsafe_allow_html=True)
                st.write(response.text)
                st.markdown('</div>', unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"חלה שגיאה בתקשורת עם מנוע ה-AI: {e}")