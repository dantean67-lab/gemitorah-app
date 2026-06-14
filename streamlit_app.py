import os
import re
import time
import base64
import requests
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(
    page_title="ג'מי תורה - עוזר הלכה ובינה מלאכותית תורנית",
    page_icon="📜",
    layout="wide"
)

def get_base64_image(img_path):
    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def strip_html(text: str) -> str:
    return re.sub(r'<[^>]+>', ' ', text).strip()

def search_local_kitzur(query: str, max_chars: int = 2000) -> str:
    try:
        if not os.path.exists("kitzur_shulchan_aruch.txt"):
            return ""
        with open("kitzur_shulchan_aruch.txt", "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        keywords = [w for w in query.split() if len(w) > 2]
        if not keywords:
            return ""
        lines = content.split("\n")
        scored = []
        for i, line in enumerate(lines):
            score = sum(1 for kw in keywords if kw in line)
            if score > 0:
                start   = max(0, i - 1)
                end     = min(len(lines), i + 6)
                section = "\n".join(lines[start:end]).strip()
                if len(section) > 20:
                    scored.append((score, section))
        if not scored:
            return ""
        scored.sort(key=lambda x: x[0], reverse=True)
        return "\n\n".join(s for _, s in scored[:4])[:max_chars]
    except Exception:
        return ""

def search_sefaria(query: str, num_results: int = 5) -> list:
    seen, results = set(), []
    def _fetch(q, n):
        try:
            r = requests.get(
                "https://www.sefaria.org/api/search-wrapper",
                params={"query": q, "type": "text", "size": n, "field": "naive_lemmatizer"},
                timeout=7
            )
            for hit in r.json().get("hits", {}).get("hits", []):
                src  = hit.get("_source", {})
                ref  = src.get("ref", "")
                he_r = src.get("heRef", ref)
                he   = strip_html(src.get("he", ""))
                if ref and he and len(he) > 15 and ref not in seen:
                    seen.add(ref)
                    results.append({"ref": ref, "heRef": he_r,
                                    "he": he[:500] + ("..." if len(he) > 500 else "")})
        except Exception:
            pass
    _fetch(query, num_results)
    kw = re.sub(r'\b(מה|האם|כיצד|למה|מדוע|איך|מתי|היכן|מי|הסבר|פרט|ספר)\b', '', query).strip()
    if kw and kw != query:
        _fetch(kw, num_results)
    return results[:num_results]

st.markdown("""
<style>
body, p, div, h1, h2, h3, h4, h5, h6, li, span, input, label,
textarea, .stMarkdown, .stAlert, .stTextInput label {
    direction: rtl !important; text-align: right !important;
    font-family: 'Segoe UI', Arial, sans-serif;
}
.block-container {
    padding-top: 2rem !important; padding-bottom: 2rem !important;
    padding-left: 5rem !important; padding-right: 5rem !important;
    max-width: 1100px !important;
}
.premium-header {
    background: linear-gradient(135deg, #0b151f, #142436);
    border-bottom: 3px solid #c5a059; padding: 36px 40px; border-radius: 16px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.3); margin-bottom: 30px;
    display: flex; flex-direction: row; justify-content: space-between; align-items: center; gap: 24px;
}
.header-text-container { flex: 1; min-width: 0; }
.premium-header h1 {
    color: #f4ecd8 !important; font-size: 2.8rem !important;
    font-weight: 800; margin: 0 0 8px 0 !important; white-space: nowrap;
}
.premium-header p { color: #c5a059 !important; font-size: 1.2rem !important; margin: 0 !important; }
.rabbi-banner-img {
    width: 200px; height: auto; border-radius: 14px;
    border: 3px solid #c5a059; box-shadow: 0 6px 25px rgba(0,0,0,0.5); flex-shrink: 0;
}
@media (max-width: 768px) {
    .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
    .premium-header { flex-direction: column !important; align-items: center !important;
                      padding: 24px 20px !important; gap: 16px !important; }
    .premium-header h1 { font-size: 2rem !important; text-align: center !important; white-space: normal !important; }
    .premium-header p  { text-align: center !important; }
    .rabbi-banner-img  { width: 130px !important; }
}
.stTextInput > div > div > input {
    direction: rtl !important; text-align: right !important;
    border: 2px solid #223446 !important; border-radius: 12px !important;
    padding: 16px 20px !important; font-size: 17px !important;
    background-color: #0f1923 !important; color: #ffffff !important;
}
.stTextInput > div > div > input:focus { border-color: #c5a059 !important; }
.stButton > button {
    direction: rtl !important; border-radius: 10px !important;
    border: 1.5px solid #c5a059 !important; background: transparent !important;
    color: #c5a059 !important; font-size: 13px !important; width: 100% !important;
}
.stButton > button:hover { background: #c5a059 !important; color: #0b151f !important; }
.answer-box {
    background: #0f1923; border: 1px solid #223446; border-radius: 14px;
    padding: 28px 32px; color: #f0e6d3; font-size: 16px; line-height: 2;
    direction: rtl; text-align: right;
}
.source-box {
    background: #0d1e2e; border-right: 4px solid #c5a059;
    border-radius: 8px; padding: 12px 16px; margin-bottom: 10px;
}
.source-ref  { color: #c5a059; font-weight: 700; font-size: 14px; margin-bottom: 4px; }
.source-text { color: #c8bfa8; font-size: 13px; line-height: 1.7; }
#MainMenu { visibility: hidden !important; }
footer    { visibility: hidden !important; }
header    { visibility: hidden !important; }
[data-testid="manage-app-button"] { display: none !important; }
[data-testid="stToolbarActions"]  { display: none !important; }
[data-testid="stToolbar"]         { display: none !important; }
.stDeployButton                   { display: none !important; }
</style>
<script>
(function(){
    const h=()=>{['[data-testid="manage-app-button"]','[data-testid="stToolbarActions"]',
    '[data-testid="stToolbar"]','.stDeployButton','footer'].forEach(s=>
    document.querySelectorAll(s).forEach(el=>el.style.setProperty('display','none','important')));};
    new MutationObserver(h).observe(document.documentElement,{childList:true,subtree:true});
    h();setTimeout(h,1000);setTimeout(h,3000);
})();
</script>
""", unsafe_allow_html=True)

rabbi_base64 = get_base64_image("rabbi.jpeg") or get_base64_image("rabbi.png")
img_tag = f'<img src="data:image/jpeg;base64,{rabbi_base64}" class="rabbi-banner-img" />' if rabbi_base64 else ''
st.markdown(f"""
<div class="premium-header">
  <div class="header-text-container">
    <h1>ג&#39;מי תורה 📜</h1>
    <p>מערכת בינה מלאכותית מתקדמת לעיון, פסיקה ולימוד תורני</p>
  </div>
  {img_tag}
</div>""", unsafe_allow_html=True)

if "history"           not in st.session_state: st.session_state.history           = []
if "selected_question" not in st.session_state: st.session_state.selected_question = ""

st.markdown('<p style="color:#c5a059;font-weight:600;">💡 שאלות לדוגמה — לחץ כדי לשאול:</p>', unsafe_allow_html=True)
examples = ["מה הלכות שבת לגבי חשמל?", "מקור מצוות כיבוד אב ואם", "דיני אבילות שבעה", "הלכות כשרות בסיסיות"]
for i, (col, q) in enumerate(zip(st.columns(4), examples)):
    if col.button(q, key=f"ex_{i}", use_container_width=True):
        st.session_state.selected_question = q
        st.rerun()

user_question = st.text_input(
    "🔮 שאל שאלה בתנ\"ך, בגמרא, בהלכה או בקיצור שולחן ערוך:",
    value=st.session_state.selected_question, key="main_input"
)
st.markdown('<div style="color:#7a7a7a;font-size:13px;font-style:italic;">⚠️ ג\'מי תורה הוא כלי עזר ללימוד ועלול לטעות. לעניין הלכה למעשה — יש להיוועץ ברב מורה הוראה.</div>', unsafe_allow_html=True)
st.write("---")

if user_question and user_question.strip():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("⚠️ מפתח ה-API לא הוגדר ב-Secrets של המערכת.")
    else:
        api_key = str(st.secrets["GEMINI_API_KEY"]).strip()

        with st.spinner("🔍 מחפש מקורות..."):
            kitzur_text = search_local_kitzur(user_question.strip())
            sefaria_src = search_sefaria(user_question.strip())

        if sefaria_src:
            html = "".join(
                f'<div class="source-box"><div class="source-ref">📖 {s["heRef"]}</div>'
                f'<div class="source-text">{s["he"]}</div></div>'
                for s in sefaria_src
            )
            with st.expander(f"📚 {len(sefaria_src)} מקורות ממאגר ספריא", expanded=False):
                st.markdown(html, unsafe_allow_html=True)

        context = ""
        if kitzur_text:
            context += f"\n\n---\nמתוך קיצור שולחן ערוך:\n{kitzur_text}\n---"
        if sefaria_src:
            context += "\n\nמקורות נוספים:\n"
            for i, s in enumerate(sefaria_src, 1):
                context += f"[{i}] {s['heRef']}: {s['he']}\n\n"
        if context:
            context += "\nהתבסס על מקורות אלו וציין אותם."

        system_instruction = """אתה ג'מי תורה — מנוע בינה מלאכותית תורני ברמת גדול הדור.
בקיאותך: תנ"ך, משנה, גמרא, רש"י, רמב"ם, שולחן ערוך, משנה ברורה, ערוך השולחן, ואחרונים.
כללי תשובה: פתח בפסוק רלוונטי. חלק לסעיפים. ציין מקורות מדויקים. הצג מחלוקות. סיים ב"למעשה...".
כתוב בעברית בלבד. תשובה מקיפה — אל תקצר."""

        client = genai.Client(api_key=api_key)
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.65,
            safety_settings=[
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH",       threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT",        threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
            ]
        )
        full_prompt = user_question.strip() + context

        # מודל יחיד ישיר — ללא ניסיונות מיותרים
        MODELS = ["gemini-2.0-flash", "gemini-1.5-pro"]

        st.markdown("### ✍️ תשובת ג'מי תורה:")
        placeholder = st.empty()
        success, last_err = False, ""

        for model_name in MODELS:
            if success: break
            try:
                full_response = ""
                with st.spinner(f"...ג'מי תורה מעיין במקורות ({model_name})"):
                    for chunk in client.models.generate_content_stream(
                        model=model_name, contents=full_prompt, config=config
                    ):
                        if chunk.text:
                            full_response += chunk.text
                            placeholder.markdown(
                                f'<div class="answer-box">{full_response}▌</div>',
                                unsafe_allow_html=True
                            )
                placeholder.markdown(
                    f'<div class="answer-box">{full_response}</div>',
                    unsafe_allow_html=True
                )
                st.balloons()
                st.session_state.history.insert(0, {"q": user_question.strip(), "a": full_response})
                st.session_state.selected_question = ""
                success = True

            except Exception as e:
                last_err = str(e)
                is_rate = any(x in last_err for x in ["429","RESOURCE_EXHAUSTED"])
                is_busy = any(x in last_err for x in ["503","UNAVAILABLE","high demand"])

                if is_rate:
                    # המתן 65 שניות ונסה שוב — זו מגבלת דקה לא מגבלת יום
                    countdown = st.empty()
                    for i in range(65, 0, -1):
                        countdown.info(f"⏳ שרת גוגל עמוס — מנסה שוב בעוד {i} שניות...")
                        time.sleep(1)
                    countdown.empty()
                    try:
                        full_response = ""
                        with st.spinner(f"...מנסה שוב ({model_name})"):
                            for chunk in client.models.generate_content_stream(
                                model=model_name, contents=full_prompt, config=config
                            ):
                                if chunk.text:
                                    full_response += chunk.text
                                    placeholder.markdown(
                                        f'<div class="answer-box">{full_response}▌</div>',
                                        unsafe_allow_html=True
                                    )
                        placeholder.markdown(
                            f'<div class="answer-box">{full_response}</div>',
                            unsafe_allow_html=True
                        )
                        st.balloons()
                        st.session_state.history.insert(0, {"q": user_question.strip(), "a": full_response})
                        st.session_state.selected_question = ""
                        success = True
                    except Exception as e2:
                        last_err = str(e2)
                elif is_busy:
                    time.sleep(5)
                # אחרת — עבור למודל הבא

        if not success:
            if any(x in last_err for x in ["401","UNAUTHENTICATED"]):
                st.error("⚠️ מפתח API שגוי. לחץ על 📋 ב-AI Studio להעתקת המפתח ועדכן ב-Secrets.")
            elif any(x in last_err for x in ["429","RESOURCE_EXHAUSTED","quota"]):
                st.error(
                    "⚠️ מגבלת שימוש — נסה שוב בעוד כמה דקות.\n\n"
                    "אם הבעיה חוזרת, כנס ל-AI Studio ← Rate Limit ← בדוק את השימוש שלך."
                )
            else:
                st.error(f"❌ שגיאה: {last_err}")

if st.session_state.history:
    st.write("---")
    st.markdown("### 📚 שאלות קודמות:")
    for item in st.session_state.history[:5]:
        with st.expander(f"🔹 {item['q'][:70]}{'...' if len(item['q'])>70 else ''}"):
            st.markdown(f'<div class="answer-box" style="font-size:14px">{item["a"]}</div>', unsafe_allow_html=True)