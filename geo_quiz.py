import streamlit as st
import csv
import random
from collections import defaultdict

# ===== ページ設定 =====
st.set_page_config(page_title="市区町村クイズ", page_icon="🗾", layout="centered")

# ===== カスタムCSS（モダンテーマ）=====
st.markdown(
    """
    <style>
    /* 全体の背景 */
    .stApp {
        background: linear-gradient(160deg, #eef2ff 0%, #f8fafc 45%, #ecfeff 100%);
    }
    /* メインコンテナの横幅を少し締める */
    .block-container {
        max-width: 760px;
        padding-top: 2.2rem;
    }
    /* 見出しフォント */
    h1, h2, h3 { letter-spacing: .02em; }

    /* ヒーローカード */
    .hero {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #06b6d4 100%);
        border-radius: 24px;
        padding: 2.6rem 1.8rem;
        text-align: center;
        color: #fff;
        box-shadow: 0 18px 40px -12px rgba(99,102,241,.55);
        margin-bottom: 1.6rem;
    }
    .hero .emoji { font-size: 3.4rem; line-height: 1; }
    .hero h1 {
        color: #fff; font-size: 2.1rem; font-weight: 800;
        margin: .5rem 0 .4rem;
    }
    .hero p { color: rgba(255,255,255,.92); font-size: 1.02rem; margin: 0; }

    /* 統計バッジ */
    .stat-row { display: flex; gap: .8rem; margin: 1.1rem 0 0; }
    .stat {
        flex: 1; background: rgba(255,255,255,.16);
        border: 1px solid rgba(255,255,255,.25);
        border-radius: 14px; padding: .7rem .4rem;
        backdrop-filter: blur(4px);
    }
    .stat .num { font-size: 1.45rem; font-weight: 800; color: #fff; }
    .stat .lbl { font-size: .78rem; color: rgba(255,255,255,.85); }

    /* セクションカード */
    .card {
        background: #fff; border-radius: 18px; padding: 1.4rem 1.4rem 1.1rem;
        box-shadow: 0 8px 24px -14px rgba(15,23,42,.25);
        border: 1px solid #eef2f7; margin-bottom: 1.2rem;
    }

    /* ボタンを大きく丸く */
    .stButton > button {
        border-radius: 14px;
        font-weight: 700;
        padding: .65rem 1rem;
        border: 1px solid #e2e8f0;
        transition: transform .06s ease, box-shadow .12s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px -10px rgba(99,102,241,.5);
    }
    /* primaryボタン（スタート等）をグラデーションに */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        border: none; color: #fff; font-size: 1.05rem;
    }

    /* 進捗バー色 */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #6366f1, #06b6d4);
    }

    /* 出題カードの市区町村名 */
    .quiz-city {
        background: #fff; border-radius: 20px; text-align: center;
        padding: 2rem 1rem; margin: .4rem 0 1rem;
        box-shadow: 0 10px 30px -16px rgba(15,23,42,.3);
        border: 1px solid #eef2f7;
    }
    .quiz-city .name { font-size: 2.6rem; font-weight: 800; color: #1e293b; }
    .quiz-city .name ruby rt {
        font-size: .9rem; font-weight: 600; color: #6366f1;
        letter-spacing: .04em; margin-bottom: .15rem;
    }
    .quiz-city .sub { color: #64748b; font-size: .95rem; margin-top: .3rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

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
if not st.session_state.started:
    # 件数を事前計算
    n_shi = len([d for d in ALL_DATA if d["city"].endswith("市")])
    n_all = len(ALL_DATA)

    # --- ヒーロー ---
    st.markdown(
        f"""
        <div class="hero">
            <div class="emoji">🗾</div>
            <h1>市区町村クイズ</h1>
            <p>表示された市区町村が、どの都道府県にあるかを4択で当てよう！</p>
            <div class="stat-row">
                <div class="stat"><div class="num">{TOTAL_QUESTIONS}</div><div class="lbl">問 出題</div></div>
                <div class="stat"><div class="num">4</div><div class="lbl">択クイズ</div></div>
                <div class="stat"><div class="num">47</div><div class="lbl">都道府県</div></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- モード選択カード ---
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("🎯 出題モードを選んでください")
        mode = st.radio(
            "モード",
            ["市のみ", "市区町村すべて"],
            captions=[
                f"「〇〇市」だけを出題（やさしめ）・全国 {n_shi} 件",
                f"市・区・町・村すべてを出題（むずかしめ）・全国 {n_all} 件",
            ],
            label_visibility="collapsed",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    n = n_shi if mode == "市のみ" else n_all
    st.caption(f"📍 全国 {n} 件からランダムで {TOTAL_QUESTIONS} 問出題します。")

    if st.button("▶ スタート", type="primary", use_container_width=True):
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
        city_html = f'🏙 <ruby>{q["city"]}<rt>{q["yomi"]}</rt></ruby>'
    else:
        city_html = f'🏙 {q["city"]}'
    st.markdown(
        f"""
        <div class="quiz-city">
            <div class="name">{city_html}</div>
            <div class="sub">この市区町村はどの都道府県にある？</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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
