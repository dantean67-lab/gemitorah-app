import streamlit as st
import requests

# הגדרת כותרת האתר ומראה כללי
st.set_page_config(page_title="ג'מיתורה והלכה", page_icon="📜", layout="centered")

# עיצוב מוחלט לעברית (מימין לשמאל)
st.markdown("""
    <style>
    body, p, div, h1, h2, h3, h4, h5, h6, li, span, input, label, .stMarkdown {
        direction: rtl !important;
        text-align: right !important;
    }
    .stTextInput > div > div > input {
        direction: rtl !important;
        text-align: right !important;
    }
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# כותרת ראשית
st.title("📜 ג'מיתורה והלכה")
st.subheader("עוזר בינה מלאכותית תורני מקיף - גרסה פתוחה לכולם")
st.write("---")

st.info("ברוכים הבאים לג'מיתורה! המערכת מחוברת כעת לשרת תורני פתוח. שאל כל שאלה בהלכה או בתנ\"ך:")

# תיבת קלט לשאלה
user_question = st.text_input("כתוב את שאלתך כאן:")

if user_question:
    with st.spinner("ג'מיתורה מעיין במקורות..."):
        try:
            # פנייה למודל פתוח ללא צורך במפתח אישי
            API_URL = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"
            
            # הנחיה לבוט לענות כרב פוסק
            prompt = f"<|system|>\nאתה עוזר תורני דייקן בשם ג'מיתורה. ענה בעברית על פי מקורות היהדות.\n<|user|>\n{user_question}\n<|assistant|>\n"
            
            response = requests.post(API_URL, json={"inputs": prompt, "parameters": {"max_new_tokens": 500}})
            result = response.json()
            
            # הצגת התשובה
            if isinstance(result, list) and len(result) > 0:
                full_text = result[0].get("generated_text", "")
                answer = full_text.split("<|assistant|>\n")[-1]
                st.success("**תשובת ג'מיתורה:**")
                st.write(answer)
            else:
                st.error("השרת עמוס זמנית, נסה שוב בעוד רגע.")
        except Exception as e:
            st.error("שגיאה בקבלת תשובה, אנא נסה שוב.")