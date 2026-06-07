import os
import streamlit as st

# התקנה אוטומטית של ספריית ג'מיני בשרת במידה ואינה קיימת
try:
    import google.generativeai as genai
except ImportError:
    os.system("pip install google-generativeai")
    import google.generativeai as genai

# הגדרת כותרת האתר ומראה כללי
st.set_page_config(page_title="ג'מיתורה והלכה", page_icon="📜", layout="centered")

# עיצוב מוחלט לעברית (מימין לשמאל) - פותר את בעיית הכיווניות ב-100%
st.markdown("""
    <style>
    /* הפיכת כל הטקסטים באתר לימין לשמאל */
    body, p, div, h1, h2, h3, h4, h5, h6, li, span, input, label, .stMarkdown {
        direction: rtl !important;
        text-align: right !important;
    }
    /* התאמת תיבת הקלט לעברית */
    .stTextInput > div -> div > input {
        direction: rtl !important;
        text-align: right !important;
    }
    /* עיצוב כפתור יפה */
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
st.subheader("עוזר בינה מלאכותית תורני מקיף לכל תחומי היהדות")
st.write("---")

# תפריט צדדי להפעלת המוח המלא של ג'מיני
st.sidebar.header("⚙️ הגדרות המוח של ג'מיתורה")
st.sidebar.write("כדי שהבוט ידע את **כל ההלכות והתנ\"ך בעולם**, מומלץ להכניס מפתח API בחינם.")
api_key = st.sidebar.text_input("הכנס מפתח Gemini API (חלון מאובטח):", type="password")
st.sidebar.markdown("[לחץ כאן לקבלת מפתח API בחינם תוך 30 שניות](https://aistudio.google.com/)")

# תיבת קלט לשאלה
user_question = st.text_input("שאל את ג'מיתורה כל שאלה בתנ\"ך, הלכה, מנהגים או גמרא:")

# בסיס ידע מקומי (למקרה שאין עדיין מפתח API)
LOCAL_KNOWLEDGE = {
    "נטילת ידיים": """
**הלכות נטילת ידיים בבוקר (מקור: קיצור שולחן ערוך, סימן ב'):**
1. מיד כשקמים מהשינה, יש ליטול ידיים כדי להסיר רוח רעה שעליהן ולטהרן לעבודת הבורא.
2. **סדר הנטילה:** נוטלים את הכלי ביד ימין, מעבירים לשמאל, ושופכים על יד ימין. לאחר מכן מעבירים ליד ימין ושופכים על שמאל. חוזרים על כך לסירוגין **3 פעמים** לכל יד.
3. המים צריכים להגיע עד פרק כף היד (שורש היד).
4. **אופן הברכה:** לאחר הנטילה והניגוב, **מגביהים את הידיים למעלה כנגד הפנים או הראש**, ומברכים: 
*\"בָּרוּךְ אַתָּה ה' אֱלֹקֵינוּ מֶלֶךְ הָעוֹלָם, אֲשֶׁר קִדְּשָׁנוּ בְּמִצְוֹתָיו וְצִוָּנוּ עַל נְטִילַת יָדָיִם\"*.
""",
    "ציצית": """
**הלכות ציצית (מקור: קיצור שולחן ערוך, סימן ט'):**
1. מצוות עשה מן התורה לשים ציצית בכל בגד שיש לו ארבע כנפות (פינות) שמתכסים בו.
2. זמן מצוות ציצית הוא ביום ולא בלילה.
3. **הברכה על טלית קטן:** מברכים *\"בָּרוּךְ אַתָּה ה' אֱלֹקֵינוּ מֶלֶךְ הָעוֹלָם, אֲשֶׁר קִדְּשָׁנוּ בְּמִצְוֹתָיו וְצִוָּנוּ עַל מִצְוַת צִיצִית\"*.
"""
}

# הפעלת מנוע התשובות
if user_question:
    # אם המשתמש הכניס מפתח API - הבוט הופך לגאון ויודע הכל!
    if api_key:
        try:
            genai.configure(api_key=api_key)
            model = gen_model = genai.GenerativeModel('gemini-1.5-flash')
            
            # הנחיה קשוחה לבינה המלאכותית שתענה רק לפי ההלכה האמיתית
            system_prompt = f"""
            אתה 'ג'מיתורה', עוזר בינה מלאכותית תורני דייקן ומקצועי ביותר. 
            תפקידך לענות על השאלה הבאה בעברית רהוטה ויראת שמיים: "{user_question}".
            ענה על בסיס מקורות יהודיים מוסמכים בלבד (תנ"ך, גמרא, רמב"ם, שולחן ערוך, משנה ברורה, ילקוט יוסף).
            הקפד להביא מקורות מדויקים (סימן, סעיף, פרק). 
            אם יש הבדל בין מנהג הספרדים (השולחן ערוך) למנהג האשכנזים (הרמ"א), ציין זאת במפורש.
            אל תמציא הלכות ואל תזרוק דברים ללא מקור.
            """
            
            with st.spinner("ג'מיתורה מעיין במקורות..."):
                response = model.generate_content(system_prompt)
                st.success("**תשובת ג'מיתורה (החלון המלא):**")
                st.markdown(response.text)
                
        except Exception as e:
            st.error(f"שגיאה בחיבור למוח של ג'מיני: {e}")
            
    # אם אין מפתח API - משתמשים במאגר המקומי
    else:
        found = False
        user_question_lower = user_question.lower()
        for key, response in LOCAL_KNOWLEDGE.items():
            if key in user_question_lower or ("ידיים" in user_question_lower and key == "נטילת ידיים"):
                st.success("**תשובת ג'מיתורה (מאגר מקומי):**")
                st.markdown(response)
                found = True
                break
        if not found:
            st.warning("המאגר המקומי מצומצם. כדי לשאול על כל נושא שתרצה, אנא הכנס מפתח API חינמי בסרגל הצד!")