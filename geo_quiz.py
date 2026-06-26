import streamlit as st
import csv
import random
from collections import defaultdict

# ===== ページ設定 =====
st.set_page_config(page_title="Geo Quiz: Japan", page_icon="📍")

# 位置ピン（モノクロSVGアイコン）
PIN_ICON = (
    '<svg width="{size}" height="{size}" viewBox="0 0 24 24" '
    'fill="currentColor" style="vertical-align:-0.12em;margin-right:.2em;">'
    '<path d="M12 2C8.1 2 5 5.1 5 9c0 5.2 7 13 7 13s7-7.8 7-13c0-3.9-3.1-7-7-7z'
    'm0 9.5A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5z"/></svg>'
)


def pin(size):
    return PIN_ICON.format(size=size)


TOTAL_QUESTIONS = 10

ALL_PREFS = [
    "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県", "茨城県", "栃木県", "群馬県",
    "埼玉県", "千葉県", "東京都", "神奈川県", "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県",
    "岐阜県", "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県", "奈良県", "和歌山県",
    "鳥取県", "島根県", "岡山県", "広島県", "山口県", "徳島県", "香川県", "愛媛県", "高知県", "福岡県",
    "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県",
]


# ===== データ読み込み =====
@st.cache_data
def load_cities():
    with open("shikuchoson.csv", "r", encoding="utf-8-sig") as f:
        return [{"pref": r["pref"], "city": r["city"], "yomi": r.get("yomi", "")}
                for r in csv.DictReader(f)]


@st.cache_data
def load_areacodes():
    with open("areacode.csv", "r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


@st.cache_data
def load_stations():
    with open("station_quiz.csv", "r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


# ===== 同名（簡単すぎ）判定 =====
def _pref_core(pref):
    for suf in ("都", "道", "府", "県"):
        if pref.endswith(suf):
            return pref[:-1]
    return pref


def _is_too_easy_city(pref, city):
    core = city
    for suf in ("市", "区", "町", "村"):
        if core.endswith(suf):
            core = core[:-1]
            break
    return core == _pref_core(pref)


# ===== 選択肢生成の共通処理 =====
def _build_choices(correct, exclude):
    exclude = set(exclude) | {correct}
    candidates = [p for p in ALL_PREFS if p not in exclude]
    choices = random.sample(candidates, 3) + [correct]
    random.shuffle(choices)
    return choices


# ===== 問題生成 =====
def make_city_questions(mode):
    all_data = load_cities()
    city_to_prefs = defaultdict(set)
    for d in all_data:
        city_to_prefs[d["city"]].add(d["pref"])

    pool = [d for d in all_data if d["city"].endswith("市")] if mode == "市のみ" else all_data
    pool = [d for d in pool if not _is_too_easy_city(d["pref"], d["city"])]
    picked = random.sample(pool, TOTAL_QUESTIONS)

    questions = []
    for q in picked:
        questions.append({
            "prompt": q["city"], "yomi": q["yomi"], "correct": q["pref"],
            "choices": _build_choices(q["pref"], city_to_prefs[q["city"]]),
            "detail": "",
        })
    return questions


def make_areacode_questions():
    picked = random.sample(load_areacodes(), TOTAL_QUESTIONS)
    questions = []
    for q in picked:
        exclude = set(q["exclude"].split("|")) if q["exclude"] else set()
        detail = f"主な対象地域： {q['cities']}"
        if q["other_cities"]:
            detail += f"\n\n※ この市外局番は次の県でも使われます： {q['other_cities']}"
        questions.append({
            "prompt": q["code"], "yomi": "", "correct": q["pref"],
            "choices": _build_choices(q["pref"], exclude), "detail": detail,
        })
    return questions


def make_station_questions():
    picked = random.sample(load_stations(), TOTAL_QUESTIONS)
    questions = []
    for q in picked:
        exclude = set(q["exclude"].split("|")) if q["exclude"] else set()
        parts = []
        if q.get("address"):
            parts.append(f"住所： {q['address']}")
        if q["companies"]:
            parts.append(f"運営： {q['companies']}")
        if q["lines"]:
            parts.append(f"路線： {q['lines']}")
        detail = "\n\n".join(parts)
        questions.append({
            "prompt": q["name"], "yomi": "", "correct": q["pref"],
            "choices": _build_choices(q["pref"], exclude), "detail": detail,
        })
    return questions


# ===== クイズ定義 =====
QUIZZES = {
    "city": {"emoji": "🗾", "title": "市区町村クイズ",
             "lead": "表示された市区町村が、どの都道府県にあるかを4択で当てよう！全10問。",
             "ask": "この市区町村はどの都道府県にある？", "unit": ""},
    "areacode": {"emoji": "☎", "title": "市外局番クイズ",
                 "lead": "表示された市外局番が、どの都道府県のものかを4択で当てよう！全10問。",
                 "ask": "この市外局番はどの都道府県？", "unit": ""},
    "station": {"emoji": "🚉", "title": "駅名クイズ",
                "lead": "表示された駅が、どの都道府県にあるかを4択で当てよう！全10問。",
                "ask": "この駅はどの都道府県にある？", "unit": "駅"},
}


# ===== セッション初期化 =====
if "quiz" not in st.session_state:
    st.session_state.quiz = None
    st.session_state.started = False


def go_home():
    st.session_state.quiz = None
    st.session_state.started = False


# ===== ホーム =====
st.markdown(f"<h1>{pin(34)}Geo Quiz: Japan</h1>", unsafe_allow_html=True)
st.caption("ジオゲッサー日本マップ練習アプリ")

if st.session_state.quiz is None:
    st.write("挑戦するクイズを選んでください。")
    items = [
        ("city", "市区町村 → どの都道府県かを4択で（ふりがな付き）"),
        ("areacode", "市外局番 → どの都道府県かを4択で（対象地域も表示）"),
        ("station", "駅名 → どの都道府県かを4択で（運営会社・路線も表示）"),
    ]
    for key, desc in items:
        q = QUIZZES[key]
        st.subheader(f"{q['emoji']} {q['title']}")
        st.caption(desc)
        if st.button(f"{q['title']}で遊ぶ", type="primary", use_container_width=True, key=f"start_{key}"):
            st.session_state.quiz = key
            st.rerun()
        st.write("")
    st.stop()

# ===== 選択中クイズ =====
QZ = QUIZZES[st.session_state.quiz]
IS_CITY = st.session_state.quiz == "city"
IS_AREACODE = st.session_state.quiz == "areacode"

st.subheader(f"{QZ['emoji']} {QZ['title']}")
st.write(QZ["lead"])
if st.button("← ホームに戻る"):
    go_home()
    st.rerun()

# ===== スタート画面 =====
if not st.session_state.started:
    if IS_CITY:
        st.markdown("#### 出題モードを選んでください")
        mode = st.radio(
            "モード", ["市のみ", "市区町村すべて"],
            captions=["「〇〇市」だけを出題（やさしめ）", "市・区・町・村すべてを出題（むずかしめ）"],
            label_visibility="collapsed",
        )
        all_data = load_cities()
        n = len([d for d in all_data if d["city"].endswith("市")]) if mode == "市のみ" else len(all_data)
        st.info(f"全国 {n} 件からランダムで {TOTAL_QUESTIONS} 問出題します。")
    else:
        mode = None
        n = len(load_areacodes()) if IS_AREACODE else len(load_stations())
        unit = "市外局番" if IS_AREACODE else "駅"
        st.info(f"全国 {n} 件の{unit}からランダムで {TOTAL_QUESTIONS} 問出題します。")

    if st.button("▶ スタート", type="primary"):
        st.session_state.started = True
        st.session_state.mode = mode
        if IS_CITY:
            st.session_state.questions = make_city_questions(mode)
        elif IS_AREACODE:
            st.session_state.questions = make_areacode_questions()
        else:
            st.session_state.questions = make_station_questions()
        st.session_state.current = 0
        st.session_state.answers = []
        st.rerun()
    st.stop()

# ===== クイズ進行 =====
questions = st.session_state.questions
current = st.session_state.current

if current < TOTAL_QUESTIONS:
    q = questions[current]
    if st.session_state.mode:
        st.caption(f"モード: {st.session_state.mode}")
    st.progress(current / TOTAL_QUESTIONS)
    st.markdown(f"#### 第 {current + 1} 問 / {TOTAL_QUESTIONS}")
    st.write(QZ["ask"])

    if IS_AREACODE:
        st.markdown(f'<h1 style="letter-spacing:.1em;">{pin(34)}{q["prompt"]}</h1>', unsafe_allow_html=True)
    else:
        if q.get("yomi"):
            body = f'<ruby>{q["prompt"]}<rt>{q["yomi"]}</rt></ruby>'
        else:
            body = q["prompt"] + QZ["unit"]
        st.markdown(f'<h2>{pin(30)}{body}</h2>', unsafe_allow_html=True)

    if len(st.session_state.answers) == current:
        cols = st.columns(2)
        for i, choice in enumerate(q["choices"]):
            if cols[i % 2].button(choice, key=f"q{current}_c{i}", use_container_width=True):
                st.session_state.answers.append({
                    "prompt": q["prompt"], "yomi": q["yomi"], "correct": q["correct"],
                    "selected": choice, "is_correct": (choice == q["correct"]), "detail": q["detail"],
                })
                st.rerun()
    else:
        ans = st.session_state.answers[current]
        name = ans["prompt"] + QZ["unit"]
        if ans["is_correct"]:
            st.success(f"⭕ 正解！　{name} は {ans['correct']} です。")
        else:
            st.error(f"❌ 不正解…　あなたの回答: {ans['selected']} ／ 正解は {ans['correct']} です。")
        if ans["detail"]:
            st.info(ans["detail"])

        if st.button("次の問題へ ▶", type="primary"):
            st.session_state.current += 1
            st.rerun()

else:
    answers = st.session_state.answers
    score = sum(1 for a in answers if a["is_correct"])

    st.balloons()
    st.header("🎉 結果発表")
    st.markdown(f"# {score} 点 / {TOTAL_QUESTIONS} 点")

    if score == TOTAL_QUESTIONS:
        st.success("満点！地理マスターですね！")
    elif score >= 7:
        st.success("お見事！かなりの地理通です。")
    elif score >= 4:
        st.info("まずまず！この調子で覚えていきましょう。")
    else:
        st.warning("これから伸びしろたっぷり！復習しよう。")

    st.divider()
    st.subheader("各問題の結果")
    for i, a in enumerate(answers, start=1):
        mark = "⭕" if a["is_correct"] else "❌"
        label = f"**{a['prompt']}{QZ['unit']}**"
        if a.get("yomi"):
            label += f"（{a['yomi']}）"
        if a["is_correct"]:
            st.write(f"{mark} 第{i}問　{label} → {a['correct']}")
        else:
            st.write(f"{mark} 第{i}問　{label} → あなた: {a['selected']} ／ 正解: {a['correct']}")

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔄 もう一度挑戦", type="primary", use_container_width=True):
            st.session_state.started = False
            st.rerun()
    with c2:
        if st.button("🏠 ホームに戻る", use_container_width=True):
            go_home()
            st.rerun()
