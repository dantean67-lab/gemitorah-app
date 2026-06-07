import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# 1. הגדרת העמוד (חייב להיות ראשון בקוד)
st.set_page_config(page_title="ג'מיתורה והלכה", page_icon="📜", layout="centered")

# 2. עיצוב לעברית (RTL) ותיבות טקסט נקיות
st.markdown("""
    <style>
    body, p, div, h1, h2, h3, h4, h5, h6, li, span, input, label, .stMarkdown, .stAlert {
        direction: rtl !important;
        text-align: right !important;
    }
    .stTextInput > div > div > input {
        direction: rtl !important;
        text-align: right !important;
        border: 2px solid #4CAF50;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. כותרות האתר
st.title("📜 ג'מיתורה והלכה")
st.subheader("גרסת ה-Pro האולטימטיבית: יודע הכל מכל כל")
st.write("---")

# 4. הגדרת מפתח ה-API ישירות על המסך
api_key = st.text_input("🔑 שלב א': הדבק כאן את מפתח ה-API שלך:", type="password")
st.markdown("[קישור ישיר לקבלת מפתח בחינם מגוגל (בחשבון מבוגר)](https://aistudio.google.com/)")
st.write("---")

# 5. תיבת השאלה של המשתמש
user_question = st.text_input("🔮 שלב ב': שאל את ג'מיתורה כל שאלה שקיימת בעולם (תנ\"ך, הלכה, גמרא):")

# 6. מנוע הבינה המלאכותית
if user_question:
    if not api_key:
        st.error("❌ הבוט לא יכול לגשת לכל הידע שבעולם בלי מפתח. אנא הדבק את המפתח בתיבה למעלה!")
    else:
        try:
            # חיבור לגוגל
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # כיבוי מוחלט של כל מסנני הבטיחות כדי למנוע את הודעות הסירוב המציקות של גוגל
            disable_safety = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            
            # הגדרת פקודה חזקה לבוט
            system_prompt = f"""
            אתה עוזר תורני גאון ועצום בשם ג'מיתורה שיודע את כל התורה, התנ"ך, המשנה, הגמרא וההלכה מכל כל.
            תפקידך לענות בעברית רהוטה, ברורה ומדויקת על השאלה: "{user_question}".
            הבא מקורות מדויקים מהספרים (ספר, פרק, פסוק, סימן או סעיף) לכל דבר שאתה אומר.
            """
            
            with st.spinner("ג'מיתורה מעיין בכל הספרים שבעולם..."):
                # שליחת הבקשה עם הגדרות הבטיחות המבוטלות
                response = model.generate_content(system_prompt, safety_settings=disable_safety)
                
                # הצגת התשובה רק כשהיא מוכנה לחלוטין
                st.balloons()
                st.success("**תשובת ג'מיתורה:**")
                st.write(response.text)
                
        except Exception as e:
            st.error(f"שגיאה בהפעלת ה-AI. ודא שהקוד שהדבקת תקין. פרטי שגיאה: {e}")