import os
import base64
import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# 1. הגדרות דף - רוחב מלא (Wide)
st.set_page_config(
    page_title="ג'מי תורה - עוזר הלכה ובינה מלאכותית תורנית", 
    page_icon="📜", 
    layout="wide"
)

# פונקציית עזר להטמעת תמונת הרב בצורה נקייה וגדולה בתוך הבאנר
def get_base64_image(img_path):
    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

# 2. עיצוב ה-CSS היוקרתי והרחב
st.markdown("""
    <style>
    /* הגדרת כיוון גלובלי ויישור לימין */
    body, p, div, h1, h2, h3, h4, h5, h6, li, span, input, label, .stMarkdown, .stAlert {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    }
    
    /* שוליים רחבים ונקיים בצדדים */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 6rem !important;
        padding-right: 6rem !important;
    }
    
    /* באנר כותרת מלכותי ויוקרתי משולב Flexbox */
    .premium-header {
        background: linear-gradient(135deg, #0b151f, #142436);
        border-bottom: 3px solid #c5a059;
        padding: 40px;
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        margin-bottom: 35px;
        width: 100%;
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 30px;
    }
    .header-text-container {
        flex: 1;
    }
    .premium-header h1 {
        color: #f4ecd8 !important;
        font-size: 3rem !important;
        font-weight: 800;
        margin: 0 0 10px 0 !important;
    }
    .premium-header p {
        color: #c5a059 !important;
        font-size: 1.3rem !important;
        margin: 0 !important;
    }
    
    /* עיצוב תמונת הרב */
    .rabbi-banner-img {
        width: 240px;
        height: auto;
        border-radius: 14px;
        border: 3px solid #c5a059;
        box-shadow: 0 6px 25px rgba(0,0,0,0.5);
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
        transition: all 0.3s ease;
    }
    .stTextInput > div > div > input:focus {
        border-color: #c5a059 !important;
        box-shadow: 0 0 15px rgba(197, 160, 89, 0.2);
    }
    
    .disclaimer-text {
        color: #8a8a8a;
        font-size: 13.5px;
        margin-top: 12px;
        font-style: italic;
    }
    
    h1, h2, h3 {
        color: #c5a059 !important;
        font-weight: 600 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. בניית הבאנר העליון עם תמונת הרב
rabbi_base64 = get_base64_image("rabbi.jpeg") or get_base64_image("rabbi.png")

if rabbi_base64:
    header_html = f"""
    <div class="premium-header">
        <div class="header-text-container">
            <h1>📜 ג'מי תורה</h1>
            <p>מערכת בינה מלאכותית מתקדמת לעיון, פסיקה ולימוד תורני</p>
        </div>
        <img src="data:image/jpeg;base64,{rabbi_base64}" class="rabbi-banner-img" />
    </div>
    """
else:
    header_html = """
    <div class="premium-header">
        <div class="header-text-container">
            <h1>📜 ג'מי תורה</h1>
            <p>מערכת בינה מלאכותית מתקדמת לעיון, פסיקה ולימוד תורני</p>
        </div>
    </div>
    """
st.markdown(header_html, unsafe_allow_html=True)

# 4. מרחב העבודה הראשי
user_question = st.text_input("🔮 שאל שאלה מפורטת בתנ\"ך, בגמרא, בהלכה או בקיצור שולחן ערוך:")
st.markdown('<div class="disclaimer-text">⚠️ לתשומת לבך: ג\'מי תורה הוא כלי עזר ללימוד ועלול לטעות. לעניין הלכה למעשה יש להיוועץ ברב מורה הוראה.</div>', unsafe_allow_html=True)

st.write("---")

# 5. הפעלת המודל - הגרסה היציבה (gemini-pro)
if user_question:
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("⚠️ שגיאה: מפתח ה-API לא הוגדר ב-Secrets של המערכת.")
    else:
        try:
            # הגדרת המפתח והמודל
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel('gemini-pro')
            
            # הגדרות בטיחות פתוחות ללימוד תורני
            disable_safety = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
            }
            
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
                
                with st.container(border=True):
                    st.markdown(
                        f"<div style='font-size: 18px; line-height: 1.8; color: #e0e0e0;'>", 
                        unsafe_allow_html=True
                    )
                    st.write(response.text)
                    st.markdown("</div>", unsafe_allow_html=True)
                
        except Exception as e:
            error_str = str(e).lower()
            
            if "429" in error_str or "quota" in error_str or "exhausted" in error_str:
                st.error("⚠️ שגיאה מהשרת (קוד 429) - המכסה החינמית של גוגל הסתיימה להיום, יש לנסות שוב מחר או להחליף מפתח API.")
            elif "404" in error_str or "not found" in error_str:
                st.error("⚠️ שגיאה מהשרת (קוד 404) - בעיה בזיהוי המודל או במפתח ה-API החינמי.")
            else:
                st.error(f"חלה שגיאה בתקשורת עם מנוע ה-AI: {e}")