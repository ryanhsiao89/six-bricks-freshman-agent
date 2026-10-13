import re
import html
import streamlit as st
import google.generativeai as genai


# =========================================================
# 1. 基礎設定 / Basic Settings
# =========================================================
st.set_page_config(
    page_title="六色新生小夥伴 | Six Bricks Freshman Buddy",
    page_icon="brick_icon.png",
    layout="centered",
)

APP_TITLE = "六色新生小夥伴 | Six Bricks Freshman Buddy"
MODEL_NAME = "gemini-3.5-flash-lite"
APP_VERSION = "v0.4.5 Bilingual"


# =========================================================
# 2. Session State
# =========================================================
def init_state():
    defaults = {
        "api_ready": False,
        "nickname": "",
        "current_energy": 5,
        "selected_topic": "interpersonal",
        "reflection_started": False,
        "active_api_key": "",
        "active_key_index": None,
        "api_keys_list": [],
        "last_test_message": "",
        "activity_feedback": {},
        "activity_answers": {},
        "custom_activity_name": "",
        "bilingual_feedback": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()


# =========================================================
# 3. VIA 六大美德 × 24 項優勢 / VIA 6 Virtues × 24 Strengths
# =========================================================
ALL_VIA_STRENGTHS_ZH = (
    "智慧與知識：創造力、好奇心、開明思想、喜愛學習、觀點；"
    "勇氣：勇敢、堅毅、正直、生命力；"
    "人道：愛、仁慈、社交智慧；"
    "正義：公民精神、公平、領導力；"
    "節制：寬恕、謙遜、謹慎、自制力；"
    "超越：欣賞美好卓越、感恩、希望、幽默、靈修性"
)

ALL_VIA_STRENGTHS_EN = (
    "Wisdom & Knowledge: Creativity, Curiosity, Open-Mindedness/Judgment, Love of Learning, Perspective; "
    "Courage: Bravery, Perseverance, Honesty, Zest; "
    "Humanity: Love, Kindness, Social Intelligence; "
    "Justice: Teamwork/Citizenship, Fairness, Leadership; "
    "Temperance: Forgiveness, Humility, Prudence, Self-Regulation; "
    "Transcendence: Appreciation of Beauty & Excellence, Gratitude, Hope, Humor, Spirituality"
)


# =========================================================
# 4. 主題設定 / Topic Settings
# =========================================================
TOPICS = {
    "interpersonal": {
        "zh": "👋 人際交往",
        "en": "👋 Relationships & Social Connection",
    },
    "academic": {
        "zh": "📚 學業挑戰",
        "en": "📚 Academic Challenges",
    },
    "career": {
        "zh": "🚀 生涯展望",
        "en": "🚀 Career Exploration",
    },
    "wellbeing": {
        "zh": "🌿 壓力與自我照顧",
        "en": "🌿 Stress & Self-Care",
    },
    "reflection": {
        "zh": "✨ 只是想整理一下今天的活動經驗",
        "en": "✨ I Just Want to Reflect on Today's Experience",
    },
}


def topic_display(topic_key: str) -> str:
    topic = TOPICS[topic_key]
    return f"{topic['zh']} / {topic['en']}"


# =========================================================
# 5. 活動設定 / Activity Settings
#    不預先綁定 VIA 美德；由 AI 依學生實際描述辨識。
#    VIA strengths are inferred from the student's own reflection.
# =========================================================
ACTIVITIES = {
    "tower": {
        "emoji": "🧱",
        "label_zh": "合作高塔",
        "label_en": "Team Tower Challenge",
        "description_zh": "透過合作疊高塔，觀察自己在團隊中的角色、行動力、挫折反應與合作方式。",
        "description_en": "Build a tower together and notice your role, initiative, response to setbacks, and teamwork style.",
        "questions": [
            {
                "zh": "剛剛在合作高塔活動中，你在團隊裡比較像哪一種角色？例如：快速行動者、穩定支持者、規則提醒者、創意發想者、團隊協調者。",
                "en": "What role did you tend to take in the tower activity—for example, quick starter, steady supporter, rule reminder, idea generator, or team coordinator?",
            },
            {
                "zh": "當高塔倒下或遇到困難時，你的第一個反應是什麼？你後來怎麼調整？",
                "en": "When the tower fell or your group got stuck, what was your first reaction? How did you adjust afterward?",
            },
            {
                "zh": "這個活動讓你看見自己有哪些能力、習慣或特質？",
                "en": "What abilities, habits, or personal qualities did this activity help you notice in yourself?",
            },
        ],
    },
    "back_to_back": {
        "emoji": "👂",
        "label_zh": "背對背溝通",
        "label_en": "Back-to-Back Communication",
        "description_zh": "透過背對背建構，體驗表達、聆聽、提問、同理與形成共識的重要性。",
        "description_en": "Experience the importance of clear expression, listening, questioning, empathy, and shared understanding.",
        "questions": [
            {
                "zh": "剛剛活動中，你覺得「說清楚」比較難，還是「聽懂別人」比較難？為什麼？",
                "en": "Which was harder for you: explaining clearly or understanding the other person? Why?",
            },
            {
                "zh": "當訊息不清楚時，你有沒有嘗試確認、提問、理解對方的角度或感受？請簡單描述。",
                "en": "When the message was unclear, did you try to clarify, ask questions, or understand the other person's perspective or feelings? Briefly describe what you did.",
            },
            {
                "zh": "如果把這個經驗放到大學交朋友、宿舍生活或分組報告，你想提醒自己什麼？",
                "en": "If you apply this experience to making friends, dorm life, or group projects, what would you like to remind yourself?",
            },
        ],
    },
    "listen_build": {
        "emoji": "📚",
        "label_zh": "聆聽與建構",
        "label_en": "Listen & Build",
        "description_zh": "透過聆聽指令與建構任務，連結大學課業、學習策略、壓力調節與自我修正。",
        "description_en": "Use a listening-and-building task to reflect on learning strategies, academic adjustment, stress regulation, and self-correction.",
        "questions": [
            {
                "zh": "當指令不清楚、任務不確定時，你通常會怎麼做？例如：先嘗試、問清楚、觀察別人、等待更多資訊、容易焦慮。",
                "en": "When instructions are unclear or a task feels uncertain, what do you usually do—for example, try first, ask for clarification, observe others, wait for more information, or become anxious?",
            },
            {
                "zh": "面對大學課業，你目前最需要哪一種支持？例如：時間管理、同伴討論、問問題的勇氣、整理筆記、先完成基本版本。",
                "en": "What kind of support do you most need for university study right now—for example, time management, peer discussion, courage to ask questions, note organization, or permission to start with a basic draft?",
            },
            {
                "zh": "這週你可以做哪一個小行動，幫助自己更適應大學學習？",
                "en": "What small action could you take this week to help yourself adjust to university learning?",
            },
        ],
    },
    "domino": {
        "emoji": "🎯",
        "label_zh": "六色積木骨牌",
        "label_en": "Six Bricks Domino Challenge",
        "description_zh": "透過六色積木骨牌活動，觀察自己在規劃、耐心、細心、合作與連鎖影響中的表現，也反思失敗後如何重新調整與再開始。",
        "description_en": "Use the domino challenge to notice planning, patience, attention to detail, teamwork, and how you reset after something goes wrong.",
        "questions": [
            {
                "zh": "在六色積木骨牌活動中，你比較投入的是哪一部分？例如：規劃路線、擺放細節、協助同伴、檢查穩定性、觀察整體效果。",
                "en": "Which part of the domino activity drew you in most—for example, planning the route, placing pieces carefully, helping teammates, checking stability, or watching the overall effect?",
            },
            {
                "zh": "當骨牌中途倒掉、失敗或不如預期時，你的第一個反應是什麼？你後來怎麼面對或調整？",
                "en": "When the dominoes fell too early or things did not go as expected, what was your first reaction? How did you respond or adjust afterward?",
            },
            {
                "zh": "這個活動讓你看見自己有哪些能力、優勢線索或值得帶進大學生活的提醒？",
                "en": "What abilities, possible strengths, or reminders for university life did this activity help you notice?",
            },
        ],
    },
    "other": {
        "emoji": "✨",
        "label_zh": "其他六色積木活動",
        "label_en": "Other Six Bricks Activity",
        "description_zh": "如果最有感受、最有印象的活動不在前面四項，可以自行輸入活動名稱，並和 AI 小夥伴分享經驗。",
        "description_en": "If your most meaningful activity is not listed above, enter its name and reflect on the experience with the AI buddy.",
        "questions": [
            {
                "zh": "這個活動中發生了什麼事情，讓你特別有感受或印象深刻？",
                "en": "What happened in this activity that felt especially meaningful or memorable to you?",
            },
            {
                "zh": "在活動過程中，你觀察到自己有哪些反應、做法、想法或情緒？也可以分享你和其他人的互動。",
                "en": "What reactions, actions, thoughts, or emotions did you notice in yourself? You may also describe how you interacted with others.",
            },
            {
                "zh": "從這個活動經驗中，你覺得自己發現了什麼能力、優勢線索，或值得帶進大學生活的提醒？",
                "en": "What abilities, possible strengths, or useful reminders for university life did you discover from this experience?",
            },
        ],
    },
}

ACTIVITY_OPTIONS = list(ACTIVITIES.keys())


def activity_display(activity_key: str) -> str:
    activity = ACTIVITIES[activity_key]
    return f"{activity['emoji']} {activity['label_zh']} / {activity['label_en']}"


# =========================================================
# 6. 工具函式 / Utility Functions
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

    return (
        "我有收到你的反思，但這次模型沒有回傳完整文字。可以再試一次。\n"
        "I received your reflection, but the model did not return complete text this time. Please try again."
    )


def test_gemini_api(api_key: str):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(
        (
            "請先用一句自然、活潑、溫暖的繁體中文，歡迎學生使用六色積木 AI 反思小夥伴；"
            "下一行提供一句意思相同、自然簡潔的英文。"
            "不要假設使用者一定正在工作坊現場。"
        ),
        generation_config={
            "temperature": 0.2,
            "max_output_tokens": 180,
        },
    )
    return extract_response_text(response)


def build_activity_prompt(
    activity_key: str,
    nickname: str,
    current_energy: int,
    selected_topic: str,
    answers: list[str],
    bilingual_feedback: bool,
):
    activity = ACTIVITIES[activity_key]

    if activity_key == "other":
        actual_activity_name_zh = (
            st.session_state.custom_activity_name.strip()
            if st.session_state.custom_activity_name.strip()
            else "其他六色積木活動"
        )
        actual_activity_name_en = "Student-specified Six Bricks activity"
    else:
        actual_activity_name_zh = activity["label_zh"]
        actual_activity_name_en = activity["label_en"]

    answer_text = "\n".join(
        (
            f"Q{i + 1} 中文：{activity['questions'][i]['zh']}\n"
            f"Q{i + 1} English: {activity['questions'][i]['en']}\n"
            f"A{i + 1}: {answers[i].strip()}"
        )
        for i in range(len(answers))
    )

    topic_zh = TOPICS[selected_topic]["zh"]
    topic_en = TOPICS[selected_topic]["en"]

    if bilingual_feedback:
        output_instruction = """
【輸出語言 / Output Language】
請每一個段落都先提供繁體中文，再緊接著提供自然、簡潔的英文翻譯。
Do not add extra sections beyond the requested format.

【請使用以下格式 / Required Format】

🧱 從你的描述中，我看見你可能展現：
（繁體中文：指出 1–2 項 VIA 優勢，並簡述具體依據。）
From your reflection, you may be showing:
(English: name the same 1–2 VIA strengths and briefly explain the evidence.)

🌱 這份優勢可以怎麼帶進大學生活：
（繁體中文：連結到人際、學業、生涯或自我照顧。）
How these strengths may support your university life:
(English translation.)

✨ 如果你願意，可以試試這一小步：
（繁體中文：提供一個五分鐘內可開始的小行動。）
If you would like, try this small next step:
(English translation.)
"""
    else:
        output_instruction = """
【輸出語言】
請只使用自然的繁體中文回覆。

【請使用以下格式回覆】

🧱 從你的描述中，我看見你可能展現：
（指出 1 到 2 項 VIA 優勢，並用一句話說明依據。）

🌱 這份優勢可以怎麼帶進大學生活：
（連結到人際、學業、生涯或自我照顧。）

✨ 如果你願意，可以試試這一小步：
（提供一個五分鐘內可以開始的小行動。）
"""

    return f"""
你是「六色新生小夥伴 / Six Bricks Freshman Buddy」，一位溫暖、活潑、穩定的大學生工作坊延伸反思陪伴者。

學生可能在工作坊現場使用，也可能在活動結束後回家才使用。請不要假設他此刻一定仍在現場，也不要要求他完成所有活動；只需要根據他現在選擇的一項最有感經驗進行反思。

【核心任務】
1. 根據學生的實際敘述，從完整 VIA 六大美德與 24 項性格優勢中，指出最有具體證據支持的 1 到 2 項優勢。
2. 簡短說明你是從哪些具體反應、行為、想法或互動看見這些優勢。
3. 說明這些優勢如何連結到大學生活的人際、學業、生涯或自我照顧。
4. 提供一個簡單、可行、約五分鐘內可以開始的小行動。

【非常重要】
1. 六色積木的顏色或活動本身不預先對應特定 VIA 美德或優勢。
2. 不要因為活動名稱就直接推測優勢。
3. 只能根據學生實際提供的內容推論，不要憑空稱讚或硬套標籤。
4. 優勢命名需使用 VIA 正式名稱。
5. 請使用「可能展現」、「從你的描述中看見」等審慎措辭，不把 AI 回饋當成正式測驗結果。

【完整 VIA 六大美德與 24 項優勢】
中文：{ALL_VIA_STRENGTHS_ZH}
English: {ALL_VIA_STRENGTHS_EN}

【安全與界線】
1. 不要診斷、不要提供心理治療、不要說教。
2. 不要要求揭露真實姓名、學號、同學姓名或私人個資。
3. 不要自稱心理師或治療師。
4. 如果學生內容出現明顯自傷、輕生、傷害他人的意圖、嚴重絕望或立即安全危機，請停止一般優勢回饋，鼓勵他立即找可信任的人陪伴、聯絡校內諮商輔導資源；若有立即危險，尋求當地緊急服務。

【學生資訊】
暱稱或匿名代碼：{nickname}
此刻的大學生活電量：{current_energy}/10
目前最想探索的主題：{topic_zh} / {topic_en}

【本次活動】
活動名稱：{actual_activity_name_zh} / {actual_activity_name_en}
活動說明：{activity['description_zh']} / {activity['description_en']}

【學生反思】
{answer_text}

{output_instruction}
""".strip()


def generate_with_key(api_key: str, prompt: str):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.3,
            "max_output_tokens": 750,
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
        bilingual_feedback=st.session_state.bilingual_feedback,
    )

    keys_to_try = []
    if st.session_state.active_api_key:
        keys_to_try.append(st.session_state.active_api_key)

    for key in st.session_state.api_keys_list:
        if key not in keys_to_try:
            keys_to_try.append(key)

    if not keys_to_try:
        raise RuntimeError(
            "目前沒有可用的 API Key。請先完成連線測試。 / "
            "No API key is currently available. Please complete the connection test first."
        )

    last_error = None
    for key in keys_to_try:
        try:
            feedback = generate_with_key(key, prompt)
            st.session_state.active_api_key = key
            return feedback
        except Exception as e:
            last_error = e

    raise RuntimeError(
        f"目前所有 API Key 都無法產生回饋。 / All API keys failed to generate feedback. Last error: {last_error}"
    )


def enough_answers(answers: list[str]):
    non_empty = [a.strip() for a in answers if a.strip()]
    total_chars = sum(len(a) for a in non_empty)
    return len(non_empty) >= 2 and total_chars >= 20


# =========================================================
# 7. 自訂樣式 / Custom Styling
# =========================================================
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(180deg, #FFF9FB 0%, #F8FBFF 100%);
    }
    .main .block-container {
        max-width: 800px;
        padding-top: 1.6rem;
        padding-bottom: 3rem;
    }
    .hero-card {
        background: linear-gradient(135deg, #FFF1F7 0%, #EEF8FF 100%);
        border: 1px solid #F4D7E8;
        border-radius: 24px;
        padding: 1.35rem;
        margin-bottom: 1.1rem;
        box-shadow: 0 6px 18px rgba(0,0,0,0.05);
    }
    .hero-badge {
        display: inline-block;
        background: #FFFFFF;
        color: #E76F9A;
        border: 1px solid #F4C7DB;
        border-radius: 999px;
        padding: 0.28rem 0.75rem;
        font-size: 0.88rem;
        font-weight: 700;
        margin-bottom: 0.8rem;
    }
    .hero-title {
        font-size: 2.05rem;
        font-weight: 800;
        color: #2E3141;
        line-height: 1.25;
        margin-bottom: 0.25rem;
    }
    .hero-title-en {
        font-size: 1.15rem;
        font-weight: 700;
        color: #596079;
        margin-bottom: 0.7rem;
    }
    .hero-subtitle {
        font-size: 1.02rem;
        color: #555B6E;
        line-height: 1.75;
    }
    .hero-subtitle-en {
        font-size: 0.94rem;
        color: #72788D;
        line-height: 1.65;
        margin-top: 0.35rem;
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
        margin-bottom: 0.35rem;
    }
    .mini-card-title-en, .result-title-en, .activity-title-en {
        font-size: 0.9rem;
        color: #70778D;
        font-weight: 700;
        margin-bottom: 0.55rem;
    }
    .mini-card-text, .result-text, .activity-meta {
        color: #5B6075;
        line-height: 1.7;
        font-size: 0.96rem;
    }
    .en-text {
        color: #787E91;
        font-size: 0.9rem;
        line-height: 1.6;
        margin-top: 0.3rem;
    }
    .section-title {
        font-size: 1.18rem;
        font-weight: 800;
        color: #3B3F55;
        margin-top: 1.2rem;
        margin-bottom: 0.12rem;
    }
    .section-title-en {
        color: #7A8093;
        font-size: 0.9rem;
        font-weight: 650;
        margin-bottom: 0.55rem;
    }
    .small-tip {
        color: #6B7280;
        font-size: 0.9rem;
        line-height: 1.6;
        margin-top: -0.2rem;
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
        line-height: 1.8;
        font-size: 0.98rem;
    }
    .other-box {
        background: #FFFDF4;
        border: 1px dashed #EBCB75;
        border-radius: 18px;
        padding: 0.9rem 1rem;
        margin: 0.7rem 0 0.8rem 0;
        color: #5D5665;
        line-height: 1.65;
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
        font-size: 0.84rem;
        margin-top: 1.2rem;
        line-height: 1.6;
    }
    @media (max-width: 640px) {
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
            padding-top: 1rem;
        }
        .hero-title {
            font-size: 1.72rem;
        }
        .hero-title-en {
            font-size: 1rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 8. 頁首 / Header
# =========================================================
st.image("brick_icon.png", width=110)

st.markdown(
    f"""
    <div class="hero-card">
        <div class="hero-badge">🧱 測試版 / Beta {APP_VERSION}</div>
        <div class="hero-title">六色新生小夥伴</div>
        <div class="hero-title-en">Six Bricks Freshman Buddy</div>
        <div class="hero-subtitle">
            這是六色積木工作坊的 <b>選配延伸反思工具</b>。<br>
            你可以在工作坊現場使用，也可以先收藏連結，回家有空時再慢慢操作。<br>
            不需要完成所有活動，只要選一個你最有感受或印象最深的活動就可以。
        </div>
        <div class="hero-subtitle-en">
            This is an <b>optional reflection tool</b> for the Six Bricks workshop.<br>
            You can use it during the workshop or return to it later at home.<br>
            You do not need to complete every activity—choose the one that felt most meaningful to you.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.info(
    "Agent 不是工作坊的必做任務，也不是心理測驗；它會依你分享的活動經驗，陪你看看自己可能展現哪些 VIA 優勢。\n\n"
    "This agent is optional and is not a psychological test. It helps you reflect on possible VIA character strengths based on the experience you share.",
    icon="💡",
)


# =========================================================
# 9. 提醒卡 / Before You Begin
# =========================================================
st.markdown('<div class="section-title">使用前的小提醒</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title-en">A Few Notes Before You Begin</div>', unsafe_allow_html=True)

st.markdown(
    """
    <div class="mini-card">
        <div class="mini-card-title">🌷 自由使用</div>
        <div class="mini-card-title-en">Use It at Your Own Pace</div>
        <div class="mini-card-text">
            • 現場不方便操作完全沒關係。<br>
            • 可以回家後再使用。<br>
            • 選一項最有感的活動即可，不必全部做完。
        </div>
        <div class="en-text">
            • It is completely fine if you cannot use it during the workshop.<br>
            • You may come back and use it later at home.<br>
            • Choose one meaningful activity; you do not need to complete them all.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="mini-card">
        <div class="mini-card-title">🔐 隱私提醒</div>
        <div class="mini-card-title-en">Privacy Reminder</div>
        <div class="mini-card-text">
            • 不要輸入真實姓名、學號或他人個資。<br>
            • API Key 請勿貼到群組或公開場所。<br>
            • AI 回饋不是正式心理測驗或診斷。
        </div>
        <div class="en-text">
            • Do not enter your real name, student ID, or another person's private information.<br>
            • Never post your API key in a group chat or public space.<br>
            • AI feedback is not a formal psychological assessment or diagnosis.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander("🌱 VIA 六大美德與 24 項優勢 / VIA 6 Virtues & 24 Character Strengths"):
    st.markdown(
        """
**智慧與知識 / Wisdom & Knowledge**  
創造力 Creativity｜好奇心 Curiosity｜開明思想 Open-Mindedness/Judgment｜喜愛學習 Love of Learning｜觀點 Perspective

**勇氣 / Courage**  
勇敢 Bravery｜堅毅 Perseverance｜正直 Honesty｜生命力 Zest

**人道 / Humanity**  
愛 Love｜仁慈 Kindness｜社交智慧 Social Intelligence

**正義 / Justice**  
公民精神 Teamwork/Citizenship｜公平 Fairness｜領導力 Leadership

**節制 / Temperance**  
寬恕 Forgiveness｜謙遜 Humility｜謹慎 Prudence｜自制力 Self-Regulation

**超越 / Transcendence**  
欣賞美好卓越 Appreciation of Beauty & Excellence｜感恩 Gratitude｜希望 Hope｜幽默 Humor｜靈修性 Spirituality

> 六色積木的顏色或活動不會預先綁定某項美德。Agent 會依你的實際描述尋找可能的優勢線索。  
> Six Bricks colors and activities are not pre-assigned to any virtue. The agent infers possible strength clues from what you actually describe.
"""
    )


# =========================================================
# 10. API Key 連線 / Connect Your API Key
# =========================================================
st.markdown('<div class="section-title">第一步：連線你的小夥伴</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title-en">Step 1: Connect to Your AI Buddy</div>', unsafe_allow_html=True)

nickname = st.text_input(
    "幫自己取一個小代號 / Choose a nickname or anonymous code",
    placeholder="例如 / e.g. A001、小磚友、NuuStudent01",
)

api_key_text = st.text_input(
    "請貼上 Gemini API Key（若有多組，請用半形逗號分隔） / Paste your Gemini API key (separate multiple keys with commas)",
    placeholder="AIzaSyxxxxxx, AIzaSyyyyyy",
    type="password",
)

st.markdown(
    '<div class="small-tip">若準備第 2 組備用 Key，建議來自不同 Google Cloud project。<br>'
    'If you prepare a second backup key, it is best to use a different Google Cloud project.</div>',
    unsafe_allow_html=True,
)

privacy_ok = st.checkbox(
    "我了解這是自我反思工具，不是心理治療、診斷或正式優勢測驗；我也不會輸入可識別個資。 / "
    "I understand this is a reflection tool, not psychotherapy, diagnosis, or a formal strengths test, and I will not enter identifiable personal information."
)

keys = parse_api_keys(api_key_text)

if keys:
    st.success(f"已偵測到 {len(keys)} 組 API Key。 / {len(keys)} API key(s) detected.", icon="✨")
    if len(set(keys)) < len(keys):
        st.warning(
            "偵測到重複的 API Key。重複貼上不會增加額度。 / Duplicate API keys detected. Repeating the same key does not increase quota.",
            icon="⚠️",
        )

if st.button(
    "🧱 開始連線我的小夥伴 / Connect to My AI Buddy",
    disabled=not privacy_ok or not keys,
    use_container_width=True,
):
    if not nickname.strip():
        st.error("請先輸入暱稱或匿名代碼。 / Please enter a nickname or anonymous code first.", icon="❗")
    else:
        success = False
        last_error = None

        for i, key in enumerate(keys, start=1):
            try:
                with st.spinner(f"正在測試第 {i} 組 API Key... / Testing API key {i}..."):
                    result = test_gemini_api(key)

                st.session_state.api_ready = True
                st.session_state.nickname = nickname.strip()
                st.session_state.active_api_key = key
                st.session_state.active_key_index = i
                st.session_state.api_keys_list = keys
                st.session_state.last_test_message = result

                st.success("太好了，連線成功！ / Great—connection successful!", icon="🎉")
                with st.chat_message("assistant"):
                    st.write(result)
                st.balloons()
                success = True
                break

            except Exception as e:
                last_error = e
                st.warning(
                    f"第 {i} 組 API Key 連線失敗，準備嘗試下一組。 / API key {i} failed. Trying the next one...",
                    icon="🔄",
                )

        if not success:
            st.session_state.api_ready = False
            st.error(
                f"目前所有 API Key 都無法使用。 / All API keys are currently unavailable. Error: {last_error}",
                icon="😥",
            )


# =========================================================
# 11. 此刻的大學生活電量 / Current University-Life Energy
# =========================================================
if st.session_state.api_ready:
    st.divider()
    st.markdown('<div class="section-title">第二步：此刻的大學生活電量</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title-en">Step 2: Your Current University-Life Energy</div>', unsafe_allow_html=True)

    safe_nickname = html.escape(st.session_state.nickname)
    st.markdown(
        f"""
        <div class="result-card">
            <div class="result-title">🎒 歡迎，{safe_nickname}！</div>
            <div class="result-title-en">Welcome, {safe_nickname}!</div>
            <div class="result-text">
                不論你現在仍在工作坊現場，或已經回家一段時間，都可以從此刻的感受開始。<br>
                這個分數不是測驗，只是幫你停一下，看看自己現在的狀態。
            </div>
            <div class="en-text">
                Whether you are still at the workshop or returning later from home, start with how you feel right now.<br>
                This score is not a test—it is simply a quick check-in with yourself.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.session_state.current_energy = st.slider(
        "如果 0 分是完全沒電，10 分是很有能量與期待，你此刻面對大學生活的電量大約是幾分？ / "
        "If 0 means completely drained and 10 means energized and hopeful, how would you rate your university-life energy right now?",
        min_value=0,
        max_value=10,
        value=int(st.session_state.current_energy),
    )

    topic_keys = list(TOPICS.keys())
    topic_index = topic_keys.index(st.session_state.selected_topic) if st.session_state.selected_topic in topic_keys else 0

    st.session_state.selected_topic = st.radio(
        "如果要把活動經驗和大學生活連起來，你現在最想從哪個方向想想看？ / "
        "If you connect this activity to university life, which direction would you most like to explore?",
        topic_keys,
        index=topic_index,
        format_func=topic_display,
    )

    st.session_state.bilingual_feedback = st.checkbox(
        "AI 回饋也中英並呈 / Show AI feedback in both Chinese and English",
        value=st.session_state.bilingual_feedback,
        help="開啟後會使用較多輸出 token。 Enabling this uses more output tokens.",
    )

    if st.button(
        "🚀 選一個最有感的活動來聊聊 / Choose a Meaningful Activity to Reflect On",
        use_container_width=True,
    ):
        st.session_state.reflection_started = True


# =========================================================
# 12. 活動選擇與反思 / Activity Reflection
# =========================================================
if st.session_state.api_ready and st.session_state.reflection_started:
    st.divider()
    st.markdown('<div class="section-title">第三步：選一個最有感的六色積木活動</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title-en">Step 3: Choose the Six Bricks Activity That Stood Out Most</div>', unsafe_allow_html=True)

    st.info(
        "不需要把所有活動都做一次。請選今天最有感受、印象最深，或現在最想整理的一項即可。\n\n"
        "You do not need to reflect on every activity. Choose the one that felt most meaningful, memorable, or worth exploring now.",
        icon="✨",
    )

    selected_activity_key = st.radio(
        "你想從哪個活動開始？ / Which activity would you like to start with?",
        ACTIVITY_OPTIONS,
        format_func=activity_display,
    )

    selected_activity = ACTIVITIES[selected_activity_key]

    if selected_activity_key == "other":
        st.markdown(
            """
            <div class="other-box">
                ✨ 沒看到你最有感的活動嗎？沒關係！請直接輸入活動名稱，再分享你的經驗。<br>
                <span class="en-text">Don't see the activity that stood out to you? No problem—enter its name and share your experience.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        custom_activity_name = st.text_input(
            "✏️ 請輸入活動名稱 / Enter the activity name",
            placeholder="例如 / e.g. 六色積木平衡挑戰、記憶排列、創意建構...",
            key="custom_activity_name_input",
        )
        st.session_state.custom_activity_name = custom_activity_name.strip()
    else:
        st.session_state.custom_activity_name = ""

    if selected_activity_key == "other" and st.session_state.custom_activity_name:
        display_title_zh = st.session_state.custom_activity_name
        display_title_en = "Your Selected Six Bricks Activity"
    else:
        display_title_zh = selected_activity["label_zh"]
        display_title_en = selected_activity["label_en"]

    st.markdown(
        f"""
        <div class="activity-card">
            <div class="activity-title">{selected_activity['emoji']} {html.escape(display_title_zh)}</div>
            <div class="activity-title-en">{html.escape(display_title_en)}</div>
            <div class="activity-meta">{html.escape(selected_activity['description_zh'])}</div>
            <div class="en-text">{html.escape(selected_activity['description_en'])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-title">第四步：分享 2–3 個你的活動感受</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title-en">Step 4: Share 2–3 Reflections About the Activity</div>', unsafe_allow_html=True)

    answers = []
    for q_index, question in enumerate(selected_activity["questions"], start=1):
        answer = st.text_area(
            f"Q{q_index}. {question['zh']}\n{question['en']}",
            key=f"{selected_activity_key}_q{q_index}",
            height=105,
            placeholder="簡單寫 1–3 句即可，可用中文或英文回答。 / Write 1–3 short sentences in Chinese or English.",
        )
        answers.append(answer)

    st.session_state.activity_answers[selected_activity_key] = answers

    st.markdown(
        '<div class="small-tip">至少回答 2 題、合計約 20 字以上，小夥伴才比較有足夠線索回饋你的優勢。<br>'
        'Please answer at least 2 questions and provide enough detail for the agent to identify possible strengths.</div>',
        unsafe_allow_html=True,
    )

    if st.button(
        f"✨ 請小夥伴陪我整理這次經驗 / Help Me Reflect on This Experience",
        use_container_width=True,
    ):
        if selected_activity_key == "other" and not st.session_state.custom_activity_name:
            st.warning("請先輸入活動名稱。 / Please enter the activity name first.", icon="✏️")
        elif not enough_answers(answers):
            st.warning(
                "請至少回答 2 題，並多提供一點點活動線索。 / Please answer at least 2 questions and provide a little more detail.",
                icon="📝",
            )
        else:
            try:
                with st.spinner(
                    "小夥伴正在從你的描述中整理可能的優勢線索... / Identifying possible strength clues from your reflection..."
                ):
                    feedback = generate_activity_feedback(selected_activity_key, answers)
                st.session_state.activity_feedback[selected_activity_key] = feedback
                st.success(
                    "整理完成！這是依你目前分享內容得到的反思，不是正式測驗結果。 / Reflection complete. This is not a formal assessment result.",
                    icon="🌟",
                )
            except Exception as e:
                st.error(
                    f"這次產生回饋時遇到問題。 / There was a problem generating feedback: {e}",
                    icon="😥",
                )

    if selected_activity_key in st.session_state.activity_feedback:
        st.markdown('<div class="section-title">小夥伴給你的優勢反思</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title-en">Your Strengths Reflection</div>', unsafe_allow_html=True)

        feedback_html = html.escape(
            st.session_state.activity_feedback[selected_activity_key]
        ).replace("\n", "<br>")

        st.markdown(
            f'<div class="feedback-card">{feedback_html}</div>',
            unsafe_allow_html=True,
        )
        st.caption(
            "這些是依你分享的活動經驗推測出的可能優勢，並非 VIA 正式量表測驗結果。 / "
            "These are possible strengths inferred from your reflection, not results from the official VIA assessment."
        )


# =========================================================
# 13. 無 API Key 備援反思 / Reflect Without AI
# =========================================================
st.divider()
st.markdown('<div class="section-title">暫時不使用 AI 也沒關係</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title-en">It Is Fine to Reflect Without AI</div>', unsafe_allow_html=True)

with st.expander("📝 先用自己的手機筆記想一想 / Reflect in Your Own Notes First"):
    st.markdown(
        """
如果現在不方便使用 Agent，可以先記下三件事：  
If using the agent is inconvenient right now, write down these three things first:

1. **今天哪一個六色積木活動讓我最有感受或印象？**  
   **Which Six Bricks activity felt most meaningful or memorable to me?**

2. **那個過程中，我做了什麼、想到什麼、感受到什麼？**  
   **What did I do, think, and feel during that experience?**

3. **這個經驗讓我看到自己可能有什麼能力或優勢？**  
   **What abilities or possible strengths did this experience help me notice?**

之後有空時，再回到這個 Agent，把這些筆記貼進來一起整理即可。  
When you have time later, return to this agent and use your notes to continue the reflection.
"""
    )


# =========================================================
# 14. Footer
# =========================================================
st.markdown(
    f'<div class="footer-note">測試版 / Beta {APP_VERSION}<br>'
    '六色積木 × VIA 優勢 × 大學生活反思 AI Agent<br>'
    'Six Bricks × VIA Character Strengths × University-Life Reflection AI Agent<br>'
    'Gemini 3.5 Flash-Lite</div>',
    unsafe_allow_html=True,
)
