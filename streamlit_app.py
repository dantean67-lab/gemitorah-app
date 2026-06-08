import os
import streamlit as st
import requests

# 1. הגדרות דף - רוחב מלא (Wide) כפי שהיה בקוד המקורי והטוב
st.set_page_config(
    page_title="ג'מי תורה - עוזר הלכה ובינה מלאכותית תורנית", 
    page_icon="📜", 
    layout="wide"
)

# 2. עיצוב ה-CSS היוקרתי והרחב המקורי
st.markdown("""
    <style>
    /* הגדרת כיוון גלובלי ויישור לימין */
    body, p, div, h1, h2, h3, h4, h5, h6, li, span, input, label, .stMarkdown, .stAlert {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    }
    
    /* שוליים רחבים בצדדים למראה נקי */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 6rem !important;
        padding-right: 6rem !important;
    }
    
    /* כותרת עליונה רחבה ומלכותית - שילוב של כחול נייבי עמוק וזהב עתיק */
    .premium-header {
        background: linear-gradient(135deg, #0b151f, #142436);
        border-bottom: 3px solid #c5a059;
        padding: 40px;
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        margin-bottom: 35px;
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 20px;
    }
    .header-text-container {
        flex-grow: 1;
    }
    .premium-header h1 {
        color: #f4ecd8 !important;
        font-size: 3rem !important;
        font-weight: 800;
        margin: 0 0 10px 0 !important;
    }
    .premium-header p {
        color: #c5a059 !important;
        font-size: 1.25rem !important;
        margin: 0 !important;
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
    
    /* אזהרה קטנה בתחתית השדה */
    .disclaimer-text {
        color: #8a8a8a;
        font-size: 13.5px;
        margin-top: 12px;
        font-style: italic;
    }
    
    /* עיצוב כותרות בתוך התשובה שהבוט מייצר */
    h1, h2, h3 {
        color: #c5a059 !important;
        font-weight: 600 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. בדיקה חכמה ושילוב תמונת הרב בתוך הבאנר המלכותי
rabbi_image_html = ""
if os.path.exists("rabbi.jpeg"):
    st.image("rabbi.jpeg", width=120)  # הצגת תמונת הרב מעל הכותרת בצורה נקייה בתוך הסטייל
elif os.path.exists("rabbi.png"):
    st.image("rabbi.png", width=120)

st.markdown("""
    <div class="premium-header">
        <div class="header-text-container">
            <h1>📜 ג'מי תורה</h1>
            <p>מערכת בינה מלאכותית מתקדמת לעיון, פסיקה ולימוד תורני</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 4. מרחב העבודה הראשי
user_question = st.text_input("🔮 שאל שאלה מפורטת בתנ\"ך, בגמרא, בהלכה או בקיצור שולחן ערוך:")
st.markdown('<div class="disclaimer-text">⚠️ לתשומת לבך: ג\'מי תורה הוא כלי עזר ללימוד ועלול לטעות. לעניין הלכה למעשה יש להיוועץ ברב מורה הוראה.</div>', unsafe_allow_html=True)

st.write("---")

# 5. ריצת המודל בצורה בטוחה וישירה (בלי ספריות שבורות)
if user_question:
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("⚠️ שגיאה: מפתח ה-API לא הוגדר ב-Secrets של המערכת.")
    else:
        api_key = st.secrets["GEMINI_API_KEY"]
        
        # פנייה ישירה ומאובטחת למודל העדכני ביותר
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        
        # הפרומפט המקורי, המפורט והאיכותי ביותר שלך שיוצר תשובות עמוקות
        system_prompt = f"""אתה ג'מי תורה - מנוע בינה מלאכותית תורני, פוסק הלכה ועוזר לימוד גאון ובקיא עצום.
        תפקידך להעניק תשובות מקיפות, מלומדות, עמוקות ומפורטות ביותר. אל תענה בקצרה בשום אופן.
        
        מבנה התשובה הנדרש:
        1. פתיחה מכובדת המציגה בקצרה את מהות הנושא.
        2. חלוקה לסעיפים ברורים עם כותרות בולטות (א., ב., ג. וכו').
        3. הבאת מקורות מדויקים מהתנ"ך, משנה, גמרא, ראשונים, שולחן ערוך ואחרונים (כולל מסכת, דף, סימן וסעיף במידת האפשר).
        4. סיכום קצר או מסקנה עולה בסוף הדברים.
        
        השאלה של הלומד: {user_question}"""
        
        payload = {
            "contents": [{"parts": [{"text": system_prompt}]}],
            "safetySettings": [
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]
        }
        
        with st.spinner("ג'מי תורה מעיין במקורות ויוצר תשובה מפורטת..."):
            try:
                response = requests.post(url, headers=headers, json=payload)
                
                if response.status_code == 200:
                    res_data = response.json()
                    answer = res_data["candidates"][0]["content"]["parts"][0]["text"]
                    
                    st.balloons()
                    st.markdown("### ✍️ תשובת המערכת המורחבת:")
                    
                    # קופסת התשובה המקורית והרחבה
                    with st.container(border=True):
                        st.markdown(
                            f"<div style='font-size: 18px; line-height: 1.8; color: #e0e0e0;'>", 
                            unsafe_allow_html=True
                        )
                        st.markdown(answer)
                        st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.error(f"❌ שגיאה מהשרת (קוד {response.status_code})")
                    st.info("💡 המערכת מוכנה! כל שנותר הוא לוודא שהעתקת את מפתח ה-API החדש שקיבלת מהמסך הקודם אל תוך ה-Secrets ב-Streamlit.")
            except Exception as e:
                st.error(f"חלה שגיאה בתקשורת עם מנוע ה-AI: {e}")