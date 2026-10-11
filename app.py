import re
import html
import streamlit as st
import google.generativeai as genai


# =========================================================
# 1. 基礎設定
# =========================================================
st.set_page_config(
    page_title="六色新生小夥伴",
    page_icon="brick_icon.png",
    layout="centered",
)

APP_TITLE = "六色新生小夥伴"
MODEL_NAME = "gemini-3.5-flash-lite"
APP_VERSION = "v0.4.4"


# =========================================================
# 2. Session State
# =========================================================
def init_state():
    defaults = {
        "api_ready": False,
        "nickname": "",
        "current_energy": 5,
        "selected_topic": "👋 人際交往",
        "reflection_started": False,
        "active_api_key": "",
        "active_key_index": None,
        "api_keys_list": [],
        "last_test_message": "",
        "activity_feedback": {},
        "activity_answers": {},
        "custom_activity_name": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()


# =========================================================
# 3. VIA 六大美德 × 24 項優勢
# =========================================================
ALL_VIA_STRENGTHS = (
    "智慧與知識：創造力、好奇心、開明思想、喜愛學習、觀點；"
    "勇氣：勇敢、堅毅、正直、生命力；"
    "人道：愛、仁慈、社交智慧；"
    "正義：公民精神、公平、領導力；"
    "節制：寬恕、謙遜、謹慎、自制力；"
    "超越：欣賞美好卓越、感恩、希望、幽默、靈修性"
)


# =========================================================
# 4. 活動設定：六色積木 × VIA 六大美德
# =========================================================
ACTIVITIES = {
    "tower": {
        "label": "🧱 合作高塔",
        "title": "合作高塔：勇氣 × 正義",
        "emoji": "🧱",
        "virtues": "勇氣、正義",
        "strengths": "勇敢、堅毅、正直、生命力、公民精神、公平、領導力",
        "description": "透過合作疊高塔，觀察自己在團隊中的角色、行動力、挫折反應與合作方式。",
        "questions": [
            "剛剛在合作高塔活動中，你在團隊裡比較像哪一種角色？例如：快速行動者、穩定支持者、規則提醒者、創意發想者、團隊協調者。",
            "當高塔倒下或遇到困難時，你的第一個反應是什麼？你後來怎麼調整？",
            "這個活動中，你覺得自己展現了哪一種勇氣或團隊合作的優勢？",
        ],
    },
    "back_to_back": {
        "label": "👂 背對背溝通",
        "title": "背對背溝通：人道 × 智慧與知識",
        "emoji": "👂",
        "virtues": "人道、智慧與知識",
        "strengths": "愛、仁慈、社交智慧、創造力、好奇心、開明思想、喜愛學習、觀點",
        "description": "透過背對背建構，體驗表達、聆聽、提問、同理與形成共識的重要性。",
        "questions": [
            "剛剛活動中，你覺得「說清楚」比較難，還是「聽懂別人」比較難？為什麼？",
            "當訊息不清楚時，你有沒有嘗試確認、提問、理解對方的角度或感受？請簡單描述。",
            "如果把這個經驗放到大學交朋友、宿舍生活或分組報告，你想提醒自己什麼？",
        ],
    },
    "listen_build": {
        "label": "📚 聆聽與建構",
        "title": "聆聽與建構：智慧與知識 × 節制",
        "emoji": "📚",
        "virtues": "智慧與知識、節制",
        "strengths": "創造力、好奇心、開明思想、喜愛學習、觀點、寬恕、謙遜、謹慎、自制力",
        "description": "透過聆聽指令與建構任務，連結大學課業、學習策略、壓力調節與自我修正。",
        "questions": [
            "當指令不清楚、任務不確定時，你通常會怎麼做？例如：先嘗試、問清楚、觀察別人、等待更多資訊、容易焦慮。",
            "面對大學課業，你目前最需要哪一種支持？例如：時間管理、同伴討論、問問題的勇氣、整理筆記、先完成基本版本。",
            "這週你可以做哪一個小行動，幫助自己更適應大學學習？",
        ],
    },
    "domino": {
        "label": "🎯 六色積木骨牌",
        "title": "六色積木骨牌：節制 × 正義 × 超越",
        "emoji": "🎯",
        "virtues": "節制、正義、超越",
        "strengths": "謹慎、自制力、謙遜、寬恕、公民精神、公平、領導力、希望、感恩、欣賞美好卓越、幽默、靈修性",
        "description": "透過六色積木骨牌活動，觀察自己在規劃、耐心、細心、合作與連鎖影響中的表現，也反思失敗後如何重新調整與再開始。",
        "questions": [
            "在六色積木骨牌活動中，你比較投入的是哪一部分？例如：規劃路線、擺放細節、協助同伴、檢查穩定性、觀察整體效果。",
            "當骨牌中途倒掉、失敗或不如預期時，你的第一個反應是什麼？你後來怎麼面對或調整？",
            "這個活動讓你看見自己哪一種優勢？它又可以怎麼連結到你未來的大學生活？",
        ],
    },
    "other": {
        "label": "✨ 其他六色積木活動",
        "title": "其他六色積木活動",
        "emoji": "✨",
        "virtues": "由 AI 根據學生實際經驗，從 VIA 六大美德中辨識",
        "strengths": ALL_VIA_STRENGTHS,
        "description": "如果最有感受、最有印象的活動不在前面四項，可以自行輸入活動名稱，並和 AI 小夥伴分享經驗。",
        "questions": [
            "這個活動中發生了什麼事情，讓你特別有感受或印象深刻？",
            "在活動過程中，你觀察到自己有哪些反應、做法、想法或情緒？也可以分享你和其他人的互動。",
            "從這個活動經驗中，你覺得自己發現了什麼優勢、能力，或值得帶進大學生活的提醒？",
        ],
    },
}

ACTIVITY_OPTIONS = list(ACTIVITIES.keys())


# =========================================================
# 5. 工具函式
# =========================================================
def parse_api_keys(raw_text: str):
    if not raw_text:
        return []
    return [k.strip() for k in re.split(r"[\n,]+", raw_text) if k.strip()]


def extract_response_text(response):
    try:
        text = response.text
        if text and text.strip():
            return text.strip()
    except Exception:
        pass

    try:
        candidates = getattr(response, "candidates", []) or []
        if candidates:
            parts = candidates[0].content.parts
            text = "\n".join(
                getattr(p, "text", "")
                for p in parts
                if getattr(p, "text", "")
            )
            if text.strip():
                return text.strip()
    except Exception:
        pass

    return "我有收到你的反思，但這次模型沒有回傳完整文字。可以再試一次，或先用手機筆記記下你的想法。"


def test_gemini_api(api_key: str):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(
        "請用自然的繁體中文，用一句活潑溫暖的話，歡迎學生使用六色積木 AI 反思小夥伴。不要假設使用者一定正在工作坊現場。",
        generation_config={
            "temperature": 0.2,
            "max_output_tokens": 150,
        },
    )
    return extract_response_text(response)


def build_activity_prompt(activity_key: str, nickname: str, current_energy: int, selected_topic: str, answers: list[str]):
    activity = ACTIVITIES[activity_key]

    if activity_key == "other":
        actual_activity_name = (
            st.session_state.custom_activity_name.strip()
            if st.session_state.custom_activity_name.strip()
            else "其他六色積木活動"
        )
    else:
        actual_activity_name = activity["title"]

    answer_text = "\n".join(
        f"Q{i + 1}: {activity['questions'][i]}\nA{i + 1}: {answers[i].strip()}"
        for i in range(len(answers))
    )

    other_instruction = ""
    if activity_key == "other":
        other_instruction = f"""
【本次為學生自行輸入的其他活動】
1. 不要預設學生一定展現某一類 VIA 美德。
2. 請根據學生實際描述中的行為、想法、情緒與互動證據，從完整 VIA 六大美德與 24 項優勢中選出最有具體證據支持的 1 到 2 項優勢。
3. 不要因為活動名稱本身就推測優勢。
4. 如果資料不足以支持某項優勢，請不要硬套標籤。

完整 VIA 六大美德與 24 項優勢：
{ALL_VIA_STRENGTHS}
"""

    return f"""
你是「六色新生小夥伴」，一位溫暖、活潑、穩定的大學生工作坊延伸反思陪伴者。

學生可能在工作坊現場使用，也可能在活動結束後回家才使用。請不要假設他此刻一定仍在現場，也不要要求他完成所有活動；只需要根據他現在選擇的一項最有感經驗進行反思。

你的任務：
1. 根據學生的實際敘述，指出可能展現的 1 到 2 個 VIA 性格優勢。
2. 簡短說明你是從哪些具體反應或行為看見這些優勢。
3. 說明這些優勢如何連結到大學生活的人際、學業、生涯或自我照顧。
4. 提供一個簡單、可行、約五分鐘內可以開始的小行動。

【回應原則】
1. 使用自然的繁體中文。
2. 回覆約 120 到 180 字。
3. 語氣溫暖、活潑、鼓勵，但不要幼稚。
4. 只能根據學生實際提供的內容推論，不要憑空稱讚。
5. 優勢命名必須有具體依據，並使用 VIA 六大美德與 24 項優勢的正式名稱。
6. 請用「可能展現」、「從你的描述中看見」等較審慎措辭，不把 AI 回饋當成正式測驗結果。
7. 不要診斷、不要提供心理治療、不要說教。
8. 不要要求揭露真實姓名、學號、同學姓名或私人個資。
9. 不要自稱心理師或治療師。

【安全原則】
如果學生內容出現明顯自傷、輕生、傷害他人的意圖、嚴重絕望或立即安全危機，請停止一般優勢回饋，鼓勵他立即找可信任的人陪伴、聯絡校內諮商輔導資源；若有立即危險，尋求當地緊急服務。

【學生資訊】
暱稱或匿名代碼：{nickname}
此刻的大學生活電量：{current_energy}/10
目前最想探索的主題：{selected_topic}

【本次活動】
活動名稱：{actual_activity_name}
對應 VIA 美德：{activity['virtues']}
可能相關優勢：{activity['strengths']}
活動說明：{activity['description']}

{other_instruction}

【學生反思】
{answer_text}

【請使用以下格式回覆】

🧱 從你的描述中，我看見你可能展現：
（指出 1 到 2 項 VIA 優勢，並用一句話說明依據）

🌱 這份優勢可以怎麼帶進大學生活：
（連結到人際、學業、生涯或自我照顧）

✨ 如果你願意，可以試試這一小步：
（提供一個五分鐘內可以開始的小行動）
""".strip()


def generate_with_key(api_key: str, prompt: str):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.3,
            "max_output_tokens": 500,
        },
    )
    return extract_response_text(response)


def generate_activity_feedback(activity_key: str, answers: list[str]):
    prompt = build_activity_prompt(
        activity_key=activity_key,
        nickname=st.session_state.nickname,
        current_energy=st.session_state.current_energy,
        selected_topic=st.session_state.selected_topic,
        answers=answers,
    )

    keys_to_try = []
    if st.session_state.active_api_key:
        keys_to_try.append(st.session_state.active_api_key)

    for key in st.session_state.api_keys_list:
        if key not in keys_to_try:
            keys_to_try.append(key)

    if not keys_to_try:
        raise RuntimeError("目前沒有可用的 API Key。請回到上方貼上 Gemini API Key 並完成連線測試。")

    last_error = None
    for key in keys_to_try:
        try:
            feedback = generate_with_key(key, prompt)
            st.session_state.active_api_key = key
            return feedback
        except Exception as e:
            last_error = e

    raise RuntimeError(f"目前所有 API Key 都無法產生回饋。最後錯誤：{last_error}")


def enough_answers(answers: list[str]):
    non_empty = [a.strip() for a in answers if a.strip()]
    total_chars = sum(len(a) for a in non_empty)
    return len(non_empty) >= 2 and total_chars >= 20


# =========================================================
# 6. 自訂樣式
# =========================================================
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(180deg, #FFF9FB 0%, #F8FBFF 100%);
    }
    .main .block-container {
        max-width: 780px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    .hero-card {
        background: linear-gradient(135deg, #FFF1F7 0%, #EEF8FF 100%);
        border: 1px solid #F4D7E8;
        border-radius: 24px;
        padding: 1.4rem;
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
    }
    .mini-card, .result-card, .activity-card {
        background: #FFFFFF;
        border: 1px solid #E7EEF8;
        border-radius: 20px;
        padding: 1rem 1.1rem;
        margin-top: 0.8rem;
        margin-bottom: 0.8rem;
        box-shadow: 0 4px 14px rgba(0,0,0,0.04);
    }
    .mini-card-title, .result-title, .activity-title {
        font-weight: 800;
        color: #3B3F55;
        margin-bottom: 0.45rem;
    }
    .activity-title {
        font-size: 1.2rem;
    }
    .mini-card-text, .result-text, .activity-meta {
        color: #5B6075;
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
        margin-top: -0.25rem;
        margin-bottom: 0.75rem;
    }
    .topic-pill {
        display: inline-block;
        padding: 0.25rem 0.65rem;
        border-radius: 999px;
        background: #FFF1F7;
        color: #D65C8C;
        font-weight: 700;
        margin-top: 0.3rem;
    }
    .feedback-card {
        background: linear-gradient(135deg, #FFF7FB 0%, #F1FAFF 100%);
        border: 1px solid #F0D9EA;
        border-radius: 22px;
        padding: 1.1rem 1.2rem;
        margin-top: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 14px rgba(0,0,0,0.05);
        color: #3B3F55;
        line-height: 1.85;
        font-size: 1rem;
    }
    .other-box {
        background: #FFFDF4;
        border: 1px dashed #EBCB75;
        border-radius: 18px;
        padding: 0.9rem 1rem;
        margin: 0.7rem 0 0.8rem 0;
        color: #5D5665;
        line-height: 1.7;
    }
    .stTextInput > div > div > input, .stTextArea textarea {
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


# =========================================================
# 7. 頁首
# =========================================================
st.image("brick_icon.png", width=115)

st.markdown(
    f"""
    <div class="hero-card">
        <div class="hero-badge">🧱 測試版 {APP_VERSION}</div>
        <div class="hero-title">六色新生小夥伴</div>
        <div class="hero-subtitle">
            這是六色積木工作坊的 <b>選配延伸反思工具</b>。<br>
            你可以在工作坊現場使用，也可以先收藏連結，回家有空時再慢慢操作。<br>
            不需要完成所有活動，只要選一個你最有感受或印象最深的活動就可以。
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.info(
    "Agent 不是工作坊的必做任務，也不是心理測驗。它只是依你分享的活動經驗，陪你看看自己可能展現哪些 VIA 優勢。",
    icon="💡",
)


# =========================================================
# 8. 提醒卡
# =========================================================
st.markdown('<div class="section-title">使用前的小提醒</div>', unsafe_allow_html=True)
col1, col2 = st.columns(2)

with col1:
    st.markdown(
        """
        <div class="mini-card">
            <div class="mini-card-title">🌷 自由使用</div>
            <div class="mini-card-text">
                • 現場不方便操作完全沒關係。<br>
                • 可以回家後再使用。<br>
                • 選一項最有感的活動即可，不必全部做完。
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
        <div class="mini-card">
            <div class="mini-card-title">🔐 隱私提醒</div>
            <div class="mini-card-text">
                • 不要輸入真實姓名、學號或他人個資。<br>
                • API Key 請勿貼到群組或公開場所。<br>
                • AI 回饋不是正式心理測驗或診斷。
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# 9. API Key 連線
# =========================================================
st.markdown('<div class="section-title">第一步：連線你的小夥伴</div>', unsafe_allow_html=True)

nickname = st.text_input(
    "幫自己取一個小代號",
    placeholder="例如：A001、小磚友、NuuStudent01",
)

api_key_text = st.text_input(
    "請貼上 Gemini API Key（若有多組，請用半形逗號分隔）",
    placeholder="AIzaSyxxxxxx, AIzaSyyyyyy",
    type="password",
)

st.markdown(
    '<div class="small-tip">若準備第 2 組備用 Key，建議來自不同 Google Cloud project。</div>',
    unsafe_allow_html=True,
)

privacy_ok = st.checkbox(
    "我了解這是自我反思工具，不是心理治療、診斷或正式優勢測驗；我也不會輸入可識別個資。"
)

keys = parse_api_keys(api_key_text)

if keys:
    st.success(f"已偵測到 {len(keys)} 組 API Key。", icon="✨")
    if len(set(keys)) < len(keys):
        st.warning("偵測到重複的 API Key。重複貼上不會增加額度。", icon="⚠️")

if st.button(
    "🧱 開始連線我的小夥伴",
    disabled=not privacy_ok or not keys,
    use_container_width=True,
):
    if not nickname.strip():
        st.error("請先輸入暱稱或匿名代碼。", icon="❗")
    else:
        success = False
        last_error = None

        for i, key in enumerate(keys, start=1):
            try:
                with st.spinner(f"正在測試第 {i} 組 API Key..."):
                    result = test_gemini_api(key)

                st.session_state.api_ready = True
                st.session_state.nickname = nickname.strip()
                st.session_state.active_api_key = key
                st.session_state.active_key_index = i
                st.session_state.api_keys_list = keys
                st.session_state.last_test_message = result

                st.success("太好了，連線成功！", icon="🎉")
                with st.chat_message("assistant"):
                    st.write(result)
                st.balloons()
                success = True
                break

            except Exception as e:
                last_error = e
                st.warning(f"第 {i} 組 API Key 連線失敗，準備嘗試下一組。", icon="🔄")

        if not success:
            st.session_state.api_ready = False
            st.error(f"目前所有 API Key 都無法使用。錯誤訊息：{last_error}", icon="😥")


# =========================================================
# 10. 此刻的大學生活電量
# =========================================================
if st.session_state.api_ready:
    st.divider()
    st.markdown('<div class="section-title">第二步：此刻的大學生活電量</div>', unsafe_allow_html=True)

    safe_nickname = html.escape(st.session_state.nickname)
    st.markdown(
        f"""
        <div class="result-card">
            <div class="result-title">🎒 歡迎，{safe_nickname}！</div>
            <div class="result-text">
                不論你現在仍在工作坊現場，或已經回家一段時間，都可以從此刻的感受開始。<br>
                這個分數不是測驗，只是幫你停一下，看看自己現在的狀態。
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.session_state.current_energy = st.slider(
        "如果 0 分是完全沒電，10 分是很有能量與期待，你此刻面對大學生活的電量大約是幾分？",
        min_value=0,
        max_value=10,
        value=int(st.session_state.current_energy),
    )

    topic_options = [
        "👋 人際交往",
        "📚 學業挑戰",
        "🚀 生涯展望",
        "🌿 壓力與自我照顧",
        "✨ 只是想整理一下今天的活動經驗",
    ]

    topic_index = (
        topic_options.index(st.session_state.selected_topic)
        if st.session_state.selected_topic in topic_options
        else 0
    )

    st.session_state.selected_topic = st.radio(
        "如果要把活動經驗和大學生活連起來，你現在最想從哪個方向想想看？",
        topic_options,
        index=topic_index,
    )

    if st.button("🚀 選一個最有感的活動來聊聊", use_container_width=True):
        st.session_state.reflection_started = True


# =========================================================
# 11. 活動選擇與反思
# =========================================================
if st.session_state.api_ready and st.session_state.reflection_started:
    st.divider()
    st.markdown('<div class="section-title">第三步：選一個最有感的六色積木活動</div>', unsafe_allow_html=True)

    st.info(
        "不需要把所有活動都做一次。請選今天最有感受、印象最深，或現在最想整理的一項即可。",
        icon="✨",
    )

    selected_activity_key = st.radio(
        "你想從哪個活動開始？",
        ACTIVITY_OPTIONS,
        format_func=lambda key: f"{ACTIVITIES[key]['label']}｜{ACTIVITIES[key]['virtues']}",
    )

    selected_activity = ACTIVITIES[selected_activity_key]

    if selected_activity_key == "other":
        st.markdown(
            """
            <div class="other-box">
                ✨ 沒看到你最有感的活動嗎？沒關係！請直接輸入活動名稱，再分享你的經驗。
            </div>
            """,
            unsafe_allow_html=True,
        )

        custom_activity_name = st.text_input(
            "✏️ 請輸入活動名稱",
            placeholder="例如：六色積木平衡挑戰、記憶排列、創意建構……",
            key="custom_activity_name_input",
        )
        st.session_state.custom_activity_name = custom_activity_name.strip()
    else:
        st.session_state.custom_activity_name = ""

    display_activity_title = (
        st.session_state.custom_activity_name
        if selected_activity_key == "other" and st.session_state.custom_activity_name
        else selected_activity["title"]
    )

    st.markdown(
        f"""
        <div class="activity-card">
            <div class="activity-title">{selected_activity['emoji']} {html.escape(display_activity_title)}</div>
            <div class="activity-meta">
                <b>可能連結的 VIA 美德：</b>{html.escape(selected_activity['virtues'])}<br>
                <b>活動說明：</b>{html.escape(selected_activity['description'])}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-title">第四步：分享 2–3 個你的活動感受</div>', unsafe_allow_html=True)

    answers = []
    for q_index, question in enumerate(selected_activity["questions"], start=1):
        answer = st.text_area(
            f"Q{q_index}. {question}",
            key=f"{selected_activity_key}_q{q_index}",
            height=90,
            placeholder="簡單寫 1–3 句就可以，不需要寫得很完整。",
        )
        answers.append(answer)

    st.session_state.activity_answers[selected_activity_key] = answers

    st.markdown(
        '<div class="small-tip">至少回答 2 題、合計約 20 字以上，小夥伴才比較有足夠線索回饋你的優勢。</div>',
        unsafe_allow_html=True,
    )

    if st.button(
        f"✨ 請小夥伴陪我整理「{selected_activity['label']}」的經驗",
        use_container_width=True,
    ):
        if selected_activity_key == "other" and not st.session_state.custom_activity_name:
            st.warning("請先輸入你想分享的活動名稱。", icon="✏️")
        elif not enough_answers(answers):
            st.warning("請至少回答 2 題，並多提供一點點活動線索。", icon="📝")
        else:
            try:
                with st.spinner("小夥伴正在從你的描述中整理可能的優勢線索..."):
                    feedback = generate_activity_feedback(selected_activity_key, answers)
                st.session_state.activity_feedback[selected_activity_key] = feedback
                st.success("整理完成！這是依你目前分享內容得到的反思，不是正式測驗結果。", icon="🌟")
            except Exception as e:
                st.error(f"這次產生回饋時遇到問題：{e}", icon="😥")

    if selected_activity_key in st.session_state.activity_feedback:
        st.markdown('<div class="section-title">小夥伴給你的優勢反思</div>', unsafe_allow_html=True)
        feedback_html = html.escape(
            st.session_state.activity_feedback[selected_activity_key]
        ).replace("\n", "<br>")
        st.markdown(
            f'<div class="feedback-card">{feedback_html}</div>',
            unsafe_allow_html=True,
        )
        st.caption("這些是依你分享的活動經驗推測出的可能優勢，並非 VIA 正式量表測驗結果。")


# =========================================================
# 12. 無 API Key 備援反思
# =========================================================
st.divider()
st.markdown('<div class="section-title">暫時不使用 AI 也沒關係</div>', unsafe_allow_html=True)

with st.expander("📝 先用自己的手機筆記想一想"):
    st.markdown(
        """
如果現在不方便使用 Agent，可以先記下三件事：

1. 今天哪一個六色積木活動讓我最有感受或印象？
2. 那個過程中，我做了什麼、想到什麼、感受到什麼？
3. 這個經驗讓我看到自己可能有什麼能力或優勢？

之後有空時，再回到這個 Agent，把這些筆記貼進來一起整理即可。
"""
    )


# =========================================================
# 13. Footer
# =========================================================
st.markdown(
    f'<div class="footer-note">測試版 {APP_VERSION}｜六色積木 × VIA 優勢 × 大學生活反思 AI Agent｜Gemini 3.5 Flash-Lite</div>',
    unsafe_allow_html=True,
)
