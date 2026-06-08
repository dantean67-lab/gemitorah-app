import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# 1. הגדרות האתר
st.set_page_config(
    page_title="ג'מי תורה", 
    page_icon="📜", 
    layout="centered"
)

# 2. עיצוב נקי ויוקרתי (כהה וזהב, בלי ירוק, בלי טבעות אדומות)
st.markdown("""
    <style>
    /* כיוון ימין לשמאל */
    * {
        direction: rtl;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* כותרת יוקרתית ונקייה */
    .premium-header {
        text-align: center;
        padding: 2rem 1rem;
        background: linear-gradient(180deg, #111b24 0%, #0e1117 100%);
        border-bottom: 2px solid #c5a059;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .premium-header h1 {
        color: #ffffff;
        font-size: 3rem;
        margin-bottom: 0;
    }
    .premium-header p {
        color: #c5a059;
        font-size: 1.2rem;
        margin-top: 5px;
    }
    
    /* ביטול המסגרת האדומה סביב שדה הטקסט */
    div[data-baseweb="input"] {
        border: 1px solid #2c3e50 !important;
        background-color: #1a222c !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="input"]:focus-within {
        border-color: #c5a059 !important;
        box-shadow: 0 0 5px rgba(197, 160, 89, 0.5) !important;
    }
    
    /* עיצוב האזהרה הקבועה */
    .disclaimer {
        text-align: center;
        color: #888888;
        font-size: 0.9rem;
        margin-top: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# 3. תצוגת הכותרת
st.markdown("""
    <div class="premium-header">
        <h1>📜 ג'מי תורה</h1>
        <p>עוזר תורני דיגיטלי הלכתי וגמרא חכם</p>
    </div>
""", unsafe_allow_html=True)

# 4. שדה הזנת שאלה ואזהרה מדוייקת
user_question = st.text_input("💬 שאל את ג'מי תורה כל שאלה בתורה, בהלכה ובגמרא:")
st.markdown('<div class="disclaimer">לתשומת ליבך, הרב הדיגיטלי יכול לטעות ובמקרים של ספק או הלכות למעשה תמיד מומלץ לשאול רב.</div>', unsafe_allow_html=True)

st.write("---")

# 5. הגדרות ה-AI והצ'אט
if user_question:
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("⚠️ חסר מפתח API.")
    else:
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            disable_safety = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            
            system_prompt = f"""אתה "הרב הדיגיטלי" במערכת "ג'מי תורה". השב לשאלה זו בצורה ישירה, מובנת ופשוטה. פתח בשלום וברכה, תן את השורה התחתונה מיד, הסבר בעברית פשוטה וציין מקור.
            השאלה: {user_question}"""
            
            with st.spinner("מעיין במקורות..."):
                response = model.generate_content(system_prompt, safety_settings=disable_safety)
                
                # בועת המשתמש המקורית
                with st.chat_message("user"):
                    st.write(f"**השאלה שלי:** {user_question}")
                
                # ✨ הנה השינוי! קישרתי את זה ישירות לקובץ ה-jpeg המקומי שלך
                rabbi_image_url = "rabbi.jpeg"
                
                # בועת התשובה הרשמית עם האווטאר האמיתי שלך
                with st.chat_message("assistant", avatar=rabbi_image_url):
                    st.write(response.text)
                    
        except Exception as e:
            st.error(f"חלה שגיאה: {e}")