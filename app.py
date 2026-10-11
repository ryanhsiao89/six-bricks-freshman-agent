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


# =========================================================
# 2. Session State
# =========================================================
if "api_ready" not in st.session_state:
    st.session_state.api_ready = False

if "nickname" not in st.session_state:
    st.session_state.nickname = ""

if "pre_score" not in st.session_state:
    st.session_state.pre_score = 5

if "selected_topic" not in st.session_state:
    st.session_state.selected_topic = "👋 人際交往"

if "reflection_started" not in st.session_state:
    st.session_state.reflection_started = False

if "active_api_key" not in st.session_state:
    st.session_state.active_api_key = ""

if "active_key_index" not in st.session_state:
    st.session_state.active_key_index = None

if "api_keys_list" not in st.session_state:
    st.session_state.api_keys_list = []

if "last_test_message" not in st.session_state:
    st.session_state.last_test_message = ""

if "activity_feedback" not in st.session_state:
    st.session_state.activity_feedback = {}

if "activity_answers" not in st.session_state:
    st.session_state.activity_answers = {}

if "custom_activity_name" not in st.session_state:
    st.session_state.custom_activity_name = ""


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

    # -----------------------------------------------------
    # 活動一：合作高塔
    # -----------------------------------------------------
    "tower": {
        "label": "🧱 合作高塔",
        "title": "合作高塔：勇氣 × 正義",
        "emoji": "🧱",
        "virtues": "勇氣、正義",
        "strengths": (
            "勇敢、堅毅、正直、生命力、"
            "公民精神、公平、領導力"
        ),
        "description": (
            "透過合作疊高塔，觀察自己在團隊中的角色、"
            "行動力、挫折反應與合作方式。"
        ),
        "questions": [
            (
                "剛剛在合作高塔活動中，你在團隊裡比較像哪一種角色？"
                "例如：快速行動者、穩定支持者、規則提醒者、"
                "創意發想者、團隊協調者。"
            ),
            (
                "當高塔倒下或遇到困難時，你的第一個反應是什麼？"
                "你後來怎麼調整？"
            ),
            (
                "這個活動中，你覺得自己展現了哪一種勇氣或"
                "團隊合作的優勢？"
            ),
        ],
    },

    # -----------------------------------------------------
    # 活動二：背對背溝通
    # -----------------------------------------------------
    "back_to_back": {
        "label": "👂 背對背溝通",
        "title": "背對背溝通：人道 × 智慧與知識",
        "emoji": "👂",
        "virtues": "人道、智慧與知識",
        "strengths": (
            "愛、仁慈、社交智慧、"
            "創造力、好奇心、開明思想、喜愛學習、觀點"
        ),
        "description": (
            "透過背對背建構，體驗表達、聆聽、提問、"
            "同理與形成共識的重要性。"
        ),
        "questions": [
            (
                "剛剛活動中，你覺得「說清楚」比較難，"
                "還是「聽懂別人」比較難？為什麼？"
            ),
            (
                "當訊息不清楚時，你有沒有嘗試確認、提問、"
                "理解對方的角度或感受？請簡單描述。"
            ),
            (
                "如果把這個經驗放到大學交朋友、宿舍生活或"
                "分組報告，你想提醒自己什麼？"
            ),
        ],
    },

    # -----------------------------------------------------
    # 活動三：聆聽與建構
    # -----------------------------------------------------
    "listen_build": {
        "label": "📚 聆聽與建構",
        "title": "聆聽與建構：智慧與知識 × 節制",
        "emoji": "📚",
        "virtues": "智慧與知識、節制",
        "strengths": (
            "創造力、好奇心、開明思想、喜愛學習、觀點、"
            "寬恕、謙遜、謹慎、自制力"
        ),
        "description": (
            "透過聆聽指令與建構任務，連結大學課業、"
            "學習策略、壓力調節與自我修正。"
        ),
        "questions": [
            (
                "當指令不清楚、任務不確定時，你通常會怎麼做？"
                "例如：先嘗試、問清楚、觀察別人、等待更多資訊、"
                "容易焦慮。"
            ),
            (
                "面對大學課業，你目前最需要哪一種支持？"
                "例如：時間管理、同伴討論、問問題的勇氣、"
                "整理筆記、先完成基本版本。"
            ),
            (
                "這週你可以做哪一個小行動，幫助自己更適應"
                "大學學習？"
            ),
        ],
    },

    # -----------------------------------------------------
    # 活動四：六色積木骨牌
    # -----------------------------------------------------
    "domino": {
        "label": "🎯 六色積木骨牌",
        "title": "六色積木骨牌：節制 × 正義 × 超越",
        "emoji": "🎯",
        "virtues": "節制、正義、超越",
        "strengths": (
            "謹慎、自制力、謙遜、寬恕、"
            "公民精神、公平、領導力、"
            "希望、感恩、欣賞美好卓越、幽默、靈修性"
        ),
        "description": (
            "透過六色積木骨牌活動，觀察自己在規劃、耐心、"
            "細心、合作與連鎖影響中的表現，也反思失敗後"
            "如何重新調整與再開始。"
        ),
        "questions": [
            (
                "在六色積木骨牌活動中，你比較投入的是哪一部分？"
                "例如：規劃路線、擺放細節、協助同伴、"
                "檢查穩定性、觀察整體效果。"
            ),
            (
                "當骨牌中途倒掉、失敗或不如預期時，"
                "你的第一個反應是什麼？你後來怎麼面對或調整？"
            ),
            (
                "這個活動讓你看見自己哪一種優勢？"
                "它又可以怎麼連結到你未來的大學生活？"
            ),
        ],
    },

    # -----------------------------------------------------
    # 活動五：其他活動
    # -----------------------------------------------------
    "other": {
        "label": "✨ 其他六色積木活動",
        "title": "其他六色積木活動",
        "emoji": "✨",
        "virtues": "由 AI 根據學生實際經驗，從 VIA 六大美德中辨識",
        "strengths": ALL_VIA_STRENGTHS,
        "description": (
            "如果今天最有感受、最有印象的六色積木活動"
            "不在前面四項，可以在這裡自行輸入活動名稱，"
            "並和 AI 小夥伴分享你的經驗。"
        ),
        "questions": [
            (
                "這個活動中發生了什麼事情，讓你特別有感受"
                "或印象深刻？"
            ),
            (
                "在活動過程中，你觀察到自己有哪些反應、做法、"
                "想法或情緒？也可以分享你和其他人的互動。"
            ),
            (
                "從這個活動經驗中，你覺得自己發現了什麼優勢、"
                "能力，或值得帶進大學生活的提醒？"
            ),
        ],
    },
}

ACTIVITY_OPTIONS = list(ACTIVITIES.keys())


# =========================================================
# 5. 基礎工具函式
# =========================================================
def parse_api_keys(raw_text: str):
    if not raw_text:
        return []

    keys = [
        k.strip()
        for k in re.split(r"[\n,]+", raw_text)
        if k.strip()
    ]

    return keys


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

    return (
        "我有收到你的反思，但這次模型沒有回傳完整文字。"
        "可以再試一次，或先用手機筆記記下你的想法。"
    )


# =========================================================
# 6. Gemini API 測試
# =========================================================
def test_gemini_api(api_key: str):
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(MODEL_NAME)

    response = model.generate_content(
        (
            "請用自然的繁體中文，用一句活潑溫暖的話，"
            "歡迎大一新生參加六色積木 AI 工作坊。"
            "請使用「大一新生」這個詞，不要改寫成其他稱呼。"
        ),
        generation_config={
            "temperature": 0.2,
            "max_output_tokens": 150,
        },
    )

    return extract_response_text(response)


# =========================================================
# 7. 建立活動反思 Prompt
# =========================================================
def build_activity_prompt(
    activity_key: str,
    nickname: str,
    pre_score: int,
    selected_topic: str,
    answers: list[str],
):
    activity = ACTIVITIES[activity_key]

    # 如果是「其他」，使用學生輸入的實際活動名稱
    if activity_key == "other":
        actual_activity_name = (
            st.session_state.custom_activity_name.strip()
            if st.session_state.custom_activity_name.strip()
            else "其他六色積木活動"
        )

    else:
        actual_activity_name = activity["title"]

    answer_text = "\n".join(
        [
            (
                f"Q{i + 1}: {activity['questions'][i]}\n"
                f"A{i + 1}: {answers[i].strip()}"
            )
            for i in range(len(answers))
        ]
    )

    special_other_instruction = ""

    if activity_key == "other":
        special_other_instruction = f"""
【本次是學生自行輸入的其他活動】

請特別遵守：

1. 不要預設學生一定展現某一類 VIA 美德。
2. 請根據學生實際描述中的行為、想法、情緒與互動證據，
   從完整 VIA 六大美德與 24 項優勢中，
   選出最有具體證據支持的 1 到 2 項優勢。
3. 不要因為活動名稱本身就推測優勢。
4. 如果資料不足以支持某項優勢，請不要硬套標籤。

完整 VIA 六大美德與 24 項優勢：

{ALL_VIA_STRENGTHS}
"""

    prompt = f"""
你是「六色新生小夥伴」，一位溫暖、活潑、穩定的
大學新生工作坊反思陪伴者。

你的任務是根據學生在六色積木活動後的反思，協助學生整理：

1. 他在活動中展現的 1 到 2 個 VIA 性格優勢。
2. 這些優勢如何連結到大學生活適應。
3. 一個五分鐘內可以完成的新生小行動。

【回應原則】

1. 請使用自然的繁體中文。
2. 回覆長度控制在約 120 到 180 字。
3. 語氣溫暖、活潑、鼓勵，但不要幼稚。
4. 只能根據學生實際提供的內容推論，不要憑空稱讚。
5. 優勢命名要有具體依據。
6. 不要診斷。
7. 不要提供心理治療。
8. 不要說教。
9. 不要要求學生揭露真實姓名、學號、同學姓名或私人個資。
10. 不要自稱心理師或治療師。
11. 不要假裝知道學生沒有提供的事情。

【安全原則】

如果學生內容出現：

- 明顯自傷想法
- 輕生意念
- 傷害他人的意圖
- 嚴重絕望
- 立即安全危機

請停止一般優勢回饋。

改為鼓勵學生立即：

1. 找現場講師或工作人員。
2. 找可信任的人陪伴。
3. 聯絡校內諮商輔導中心。
4. 若有立即危險，尋求當地緊急服務。

【學生資訊】

暱稱或匿名代碼：
{nickname}

目前新生適應電量：
{pre_score}/10

學生目前最想探索的主題：
{selected_topic}

【本次活動】

活動名稱：
{actual_activity_name}

對應 VIA 美德：
{activity['virtues']}

可能相關的優勢：
{activity['strengths']}

活動說明：
{activity['description']}

{special_other_instruction}

【學生反思】

{answer_text}

【請使用以下格式回覆】

🧱 我看見你的優勢：
請用 1 到 2 句，具體指出學生可能展現的 VIA 優勢，
並簡短說明你是從哪個活動反應看見的。

🌱 可以帶回大學生活的是：
把剛才的活動經驗連結到人際交往、學業挑戰、
生涯探索或自我照顧。

✨ 這週的一小步：
提供一個實際、簡單、五分鐘內可以開始的小行動。
""".strip()

    return prompt


# =========================================================
# 8. Gemini 回覆
# =========================================================
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


def generate_activity_feedback(
    activity_key: str,
    answers: list[str],
):
    prompt = build_activity_prompt(
        activity_key=activity_key,
        nickname=st.session_state.nickname,
        pre_score=st.session_state.pre_score,
        selected_topic=st.session_state.selected_topic,
        answers=answers,
    )

    keys_to_try = []

    # 先用成功測試過的 Key
    if st.session_state.active_api_key:
        keys_to_try.append(
            st.session_state.active_api_key
        )

    # 再加入其他備援 Key
    for key in st.session_state.api_keys_list:
        if key not in keys_to_try:
            keys_to_try.append(key)

    if not keys_to_try:
        raise RuntimeError(
            "目前沒有可用的 API Key。"
            "請回到上方貼上 Gemini API Key 並完成連線測試。"
        )

    last_error = None

    for key in keys_to_try:
        try:
            feedback = generate_with_key(
                key,
                prompt,
            )

            # 成功後把這把 Key 設為目前使用中的 Key
            st.session_state.active_api_key = key

            return feedback

        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(
        f"目前所有 API Key 都無法產生回饋。最後錯誤：{last_error}"
    )


def enough_answers(answers: list[str]):
    non_empty = [
        a.strip()
        for a in answers
        if a.strip()
    ]

    total_chars = sum(
        len(a)
        for a in non_empty
    )

    return (
        len(non_empty) >= 2
        and total_chars >= 20
    )


# =========================================================
# 9. 自訂樣式
# =========================================================
st.markdown(
    """
    <style>

    .stApp {
        background:
        linear-gradient(
            180deg,
            #FFF9FB 0%,
            #F8FBFF 100%
        );
    }

    .main .block-container {
        max-width: 780px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .hero-card {
        background:
        linear-gradient(
            135deg,
            #FFF1F7 0%,
            #EEF8FF 100%
        );

        border: 1px solid #F4D7E8;
        border-radius: 24px;

        padding:
        1.4rem
        1.4rem
        1.2rem
        1.4rem;

        margin-bottom: 1.2rem;

        box-shadow:
        0 6px 18px
        rgba(0,0,0,0.05);
    }

    .hero-badge {
        display: inline-block;

        background: #FFFFFF;
        color: #E76F9A;

        border:
        1px solid
        #F4C7DB;

        border-radius: 999px;

        padding:
        0.28rem
        0.75rem;

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

        border:
        1px solid
        #EAEAEA;

        border-radius: 18px;

        padding:
        0.95rem
        1rem;

        margin-top: 0.8rem;
        margin-bottom: 0.8rem;

        box-shadow:
        0 4px 14px
        rgba(0,0,0,0.04);
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

        margin-top: -0.25rem;

        margin-bottom: 0.75rem;
    }

    .result-card {
        background: #FFFFFF;

        border:
        1px solid
        #E7EEF8;

        border-radius: 20px;

        padding:
        1rem
        1.1rem;

        margin-top: 1rem;
        margin-bottom: 1rem;

        box-shadow:
        0 4px 14px
        rgba(0,0,0,0.04);
    }

    .result-title {
        font-weight: 800;

        color: #3B3F55;

        font-size: 1.05rem;

        margin-bottom: 0.45rem;
    }

    .result-text {
        color: #5B6075;

        line-height: 1.8;

        font-size: 0.98rem;
    }

    .topic-pill {
        display: inline-block;

        padding:
        0.25rem
        0.65rem;

        border-radius: 999px;

        background: #FFF1F7;

        color: #D65C8C;

        font-weight: 700;

        margin-top: 0.3rem;
    }

    .activity-card {
        background:
        linear-gradient(
            135deg,
            #FFFFFF 0%,
            #F8FBFF 100%
        );

        border:
        1px solid
        #E6EEF8;

        border-radius: 22px;

        padding:
        1rem
        1.1rem;

        margin-top: 1rem;
        margin-bottom: 1rem;

        box-shadow:
        0 4px 14px
        rgba(0,0,0,0.04);
    }

    .activity-title {
        color: #2E3141;

        font-size: 1.25rem;

        font-weight: 850;

        margin-bottom: 0.45rem;
    }

    .activity-meta {
        color: #5B6075;

        font-size: 0.96rem;

        line-height: 1.75;
    }

    .feedback-card {
        background:
        linear-gradient(
            135deg,
            #FFF7FB 0%,
            #F1FAFF 100%
        );

        border:
        1px solid
        #F0D9EA;

        border-radius: 22px;

        padding:
        1.1rem
        1.2rem;

        margin-top: 1rem;
        margin-bottom: 1rem;

        box-shadow:
        0 4px 14px
        rgba(0,0,0,0.05);

        color: #3B3F55;

        line-height: 1.85;

        font-size: 1rem;
    }

    .other-box {
        background: #FFFDF4;

        border:
        1px dashed
        #EBCB75;

        border-radius: 18px;

        padding:
        0.9rem
        1rem;

        margin-top: 0.7rem;

        margin-bottom: 0.8rem;

        color: #5D5665;

        line-height: 1.7;
    }

    .stTextInput > div > div > input {
        border-radius: 14px;
    }

    .stTextArea textarea {
        border-radius: 14px;
    }

    .stSlider {
        padding-top: 0.3rem;
        padding-bottom: 0.6rem;
    }

    .stButton > button {
        border-radius: 14px;

        border: none;

        background:
        linear-gradient(
            90deg,
            #FF8DB3 0%,
            #7CC7FF 100%
        );

        color: white;

        font-weight: 700;

        padding:
        0.6rem
        1rem;
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
# 10. 頁首
# =========================================================
st.image(
    "brick_icon.png",
    width=115,
)

st.markdown(
    """
    <div class="hero-card">

        <div class="hero-badge">
            🧱 測試版 v0.4.3
        </div>

        <div class="hero-title">
            六色新生小夥伴
        </div>

        <div class="hero-subtitle">
            歡迎來到你的
            <b>六色積木 × AI 新生陪伴小站</b>！
            <br>
            先確認 API Key 是否能順利連線，
            再進入六色積木活動反思。
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)

st.info(
    (
        "目前可以完成 API Key 連線、新生適應電量前測、"
        "四個主要六色積木活動，以及其他活動的 AI 個人化反思。"
    ),
    icon="💡",
)


# =========================================================
# 11. 說明卡
# =========================================================
st.markdown(
    '<div class="section-title">先看一下小提醒</div>',
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)

with col1:

    st.markdown(
        """
        <div class="mini-card">

            <div class="mini-card-title">
                🌷 互動原則
            </div>

            <div class="mini-card-text">
                • 不要輸入真實姓名、學號、
                  同學姓名或其他個人資料。
                <br>
                • 這裡是工作坊反思工具，
                  不是心理治療或診斷工具。
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


with col2:

    st.markdown(
        """
        <div class="mini-card">

            <div class="mini-card-title">
                🔐 API Key 提醒
            </div>

            <div class="mini-card-text">
                • API Key 只會暫存在本次網頁操作中。
                <br>
                • 請不要貼到 LINE 群組、
                  公開文件或社群平台。
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# 12. API Key 測試區
# =========================================================
st.markdown(
    '<div class="section-title">第一步：開始連線小夥伴</div>',
    unsafe_allow_html=True,
)

nickname = st.text_input(
    "先幫自己取一個今天的小代號吧",
    placeholder=(
        "例如：A001、小磚友、NuuStudent01"
    ),
)

api_key_text = st.text_input(
    (
        "請貼上你的 Gemini API Key"
        "（若有多組，請用半形逗號分隔）"
    ),
    placeholder=(
        "AIzaSyxxxxxx, AIzaSyyyyyy"
    ),
    type="password",
)

st.markdown(
    (
        '<div class="small-tip">'
        '小提醒：如果有第 2 組備用 Key，'
        '最好來自不同 Google Cloud project。'
        '</div>'
    ),
    unsafe_allow_html=True,
)

privacy_ok = st.checkbox(
    (
        "我了解這是工作坊反思工具，"
        "不是心理治療或診斷工具；"
        "我也不會輸入可識別個資。"
    )
)

keys = parse_api_keys(
    api_key_text
)

if keys:

    st.success(
        f"已偵測到 {len(keys)} 組 API Key。",
        icon="✨",
    )

    if len(set(keys)) < len(keys):

        st.warning(
            (
                "偵測到重複的 API Key。"
                "重複貼上不會增加額度。"
            ),
            icon="⚠️",
        )

st.divider()


if st.button(
    "🧱 開始連線我的小夥伴",
    disabled=(
        not privacy_ok
        or not keys
    ),
    use_container_width=True,
):

    if not nickname.strip():

        st.error(
            "請先輸入暱稱或匿名代碼。",
            icon="❗",
        )

    else:

        success = False
        last_error = None

        for i, key in enumerate(
            keys,
            start=1,
        ):

            try:

                with st.spinner(
                    f"正在測試第 {i} 組 API Key..."
                ):

                    result = test_gemini_api(
                        key
                    )

                st.success(
                    "太好了，API Key 測試成功！",
                    icon="🎉",
                )

                with st.chat_message(
                    "assistant"
                ):

                    st.write(
                        result
                    )

                st.session_state.api_ready = True

                st.session_state.nickname = (
                    nickname.strip()
                )

                st.session_state.active_api_key = key

                st.session_state.active_key_index = i

                st.session_state.api_keys_list = keys

                st.session_state.last_test_message = result

                st.balloons()

                success = True

                break

            except Exception as e:

                last_error = e

                st.warning(
                    (
                        f"第 {i} 組 API Key 測試失敗，"
                        "準備嘗試下一組。"
                    ),
                    icon="🔄",
                )

        if not success:

            st.session_state.api_ready = False

            st.error(
                (
                    "目前所有 API Key 都無法使用。"
                    f"錯誤訊息：{last_error}"
                ),
                icon="😥",
            )


# =========================================================
# 13. API 成功後：新生適應電量前測
# =========================================================
if st.session_state.api_ready:

    st.divider()

    st.markdown(
        (
            '<div class="section-title">'
            '第二步：新生適應電量前測'
            '</div>'
        ),
        unsafe_allow_html=True,
    )

    safe_nickname = html.escape(
        st.session_state.nickname
    )

    st.markdown(
        f"""
        <div class="result-card">

            <div class="result-title">
                🎒 連線成功，{safe_nickname}！
            </div>

            <div class="result-text">
                你現在可以進入六色積木 AI 反思流程。
                <br>
                先感受一下：
                面對即將開始的大學生活，
                你目前的能量在哪裡？
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.session_state.pre_score = st.slider(
        (
            "如果 0 分是完全沒電，"
            "10 分是充滿期待，"
            "你現在面對大學新生活的電量是幾分？"
        ),
        min_value=0,
        max_value=10,
        value=int(
            st.session_state.pre_score
        ),
    )

    topic_options = [
        "👋 人際交往",
        "📚 學業挑戰",
        "🚀 生涯展望",
        "🌿 壓力與自我照顧",
    ]

    if (
        st.session_state.selected_topic
        in topic_options
    ):
        topic_index = topic_options.index(
            st.session_state.selected_topic
        )

    else:
        topic_index = 0

    st.session_state.selected_topic = st.radio(
        "你目前最想先探索哪一個主題？",
        topic_options,
        index=topic_index,
    )

    if st.button(
        "🚀 進入六色積木反思",
        use_container_width=True,
    ):

        st.session_state.reflection_started = True

    if st.session_state.reflection_started:

        safe_topic = html.escape(
            st.session_state.selected_topic
        )

        st.markdown(
            f"""
            <div class="result-card">

                <div class="result-title">
                    🧱 你的今日起點
                </div>

                <div class="result-text">

                    目前的大學生活電量：
                    <b>
                    {st.session_state.pre_score} / 10
                    </b>

                    <br>

                    想先探索的主題：

                    <span class="topic-pill">
                    {safe_topic}
                    </span>

                    <br><br>

                    接下來請選擇剛剛完成，
                    或現在最想反思的六色積木活動。

                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


# =========================================================
# 14. 五種活動入口
# =========================================================
if (
    st.session_state.api_ready
    and st.session_state.reflection_started
):

    st.divider()

    st.markdown(
        (
            '<div class="section-title">'
            '第三步：選擇六色積木活動'
            '</div>'
        ),
        unsafe_allow_html=True,
    )

    selected_activity_key = st.radio(
        (
            "請選擇剛剛完成，"
            "或今天最有感受、最有印象的活動："
        ),
        ACTIVITY_OPTIONS,
        format_func=lambda key: (
            f"{ACTIVITIES[key]['label']}"
            f"｜{ACTIVITIES[key]['virtues']}"
        ),
        horizontal=False,
    )

    selected_activity = ACTIVITIES[
        selected_activity_key
    ]


    # =====================================================
    # 如果選擇「其他」
    # =====================================================
    if selected_activity_key == "other":

        st.markdown(
            """
            <div class="other-box">
                ✨ 沒有看到你剛剛參加的活動嗎？沒關係！
                <br>
                請直接告訴小夥伴活動名稱，
                接著分享剛才的體驗即可。
            </div>
            """,
            unsafe_allow_html=True,
        )

        custom_activity_name = st.text_input(
            "✏️ 請輸入你剛剛參加的活動名稱",
            placeholder=(
                "例如：六色積木平衡挑戰、"
                "記憶排列、創意建構……"
            ),
            key="custom_activity_name_input",
        )

        st.session_state.custom_activity_name = (
            custom_activity_name.strip()
        )

    else:

        st.session_state.custom_activity_name = ""


    # =====================================================
    # 活動卡片
    # =====================================================
    if (
        selected_activity_key == "other"
        and st.session_state.custom_activity_name
    ):

        display_activity_title = (
            st.session_state.custom_activity_name
        )

    else:

        display_activity_title = (
            selected_activity["title"]
        )

    safe_activity_title = html.escape(
        display_activity_title
    )

    safe_virtues = html.escape(
        selected_activity["virtues"]
    )

    safe_strengths = html.escape(
        selected_activity["strengths"]
    )

    safe_description = html.escape(
        selected_activity["description"]
    )

    st.markdown(
        f"""
        <div class="activity-card">

            <div class="activity-title">
                {selected_activity['emoji']}
                {safe_activity_title}
            </div>

            <div class="activity-meta">

                <b>對應 VIA 美德：</b>
                {safe_virtues}

                <br>

                <b>可能相關優勢：</b>
                {safe_strengths}

                <br>

                <b>活動說明：</b>
                {safe_description}

            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


    # =====================================================
    # 活動反思
    # =====================================================
    st.markdown(
        (
            '<div class="section-title">'
            '第四步：填寫 2–3 題活動反思'
            '</div>'
        ),
        unsafe_allow_html=True,
    )

    answers = []

    for q_index, question in enumerate(
        selected_activity["questions"],
        start=1,
    ):

        answer_key = (
            f"{selected_activity_key}"
            f"_q{q_index}"
        )

        answer = st.text_area(
            f"Q{q_index}. {question}",
            key=answer_key,
            height=90,
            placeholder=(
                "可以簡單寫 1–3 句，"
                "不需要寫很多。"
            ),
        )

        answers.append(
            answer
        )

    st.session_state.activity_answers[
        selected_activity_key
    ] = answers

    st.markdown(
        (
            '<div class="small-tip">'
            '小提醒：至少填 2 題、'
            '合計約 20 字以上，'
            'AI 回饋會比較具體。'
            '</div>'
        ),
        unsafe_allow_html=True,
    )


    # =====================================================
    # 產生回饋
    # =====================================================
    if st.button(
        (
            "✨ 請小夥伴整理我的「"
            f"{selected_activity['label']}"
            "」反思"
        ),
        use_container_width=True,
    ):

        # 「其他」一定要先輸入活動名稱
        if (
            selected_activity_key == "other"
            and not st.session_state.custom_activity_name
        ):

            st.warning(
                (
                    "請先告訴小夥伴，"
                    "你剛剛參加的是哪一個活動。"
                ),
                icon="✏️",
            )

        elif not enough_answers(
            answers
        ):

            st.warning(
                (
                    "請至少填寫 2 題，"
                    "並稍微多寫一點點，"
                    "這樣小夥伴才能給你"
                    "比較具體的回饋。"
                ),
                icon="📝",
            )

        else:

            try:

                with st.spinner(
                    (
                        "小夥伴正在整理你的"
                        "優勢與下一小步..."
                    )
                ):

                    feedback = (
                        generate_activity_feedback(
                            selected_activity_key,
                            answers,
                        )
                    )

                st.session_state.activity_feedback[
                    selected_activity_key
                ] = feedback

                st.success(
                    "小夥伴整理完成！",
                    icon="🌟",
                )

            except Exception as e:

                st.error(
                    (
                        "這次產生回饋時遇到問題："
                        f"{e}"
                    ),
                    icon="😥",
                )


    # =====================================================
    # 顯示 AI 回饋
    # =====================================================
    if (
        selected_activity_key
        in st.session_state.activity_feedback
    ):

        st.markdown(
            (
                '<div class="section-title">'
                '小夥伴給你的短回饋'
                '</div>'
            ),
            unsafe_allow_html=True,
        )

        raw_feedback = (
            st.session_state.activity_feedback[
                selected_activity_key
            ]
        )

        feedback_html = html.escape(
            raw_feedback
        ).replace(
            "\n",
            "<br>",
        )

        st.markdown(
            f"""
            <div class="feedback-card">
                {feedback_html}
            </div>
            """,
            unsafe_allow_html=True,
        )


# =========================================================
# 15. 無 API Key 備援版
# =========================================================
st.divider()

st.markdown(
    (
        '<div class="section-title">'
        '沒有 API Key 也可以先做反思'
        '</div>'
    ),
    unsafe_allow_html=True,
)

with st.expander(
    "📝 我沒有 API Key，先使用固定反思題"
):

    st.markdown(
        """
請先用下面幾題完成紙本或手機筆記反思：

1. 今天六色積木活動中，我最常扮演的角色是什麼？
2. 我在人際互動中發現自己有什麼習慣？
3. 面對學業挑戰時，我最需要哪一種支持？
4. 我今天看見自己的一個優勢是什麼？
5. 我這週願意完成的一個大學生活小行動是什麼？

如果你正在做不同活動，也可以依照下面分類反思：

- 🧱 **合作高塔**：我在團隊中扮演什麼角色？遇到倒塌時怎麼調整？
- 👂 **背對背溝通**：我比較擅長表達還是聆聽？我可以如何確認對方意思？
- 📚 **聆聽與建構**：面對不清楚的指令時，我會怎麼做？我需要什麼學習支持？
- 🎯 **六色積木骨牌**：我在規劃、擺放、合作或重來的過程中展現了什麼？遇到失敗時我怎麼面對？
- ✨ **其他活動**：哪個部分讓我最有感受？我在其中展現了什麼反應、能力或優勢？
"""
    )


# =========================================================
# 16. Footer
# =========================================================
st.markdown(
    (
        '<div class="footer-note">'
        '測試版 v0.4.3｜'
        '六色積木 × VIA 優勢 × '
        '新生適應 AI Agent｜'
        'Gemini 3.5 Flash-Lite'
        '</div>'
    ),
    unsafe_allow_html=True,
)
