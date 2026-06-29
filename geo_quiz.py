import streamlit as st
import csv
import random
import requests
from collections import defaultdict

# ===== ページ設定 =====
st.set_page_config(page_title="Geo Quiz: Japan", page_icon="📍")

# ドット絵風フォント（タイトル・見出し用）
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap');
    html, body, .stApp, .stApp * { font-family:'Noto Sans JP', sans-serif; }
    </style>
    """,
    unsafe_allow_html=True,
)

# 位置ピン（モノクロSVGアイコン）
# モノクロアイコン（24x24, currentColorで塗り。白い部分は窓などの抜き）
ICON_MARKUP = {
    # 位置ピン（タイトル左）
    "pin": ("<path d='M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"
            "m0 9.5a2.5 2.5 0 1 1 0-5 2.5 2.5 0 0 1 0 5z'/>"),
    # ビル（市区町村）
    "city": ("<path d='M4 21V4h10v17H4z'/><path d='M14 9h6v12h-6z'/>"
             "<rect x='6' y='6' width='2' height='2' fill='#fff'/>"
             "<rect x='10' y='6' width='2' height='2' fill='#fff'/>"
             "<rect x='6' y='10' width='2' height='2' fill='#fff'/>"
             "<rect x='10' y='10' width='2' height='2' fill='#fff'/>"
             "<rect x='6' y='14' width='2' height='2' fill='#fff'/>"
             "<rect x='10' y='14' width='2' height='2' fill='#fff'/>"
             "<rect x='16' y='12' width='2' height='2' fill='#fff'/>"
             "<rect x='16' y='16' width='2' height='2' fill='#fff'/>"),
    # 電車（駅名）
    "station": ("<path d='M12 2c-4 0-8 .5-8 4v9.5C4 17.43 5.57 19 7.5 19L6 20.5v.5h12v-.5"
                "L16.5 19c1.93 0 3.5-1.57 3.5-3.5V6c0-3.5-3.58-4-8-4zM7.5 17c-.83 0-1.5-.67-1.5-1.5"
                "S6.67 14 7.5 14s1.5.67 1.5 1.5S8.33 17 7.5 17zM11 10H6V6h5v4zm2 0V6h5v4h-5z"
                "m3.5 7c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5z'/>"),
    # 電話の受話器（市外局番）
    "areacode": ("<path d='M6.62 10.79a15.15 15.15 0 0 0 6.59 6.59l2.2-2.2a1 1 0 0 1 1.02-.24"
                 " 11.36 11.36 0 0 0 3.57.57 1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4"
                 "a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1c0 1.24.2 2.45.57 3.57a1 1 0 0 1-.24 1.02"
                 "l-2.21 2.2z'/>"),
    # クリップボード（マスタ）
    "master": ("<path d='M9 2a1 1 0 0 0-1 1H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V5"
               "a2 2 0 0 0-2-2h-2a1 1 0 0 0-1-1H9zm0 2h6v2H9V4zM7 10h10v2H7v-2zm0 4h10v2H7v-2z"
               "m0 4h7v2H7v-2z'/>"),
    # 吹き出し（開発者への要望）
    "feedback": ("<path d='M4 3h16a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H9l-5 4v-4H4"
                 "a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2zm3 5v2h10V8H7zm0 4v2h7v-2H7z'/>"),
}


def _svg(key, size):
    return (f"<svg width='{size}' height='{size}' viewBox='0 0 24 24' fill='currentColor' "
            f"style='vertical-align:-0.18em;margin-right:.3em;'>{ICON_MARKUP[key]}</svg>")


def pin(size):
    return _svg("pin", size)


def quiz_icon(key, size):
    return _svg(key, size)


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


# ===== 投稿機能（Supabase REST 連携）=====
def _sb():
    try:
        return st.secrets["SUPABASE_URL"].rstrip("/"), st.secrets["SUPABASE_KEY"]
    except Exception:
        return None, None


def sb_enabled():
    u, k = _sb()
    return bool(u and k)


def _sb_headers(extra=None):
    _, k = _sb()
    h = {"apikey": k, "Authorization": f"Bearer {k}"}
    if extra:
        h.update(extra)
    return h


def sb_select(table, query=""):
    u, k = _sb()
    if not u:
        return []
    try:
        r = requests.get(f"{u}/rest/v1/{table}?{query}", headers=_sb_headers(), timeout=10)
        return r.json() if r.ok else []
    except Exception:
        return []


def sb_insert(table, row):
    u, k = _sb()
    if not u:
        return False
    try:
        r = requests.post(f"{u}/rest/v1/{table}",
                          headers=_sb_headers({"Content-Type": "application/json",
                                               "Prefer": "return=minimal"}),
                          json=row, timeout=10)
        return r.ok
    except Exception:
        return False


def sb_delete(table, row_id):
    u, k = _sb()
    if not u:
        return False
    try:
        r = requests.delete(f"{u}/rest/v1/{table}?id=eq.{row_id}",
                            headers=_sb_headers({"Prefer": "return=minimal"}), timeout=10)
        return r.ok
    except Exception:
        return False


def admin_pw():
    try:
        return st.secrets.get("ADMIN_PASSCODE", "")
    except Exception:
        return ""


# 簡易モデレーション
NG_WORDS = ["http://", "https://", "www.", "ｈｔｔｐ"]  # スパムURL等。必要に応じて追記。


def moderate(text, maxlen):
    t = (text or "").strip()
    if not t:
        return None, "内容が空です。"
    if len(t) > maxlen:
        return None, f"{maxlen}文字以内で入力してください。"
    low = t.lower()
    for w in NG_WORDS:
        if w and w in low:
            return None, "リンクや不適切な内容は投稿できません。"
    return t, ""


def clean_author(name):
    return ((name or "").strip() or "名無し")[:20]


@st.cache_data(ttl=20)
def load_user_trivia():
    rows = sb_select("trivia_posts", "select=type,key,pref,trivia,author&order=id.asc")
    d = {}
    for r in rows:
        d.setdefault((r.get("type"), r.get("key"), r.get("pref")), []).append(
            (r.get("trivia", ""), r.get("author") or "名無し"))
    return d


def get_user_trivia(typ, key, pref):
    return load_user_trivia().get((typ, key, pref), [])


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
    f'<h1>{pin(30)}Geo Quiz: Japan</h1></a>',
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

    st.write("")
    st.markdown(f'<h3>{quiz_icon("feedback", 24)}開発者への要望</h3>', unsafe_allow_html=True)
    st.caption("アプリへの要望・感想を投稿できます（だれでも閲覧できます）。")
    if st.button("要望を見る・投稿する", use_container_width=True, key="open_feedback"):
        st.session_state.quiz = "feedback"
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

    st.divider()
    st.markdown("#### このマスタにTriviaを投稿する")
    if not sb_enabled():
        st.info("投稿機能は現在準備中です（データベース未接続）。")
    else:
        with st.form("post_trivia", clear_on_submit=True):
            tlabel = st.selectbox("種別", ["市区町村", "駅", "市外局番"])
            tpref = st.selectbox("都道府県", ALL_PREFS)
            ttarget = st.text_input("対象（マスタ一覧の表記どおり。例: 横浜市 ／ 渋谷 ／ 045）")
            tbody = st.text_area("Trivia本文（120文字以内）", max_chars=120)
            tauthor = st.text_input("投稿者名（20文字以内・任意）", max_chars=20)
            submitted = st.form_submit_button("投稿する", type="primary")
        if submitted:
            itype = {"市区町村": "city", "駅": "station", "市外局番": "areacode"}[tlabel]
            target = ttarget.strip()
            body, err = moderate(tbody, 120)
            resolved = None
            if itype == "city":
                if any(d["city"] == target and d["pref"] == tpref for d in load_cities()):
                    resolved = (target, tpref)
            elif itype == "station":
                if any(d["name"] == target and d["pref"] == tpref for d in load_stations()):
                    resolved = (target, tpref)
            else:
                for d in load_areacodes():
                    if d["code"] == target:
                        resolved = (target, d["pref"])
                        break
            if err:
                st.error(err)
            elif not resolved:
                st.error("対象が見つかりません。一覧の表記どおりに入力してください"
                         "（市区町村は『○○市』、駅は駅名のみ、市外局番は数字）。")
            else:
                ok = sb_insert("trivia_posts", {
                    "type": itype, "key": resolved[0], "pref": resolved[1],
                    "trivia": body, "author": clean_author(tauthor)})
                if ok:
                    load_user_trivia.clear()
                    st.success("投稿しました。該当クイズの正解画面に表示されます。")
                else:
                    st.error("投稿に失敗しました。時間をおいて再度お試しください。")
    st.stop()

# ===== 開発者への要望（掲示板）=====
if st.session_state.quiz == "feedback":
    st.markdown(f'<h3>{quiz_icon("feedback", 24)}開発者への要望</h3>', unsafe_allow_html=True)
    if st.button("← ホームに戻る"):
        go_home()
        st.rerun()
    st.caption("アプリへの要望・感想を投稿できます。だれでも閲覧できます。")

    if not sb_enabled():
        st.info("投稿機能は現在準備中です（データベース未接続）。")
        st.stop()

    with st.form("post_fb", clear_on_submit=True):
        fbody = st.text_area("要望・感想（300文字以内）", max_chars=300)
        fauthor = st.text_input("投稿者名（20文字以内・任意）", max_chars=20)
        fsub = st.form_submit_button("投稿する", type="primary")
    if fsub:
        body, err = moderate(fbody, 300)
        if err:
            st.error(err)
        elif sb_insert("feedback_posts", {"body": body, "author": clean_author(fauthor)}):
            st.success("投稿しました。")
        else:
            st.error("投稿に失敗しました。時間をおいて再度お試しください。")

    st.divider()
    posts = sb_select("feedback_posts", "select=id,body,author&order=id.desc")
    st.caption(f"{len(posts)} 件の投稿")

    is_admin = False
    with st.expander("管理者用"):
        pw = st.text_input("管理パスコード", type="password")
        if pw and admin_pw() and pw == admin_pw():
            is_admin = True
            st.success("管理者モード：各投稿に削除ボタンが表示されます。")
        elif pw:
            st.error("パスコードが違います。")

    for p in posts:
        with st.container(border=True):
            st.markdown(p.get("body", ""))
            st.caption(f"By {p.get('author') or '名無し'}")
            if is_admin and st.button("削除", key=f"del_fb_{p['id']}"):
                if sb_delete("feedback_posts", p["id"]):
                    st.rerun()
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
        for _body, _author in get_user_trivia(st.session_state.quiz, ans["prompt"], ans["correct"]):
            st.markdown(f"**Trivia**\n\n{_body}")
            st.caption(f"By {_author}")

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
