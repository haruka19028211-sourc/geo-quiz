import streamlit as st
import csv
import random
from collections import defaultdict

# ===== ページ設定 =====
st.set_page_config(page_title="市区町村クイズ", page_icon="📍")

# 位置ピン（モノクロSVGアイコン）
PIN_ICON = (
    '<svg width="{size}" height="{size}" viewBox="0 0 24 24" '
    'fill="currentColor" style="vertical-align:-0.12em;margin-right:.2em;">'
    '<path d="M12 2C8.1 2 5 5.1 5 9c0 5.2 7 13 7 13s7-7.8 7-13c0-3.9-3.1-7-7-7z'
    'm0 9.5A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5z"/></svg>'
)


def pin(size):
    return PIN_ICON.format(size=size)


# ===== データ読み込み（最初の1回だけ）=====
@st.cache_data
def load_data():
    data = []
    with open("shikuchoson.csv", "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                "pref": row["pref"],
                "city": row["city"],
                "yomi": row.get("yomi", ""),
            })
    return data

ALL_DATA = load_data()
ALL_PREFS = sorted(set(d["pref"] for d in ALL_DATA))  # 47都道府県
TOTAL_QUESTIONS = 10  # 出題数

# --- 同名の市区町村 → それが存在する都道府県のリスト ---
# 例: "府中市" → ["東京都", "広島県"]
CITY_TO_PREFS = defaultdict(list)
for d in ALL_DATA:
    CITY_TO_PREFS[d["city"]].append(d["pref"])


# ===== 問題を10問生成する関数 =====
def make_questions(mode):
    # モードに応じて出題プールを絞る
    if mode == "市のみ":
        pool = [d for d in ALL_DATA if d["city"].endswith("市")]
    else:  # 市区町村すべて
        pool = ALL_DATA

    picked = random.sample(pool, TOTAL_QUESTIONS)
    questions = []
    for q in picked:
        city = q["city"]
        yomi = q.get("yomi", "")
        correct = q["pref"]

        # ★同名対策★
        # この市区町村名を持つ「すべての都道府県」を除外対象にする。
        # こうすれば、選択肢に「同名の別の正解」が混ざらない。
        same_name_prefs = set(CITY_TO_PREFS[city])

        # ダミー選択肢の候補 = 全都道府県から、同名を持つ県をすべて除いたもの
        candidates = [p for p in ALL_PREFS if p not in same_name_prefs]
        wrong3 = random.sample(candidates, 3)

        choices = wrong3 + [correct]
        random.shuffle(choices)
        questions.append({
            "city": city,
            "yomi": yomi,
            "correct": correct,
            "choices": choices,
        })
    return questions


# ===== セッション初期化 =====
if "started" not in st.session_state:
    st.session_state.started = False

# ===== スタート画面 =====
st.markdown(
    f"<h1>{pin(36)}市区町村クイズ</h1>",
    unsafe_allow_html=True,
)
st.write("表示された市区町村が、どの都道府県にあるかを4択で当てよう！全10問。")

if not st.session_state.started:
    # --- モード選択 ---
    st.subheader("出題モードを選んでください")
    mode = st.radio(
        "モード",
        ["市のみ", "市区町村すべて"],
        captions=[
            "「〇〇市」だけを出題（やさしめ）",
            "市・区・町・村すべてを出題（むずかしめ）",
        ],
        label_visibility="collapsed",
    )

    # 出題プールの件数を表示
    if mode == "市のみ":
        n = len([d for d in ALL_DATA if d["city"].endswith("市")])
    else:
        n = len(ALL_DATA)
    st.info(f"全国 {n} 件からランダムで {TOTAL_QUESTIONS} 問出題します。")

    if st.button("▶ スタート", type="primary"):
        st.session_state.started = True
        st.session_state.mode = mode
        st.session_state.questions = make_questions(mode)
        st.session_state.current = 0
        st.session_state.answers = []
        st.rerun()
    st.stop()

# ===== クイズ進行 =====
questions = st.session_state.questions
current = st.session_state.current

if current < TOTAL_QUESTIONS:
    q = questions[current]

    st.caption(f"モード: {st.session_state.mode}")
    st.progress(current / TOTAL_QUESTIONS)
    st.subheader(f"第 {current + 1} 問 / {TOTAL_QUESTIONS}")

    if q.get("yomi"):
        city_html = f'<ruby>{q["city"]}<rt>{q["yomi"]}</rt></ruby>'
    else:
        city_html = q["city"]
    st.markdown(
        f'<h2>{pin(30)}{city_html}</h2>',
        unsafe_allow_html=True,
    )
    st.write("この市区町村はどの都道府県にある？")

    if len(st.session_state.answers) == current:
        cols = st.columns(2)
        for i, choice in enumerate(q["choices"]):
            if cols[i % 2].button(choice, key=f"q{current}_c{i}", use_container_width=True):
                st.session_state.answers.append({
                    "city": q["city"],
                    "yomi": q.get("yomi", ""),
                    "correct": q["correct"],
                    "selected": choice,
                    "is_correct": (choice == q["correct"]),
                })
                st.rerun()
    else:
        ans = st.session_state.answers[current]
        if ans["is_correct"]:
            st.success(f"⭕ 正解！　{ans['city']} は {ans['correct']} です。")
        else:
            st.error(f"❌ 不正解…　あなたの回答: {ans['selected']} ／ 正解は {ans['correct']} です。")

        if st.button("次の問題へ ▶", type="primary"):
            st.session_state.current += 1
            st.rerun()

else:
    answers = st.session_state.answers
    score = sum(1 for a in answers if a["is_correct"])

    st.balloons()
    st.header("🎉 結果発表")
    st.caption(f"モード: {st.session_state.mode}")
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
        label = f"**{a['city']}**"
        if a.get("yomi"):
            label += f"（{a['yomi']}）"
        if a["is_correct"]:
            st.write(f"{mark} 第{i}問　{label} → {a['correct']}")
        else:
            st.write(f"{mark} 第{i}問　{label} → あなた: {a['selected']} ／ 正解: {a['correct']}")

    st.divider()
    if st.button("🔄 もう一度挑戦", type="primary"):
        st.session_state.started = False
        st.rerun()
