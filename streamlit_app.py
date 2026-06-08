import os
import streamlit as st
import requests

# 1. הגדרות דף
st.set_page_config(
    page_title="ג'מי תורה", 
    page_icon="📜", 
    layout="centered"
)

# 2. עיצוב CSS יוקרתי ונקי (ללא מסגרות מיותרות)
st.markdown("""
    <style>
    * {
        direction: rtl;
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    }
    .premium-header {
        text-align: center;
        padding: 2.5rem 1.5rem;
        background: linear-gradient(180deg, #111b24 0%, #0e1117 100%);
        border: 1px solid #233342;
        border-bottom: 3px solid #c5a059;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    .premium-header h1 {
        color: #ffffff !important;
        font-size: 3rem !important;
        font-weight: 800;
        margin: 0 !important;
    }
    .premium-header p {
        color: #c5a059 !important;
        font-size: 1.25rem !important;
        margin-top: 8px !important;
        opacity: 0.9;
    }
    div[data-baseweb="base-input"] {
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
    }
    div[data-baseweb="input"] {
        border: 1px solid #2c3e50 !important;
        background-color: #141617 !important;
        border-radius: 30px !important;
        padding-right: 15px;
        box-shadow: none !important;
    }
    div[data-baseweb="input"]:focus-within {
        border-color: #c5a059 !important;
        box-shadow: 0 0 10px rgba(197, 160, 89, 0.25) !important;
    }
    .disclaimer-text {
        text-align: center;
        color: #888888;
        font-size: 0.88rem;
        margin-top: 12px;
        font-weight: 400;
    }
    .stChatMessage {
        background-color: #181b1c !important;
        border: 1px solid #25292b !important;
        border-radius: 15px !important;
        padding: 1rem !important;
        margin-top: 15px !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. הצגת הכותרת
st.markdown("""
    <div class="premium-header">
        <h1>📜 ג'מי תורה</h1>
        <p>עוזר תורני דיגיטלי הלכתי וגמרא חכם</p>
    </div>
""", unsafe_allow_html=True)

# 4. שדה הקלט
user_question = st.text_input("💬 שאל את ג'מי תורה כל שאלה בתורה, בהלכה ובגמרא:")
st.markdown(
    '<div class="disclaimer-text">⚠️ לתשומת ליבך, הרב הדיגיטלי יכול לטעות '
    'ובמקרים של ספק או הלכות למעשה תמיד מומלץ לשאול רב.</div>', 
    unsafe_allow_html=True
)
st.write("---")

# 5. מנגנון הצ'אט וה-AI בפנייה ישירה
if user_question:
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("⚠️ מפתח ה-API חסר בהגדרות ה-Secrets של Streamlit.")
    else:
        api_key = st.secrets["GEMINI_API_KEY"]
        
        # חיבור ישיר לשרת ה-API של גוגל ללא תלות בספריות חיצוניות בעייתיות
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        
        system_prompt = (
            'אתה "הרב הדיגיטלי" במערכת "ג\'מי תורה". השב על השאלה הבאה בצורה הברורה, הפשוטה והישירה ביותר.\n'
            'חוקים: פתח בברכת שלום קצרה, תן את התשובה והשורה התחתונה מיד בהתחלה, הסבר קצר בעברית פשוטה, '
            'ציין מקור ברור וסיים בברכה.\n'
            f'השאלה: {user_question}'
        )
        
        payload = {
            "contents": [{"parts": [{"text": system_prompt}]}],
            "safetySettings": [
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]
        }
        
        with st.spinner("הרב מעיין במקורות ומנסח תשובה..."):
            try:
                response = requests.post(url, headers=headers, json=payload)
                
                if response.status_code == 200:
                    res_data = response.json()
                    try:
                        answer = res_data["candidates"][0]["content"]["parts"][0]["text"]
                        
                        # הצגת שאלת המשתמש
                        with st.chat_message("user"):
                            st.write(f"**השאלה שלי:** {user_question}")
                        
                        # בדיקה חכמה לקובץ התמונה (תומך בכל הפורמטים ששמרת)
                        rabbi_avatar = "📜"
                        if os.path.exists("rabbi.jpeg"):
                            rabbi_avatar = "rabbi.jpeg"
                        elif os.path.exists("rabbi.png"):
                            rabbi_avatar = "rabbi.png"
                        
                        # הצגת תשובת הרב
                        with st.chat_message("assistant", avatar=rabbi_avatar):
                            st.write(answer)
                            
                    except Exception:
                        st.error("התקבלה תשובה אך מבנה הנתונים השתנה:")
                        st.json(res_data)
                else:
                    try:
                        res_data = response.json()
                        error_msg = res_data.get("error", {}).get("message", "שגיאה לא ידועה")
                    except:
                        error_msg = response.text
                        
                    st.error(f"❌ שגיאה משרת גוגל (קוד {response.status_code}): {error_msg}")
                    st.info("💡 שים לב: אם רשום שהמודל לא נמצא (Not Found), הבעיה היא אך ורק במפתח ה-API שלך. מומלץ להיכנס ל-Google AI Studio, לייצר API Key חדש לחלוטין ולעדכן אותו ב-Secrets של Streamlit.")
                    
            except Exception as e:
                st.error(f"חלה שגיאה בתקשורת עם השרת: {e}")