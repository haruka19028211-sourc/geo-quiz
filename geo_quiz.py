import streamlit as st
import csv
import random
from collections import defaultdict

# ===== ページ設定 =====
st.set_page_config(page_title="Geo Quiz: Japan", page_icon="📍")

# ドット絵風フォント（タイトル・見出し用）
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap');
    html, body, .stApp, .stApp * { font-family:'Noto Sans JP', sans-serif; }
    h1.pix-en, .pix-en, .pix-en * { font-family:'Press Start 2P', monospace !important;
        font-size:1.3rem !important; line-height:1.7 !important; }
    .pixicon { shape-rendering:crispEdges; vertical-align:-0.2em; margin-right:.32em; }
    </style>
    """,
    unsafe_allow_html=True,
)

# 位置ピン（モノクロSVGアイコン）
# ドット絵風アイコン（16x16グリッドの矩形で構成。白い部分は窓などの抜き）
PIXEL_ICONS = {
    # 位置ピン
    "pin": ("<rect x='6' y='2' width='4' height='1'/><rect x='5' y='3' width='6' height='1'/>"
            "<rect x='5' y='4' width='2' height='1'/><rect x='9' y='4' width='2' height='1'/>"
            "<rect x='5' y='5' width='2' height='1'/><rect x='9' y='5' width='2' height='1'/>"
            "<rect x='5' y='6' width='6' height='1'/><rect x='6' y='7' width='4' height='1'/>"
            "<rect x='7' y='8' width='2' height='2'/>"),
    # ビル街（市区町村）
    "city": ("<rect x='2' y='6' width='4' height='8'/><rect x='7' y='3' width='4' height='11'/>"
             "<rect x='12' y='9' width='3' height='5'/>"
             "<rect x='3' y='8' width='2' height='1' fill='#fff'/>"
             "<rect x='3' y='11' width='2' height='1' fill='#fff'/>"
             "<rect x='8' y='5' width='2' height='1' fill='#fff'/>"
             "<rect x='8' y='8' width='2' height='1' fill='#fff'/>"
             "<rect x='8' y='11' width='2' height='1' fill='#fff'/>"),
    # 電車（駅名）
    "station": ("<rect x='3' y='3' width='10' height='9'/>"
                "<rect x='4' y='4' width='3' height='3' fill='#fff'/>"
                "<rect x='9' y='4' width='3' height='3' fill='#fff'/>"
                "<rect x='7' y='9' width='2' height='2' fill='#fff'/>"
                "<rect x='4' y='12' width='2' height='2'/><rect x='10' y='12' width='2' height='2'/>"),
    # 黒電話（市外局番）: 受話器＋本体＋丸ダイヤル
    "areacode": ("<rect x='3' y='1' width='10' height='1'/>"
                 "<rect x='2' y='2' width='2' height='2'/><rect x='12' y='2' width='2' height='2'/>"
                 "<rect x='4' y='4' width='8' height='8'/><rect x='3' y='10' width='10' height='3'/>"
                 "<rect x='6' y='6' width='4' height='4' fill='#fff'/>"
                 "<rect x='7' y='7' width='2' height='2'/>"),
    # クリップボード（マスタ）
    "master": ("<rect x='4' y='2' width='8' height='12'/><rect x='6' y='1' width='4' height='2'/>"
               "<rect x='6' y='5' width='4' height='1' fill='#fff'/>"
               "<rect x='6' y='8' width='4' height='1' fill='#fff'/>"
               "<rect x='6' y='11' width='4' height='1' fill='#fff'/>"),
}


def _pixel_svg(key, size):
    return (f"<svg class='pixicon' width='{size}' height='{size}' viewBox='0 0 16 16' "
            f"fill='currentColor'>{PIXEL_ICONS[key]}</svg>")


def pin(size):
    return _pixel_svg("pin", size)


def quiz_icon(key, size):
    return _pixel_svg(key, size)


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


@st.cache_data
def load_trivia():
    import os
    triv = {}
    if not os.path.exists("trivia.csv"):
        return triv
    with open("trivia.csv", "r", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            triv[(r["type"], r["key"], r["pref"])] = r["trivia"]
    return triv


def get_trivia(typ, key, pref):
    return load_trivia().get((typ, key, pref), "")


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
            "detail": "", "trivia": get_trivia("city", q["city"], q["pref"]),
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
            "trivia": get_trivia("areacode", q["code"], q["pref"]),
        })
    return questions


def make_station_questions():
    pool = [s for s in load_stations() if s.get("quiz_ng") != "1"]
    picked = random.sample(pool, TOTAL_QUESTIONS)
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
            "prompt": q["name"], "yomi": q.get("yomi", ""), "correct": q["pref"],
            "choices": _build_choices(q["pref"], exclude), "detail": detail,
            "trivia": get_trivia("station", q["name"], q["pref"]),
        })
    return questions


# ===== クイズ定義 =====
QUIZZES = {
    "city": {"title": "市区町村クイズ",
             "lead": "表示された市区町村が、どの都道府県にあるかを4択で当てよう！全10問。",
             "ask": "この市区町村はどの都道府県にある？", "unit": ""},
    "areacode": {"title": "市外局番クイズ",
                 "lead": "表示された市外局番が、どの都道府県のものかを4択で当てよう！全10問。",
                 "ask": "この市外局番はどの都道府県？", "unit": ""},
    "station": {"title": "駅名クイズ",
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


# タイトルクリック（?home）でホームへ戻る
if st.query_params.get("home") is not None:
    go_home()
    st.query_params.clear()

# ===== ホーム =====
st.markdown(
    f'<a href="?home=1" target="_self" style="text-decoration:none;color:inherit;">'
    f'<h1 class="pix-en" style="font-family:\'Press Start 2P\',monospace !important;'
    f'font-size:1.3rem;line-height:1.7;">{pin(28)}Geo Quiz: Japan</h1></a>',
    unsafe_allow_html=True,
)
st.markdown('<p class="pix-jp" style="color:#808495;">ジオゲッサー日本マップ練習アプリ</p>',
            unsafe_allow_html=True)

if st.session_state.quiz is None:
    st.write("挑戦するクイズを選んでください。")
    items = [
        ("city", "市区町村 → どの都道府県かを4択で"),
        ("station", "駅名 → どの都道府県かを4択で"),
        ("areacode", "市外局番 → どの都道府県かを4択で"),
    ]
    for key, desc in items:
        q = QUIZZES[key]
        st.markdown(f'<h3 class="pix-jp">{quiz_icon(key, 24)}{q["title"]}</h3>',
                    unsafe_allow_html=True)
        st.caption(desc)
        if st.button(f"{q['title']}で遊ぶ", type="primary", use_container_width=True, key=f"start_{key}"):
            st.session_state.quiz = key
            st.rerun()
        st.write("")

    st.divider()
    st.markdown(f'<h3 class="pix-jp">{quiz_icon("master", 24)}マスタ閲覧</h3>',
                unsafe_allow_html=True)
    st.caption("取り込んでいるデータ（市区町村・市外局番・駅）の一覧を確認できます。")
    if st.button("マスタを閲覧する", use_container_width=True, key="open_master"):
        st.session_state.quiz = "master"
        st.rerun()
    st.stop()

# ===== マスタ閲覧 =====
if st.session_state.quiz == "master":
    st.markdown(f'<h3 class="pix-jp">{quiz_icon("master", 24)}マスタ閲覧</h3>',
                unsafe_allow_html=True)
    if st.button("← ホームに戻る"):
        go_home()
        st.rerun()

    target = st.radio("表示するデータ", ["市区町村", "市外局番", "駅"], horizontal=True)
    kw = st.text_input("キーワード検索（名前・地域などで絞り込み）", "")

    pref_options = ["すべて"] + ALL_PREFS
    pref_sel = st.selectbox("都道府県でしぼり込み", pref_options)

    def _kw_ok(*vals):
        return (not kw) or any(kw in (v or "") for v in vals)

    def _pref_ok(p):
        return pref_sel == "すべて" or p == pref_sel

    table = []
    if target == "市区町村":
        for d in load_cities():
            if not (_pref_ok(d["pref"]) and _kw_ok(d["city"], d["yomi"], d["pref"])):
                continue
            table.append({
                "都道府県": d["pref"], "市区町村": d["city"], "読み": d["yomi"],
                "Trivia": get_trivia("city", d["city"], d["pref"]),
            })
    elif target == "市外局番":
        for d in load_areacodes():
            if not (_pref_ok(d["pref"]) and _kw_ok(d["code"], d["cities"], d["pref"], d["other_cities"])):
                continue
            table.append({
                "市外局番": d["code"], "都道府県": d["pref"], "主な対象地域": d["cities"],
                "他県でも使用": d["other_cities"],
                "Trivia": get_trivia("areacode", d["code"], d["pref"]),
            })
    else:
        for d in load_stations():
            if not (_pref_ok(d["pref"]) and _kw_ok(d["name"], d.get("yomi", ""), d["address"], d["pref"], d["lines"], d["companies"])):
                continue
            table.append({
                "駅名": d["name"], "読み": d.get("yomi", ""), "都道府県": d["pref"],
                "住所": d["address"], "運営": d["companies"], "路線": d["lines"],
                "Trivia": get_trivia("station", d["name"], d["pref"]),
            })

    st.caption(f"{len(table)} 件")
    # 表のツールバー（CSVダウンロード等）を非表示
    st.markdown(
        '<style>[data-testid="stElementToolbar"]{display:none !important;}</style>',
        unsafe_allow_html=True,
    )
    st.dataframe(table, use_container_width=True, hide_index=True)
    st.stop()

# ===== 選択中クイズ =====

# ===== 選択中クイズ =====
QZ = QUIZZES[st.session_state.quiz]
IS_CITY = st.session_state.quiz == "city"
IS_AREACODE = st.session_state.quiz == "areacode"

st.markdown(f'<h3 class="pix-jp">{quiz_icon(st.session_state.quiz, 24)}{QZ["title"]}</h3>',
            unsafe_allow_html=True)
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
            body = f'<ruby>{q["prompt"]}<rt>{q["yomi"]}</rt></ruby>{QZ["unit"]}'
        else:
            body = q["prompt"] + QZ["unit"]
        st.markdown(f'<h2>{pin(30)}{body}</h2>', unsafe_allow_html=True)

    if len(st.session_state.answers) == current:
        cols = st.columns(2)
        for i, choice in enumerate(q["choices"]):
            if cols[i % 2].button(choice, key=f"q{current}_c{i}", use_container_width=True):
                st.session_state.answers.append({
                    "prompt": q["prompt"], "yomi": q["yomi"], "correct": q["correct"],
                    "selected": choice, "is_correct": (choice == q["correct"]),
                    "detail": q["detail"], "trivia": q.get("trivia", ""),
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
        if ans.get("trivia"):
            st.markdown(f"**Trivia**\n\n{ans['trivia']}")
            st.caption("By Claude Opus 4.8")

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
