import re
import streamlit as st
import google.generativeai as genai


st.set_page_config(
    page_title="六色新生小夥伴",
    page_icon="brick_icon.png",
    layout="centered",
)

APP_TITLE = "六色新生小夥伴"
MODEL_NAME = "gemini-2.5-flash-lite"


def parse_api_keys(raw_text: str):
    if not raw_text:
        return []
    return [k.strip() for k in re.split(r"[\n,]+", raw_text) if k.strip()]


def test_gemini_api(api_key: str):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(
        "請用繁體中文，用一句活潑溫暖的話，歡迎大一新生參加六色積木AI工作坊。"
    )
    return response.text.strip()


# ---------------------------
# 自訂樣式
# ---------------------------
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(180deg, #FFF9FB 0%, #F8FBFF 100%);
    }

    .main .block-container {
        max-width: 760px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .hero-card {
        background: linear-gradient(135deg, #FFF1F7 0%, #EEF8FF 100%);
        border: 1px solid #F4D7E8;
        border-radius: 24px;
        padding: 1.4rem 1.4rem 1.2rem 1.4rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 6px 18px rgba(0,0,0,0.05);
    }

    .hero-badge {
        display: inline-block;
        background: #FFFFFF;
        color: #E76F9A;
        border: 1px solid #F4C7DB;
        border-radius: 999px;
        padding: 0.28rem 0.75rem;
        font-size: 0.9rem;
        font-weight: 700;
        margin-bottom: 0.8rem;
    }

    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #2E3141;
        line-height: 1.2;
        margin-bottom: 0.35rem;
    }

    .hero-subtitle {
        font-size: 1.06rem;
        color: #555B6E;
        line-height: 1.8;
        margin-bottom: 0.2rem;
    }

    .mini-card {
        background: #FFFFFF;
        border: 1px solid #EAEAEA;
        border-radius: 18px;
        padding: 0.95rem 1rem;
        margin-top: 0.8rem;
        margin-bottom: 0.8rem;
        box-shadow: 0 4px 14px rgba(0,0,0,0.04);
    }

    .mini-card-title {
        font-weight: 800;
        color: #3F3D56;
        margin-bottom: 0.45rem;
        font-size: 1rem;
    }

    .mini-card-text {
        color: #61667A;
        line-height: 1.75;
        font-size: 0.97rem;
    }

    .section-title {
        font-size: 1.18rem;
        font-weight: 800;
        color: #3B3F55;
        margin-top: 1.2rem;
        margin-bottom: 0.45rem;
    }

    .small-tip {
        color: #6B7280;
        font-size: 0.92rem;
        line-height: 1.7;
    }

    .stTextInput > div > div > input {
        border-radius: 14px;
    }

    .stButton > button {
        border-radius: 14px;
        border: none;
        background: linear-gradient(90deg, #FF8DB3 0%, #7CC7FF 100%);
        color: white;
        font-weight: 700;
        padding: 0.6rem 1rem;
    }

    .stButton > button:hover {
        filter: brightness(1.03);
    }

    .footer-note {
        text-align: center;
        color: #8B8FA3;
        font-size: 0.88rem;
        margin-top: 1.2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------
# 頁首
# ---------------------------
st.image("brick_icon.png", width=115)

st.markdown(
    """
    <div class="hero-card">
        <div class="hero-badge">🧱 測試版 v0.2</div>
        <div class="hero-title">六色新生小夥伴</div>
        <div class="hero-subtitle">
            歡迎來到你的 <b>六色積木 × AI 新生陪伴小站</b>！<br>
            這一步先幫你確認：貼上自己的 Gemini API Key 後，AI 是否能順利回應。
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.info(
    "這是工作坊測試版，主要用途是確認學生可以順利輸入 API Key 並成功連線。",
    icon="💡",
)

# ---------------------------
# 說明卡
# ---------------------------
st.markdown('<div class="section-title">先看一下小提醒</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown(
        """
        <div class="mini-card">
            <div class="mini-card-title">🌷 互動原則</div>
            <div class="mini-card-text">
                • 不要輸入真實姓名、學號、同學姓名或其他個人資料。<br>
                • 這裡是工作坊反思工具，不是心理治療或診斷工具。
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
        <div class="mini-card">
            <div class="mini-card-title">🔐 API Key 提醒</div>
            <div class="mini-card-text">
                • API Key 只會暫存在本次網頁操作中。<br>
                • 請不要貼到 LINE 群組、公開文件或社群平台。
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------
# 輸入區
# ---------------------------
st.markdown('<div class="section-title">開始測試</div>', unsafe_allow_html=True)

nickname = st.text_input(
    "請輸入暱稱或匿名代碼",
    placeholder="例如：A001、小磚友、NuuStudent01",
)

api_key_text = st.text_input(
    "請貼上你的 Gemini API Key（若有多組，請用半形逗號分隔）",
    placeholder="AIzaSyxxxxxx, AIzaSyyyyyy",
    type="password",
)

st.markdown(
    '<div class="small-tip">小提醒：如果有第 2 組備用 Key，最好來自不同 Google Cloud project。</div>',
    unsafe_allow_html=True,
)

privacy_ok = st.checkbox(
    "我了解這是工作坊反思工具，不是心理治療或診斷工具；我也不會輸入可識別個資。"
)

keys = parse_api_keys(api_key_text)

if keys:
    st.success(f"已偵測到 {len(keys)} 組 API Key。", icon="✨")

    if len(set(keys)) < len(keys):
        st.warning("偵測到重複的 API Key。重複貼上不會增加額度。", icon="⚠️")

st.divider()

# ---------------------------
# 測試按鈕
# ---------------------------
if st.button("🚀 測試我的 API Key", disabled=not privacy_ok or not keys, use_container_width=True):
    if not nickname.strip():
        st.error("請先輸入暱稱或匿名代碼。", icon="❗")
    else:
        success = False
        last_error = None

        for i, key in enumerate(keys, start=1):
            try:
                with st.spinner(f"正在測試第 {i} 組 API Key..."):
                    result = test_gemini_api(key)

                st.success("太好了，API Key 測試成功！", icon="🎉")
                with st.chat_message("assistant"):
                    st.write(result)
                success = True
                break

            except Exception as e:
                last_error = e
                st.warning(f"第 {i} 組 API Key 測試失敗，準備嘗試下一組。", icon="🔄")

        if not success:
            st.error(f"目前所有 API Key 都無法使用。錯誤訊息：{last_error}", icon="😥")

st.divider()

# ---------------------------
# 無 Key 備援版
# ---------------------------
st.markdown('<div class="section-title">沒有 API Key 也可以先做反思</div>', unsafe_allow_html=True)

with st.expander("📝 我沒有 API Key，先使用固定反思題"):
    st.markdown(
        """
請先用下面幾題完成紙本或手機筆記反思：

1. 今天六色積木活動中，我最常扮演的角色是什麼？
2. 我在人際互動中發現自己有什麼習慣？
3. 面對學業挑戰時，我最需要哪一種支持？
4. 我今天看見自己的一個優勢是什麼？
5. 我這週願意完成的一個大學生活小行動是什麼？
"""
    )

st.markdown(
    '<div class="footer-note">測試版 v0.2｜六色積木 × VIA 優勢 × 新生適應 AI Agent</div>',
    unsafe_allow_html=True,
)
