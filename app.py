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
        "請用繁體中文，用一句話歡迎大一新生參加六色積木AI工作坊。"
    )
    return response.text.strip()


st.image("brick_icon.png", width=120)
st.title(APP_TITLE)

st.markdown(
    """
歡迎來到「六色新生小夥伴」測試版。  
這一步只是確認：學生貼上自己的 Gemini API Key 後，AI 是否能正常回應。

請注意：

- 不要貼上真實姓名、學號、同學姓名或其他個人資料。
- API Key 只會暫存在本次網頁操作中，不會寫入 GitHub。
- 請不要把 API Key 貼到 LINE 群組或公開地方。
"""
)

nickname = st.text_input(
    "請輸入暱稱或匿名代碼",
    placeholder="例如：A001、小磚友、NuuStudent01",
)

api_key_text = st.text_input(
    "請貼上你的 Gemini API Key。若有多組，請用半形逗號分隔。",
    placeholder="AIzaSyxxxxxx, AIzaSyyyyyy",
    type="password",
)

privacy_ok = st.checkbox(
    "我了解這是工作坊反思工具，不是心理治療或診斷工具；我也不會輸入可識別個資。"
)

keys = parse_api_keys(api_key_text)

if keys:
    st.info(f"已偵測到 {len(keys)} 組 API Key。")

    if len(set(keys)) < len(keys):
        st.warning("偵測到重複的 API Key。重複貼上不會增加額度。")

st.divider()

if st.button("測試我的 API Key", type="primary", disabled=not privacy_ok or not keys):
    if not nickname.strip():
        st.error("請先輸入暱稱或匿名代碼。")
    else:
        success = False
        last_error = None

        for i, key in enumerate(keys, start=1):
            try:
                with st.spinner(f"正在測試第 {i} 組 API Key..."):
                    result = test_gemini_api(key)

                st.success("API Key 測試成功。")
                st.chat_message("assistant").write(result)
                success = True
                break

            except Exception as e:
                last_error = e
                st.warning(f"第 {i} 組 API Key 測試失敗，嘗試下一組。")

        if not success:
            st.error(f"目前所有 API Key 都無法使用。錯誤訊息：{last_error}")

st.divider()

st.subheader("沒有 API Key 的備援反思題")

with st.expander("我沒有 API Key，先使用固定反思題"):
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

st.caption("測試版 v0.1｜六色積木 × VIA 優勢 × 新生適應 AI Agent")
