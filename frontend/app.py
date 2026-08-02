"""
app.py  -  Streamlit website for the TN Agriculture Welfare Schemes portal.

Design goals (based on feedback):
  * Less scrolling  -> the app is split into TABS ("Browse" / "Scheme details")
    using a tab-style selector, so each screen is short.
  * No missing images -> tiles use a colour gradient + a scheme-relevant ICON
    (emoji). Nothing is hot-linked, so nothing can fail to load.
  * Consistent chatbot -> the chat lives in Streamlit's SIDEBAR (the one area
    Streamlit keeps in the exact same place on every screen). By default we
    shift the sidebar to the RIGHT with a little CSS; if that looks odd on your
    Streamlit version, set CHAT_ON_RIGHT = False to use the normal left side.

Pure Streamlit. Talks to the same FastAPI backend.
Run:  streamlit run app.py   (start the backend first:  uvicorn main:app ...)
"""

import os
import html as _html
import requests
import streamlit as st
from translations import T

# --- set this to False if the right-side sidebar looks wrong on your version ---
CHAT_ON_RIGHT = True

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="TN Agriculture Welfare Schemes",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------------------------
if "lang" not in st.session_state:
    st.session_state.lang = "ta"
if "page" not in st.session_state:
    st.session_state.page = "browse"          # "browse" or "detail"
if "selected_scheme" not in st.session_state:
    st.session_state.selected_scheme = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []        # list of (role, text)

# ---------------------------------------------------------------------------
# SCHEME-RELEVANT ICONS (per scheme) + tile colour (per category)
# ---------------------------------------------------------------------------
ICON = {
    "seed-multiplication": "🌱", "paddy-cereals": "🌾", "soil-health-card": "🧪",
    "fig-tanwabe": "🤝", "maize-isopom": "🌽", "pulses-isopom": "🫘",
    "oilseeds-isopom": "🌻", "oilpalm-isopom": "🌴", "cotton-icdp": "🧵",
    "coconut": "🥥", "soil-health": "🪱", "saline-reclamation": "🧂",
    "crop-insurance": "🛡️", "plant-protection": "🐛", "ftc-training": "🎓",
    "seed-village": "🏡", "nfsm-rice": "🍚", "nfsm-pulses": "🫛",
    "atma": "🧑‍🏫", "rkvy-precision": "🎯", "dryland-development": "🏜️",
    "agri-clinic": "🩺", "organic-farming": "🍃",
}
TILE = {
    "Quality Seed Production":        "linear-gradient(135deg,#a1651a,#e0a44b)",
    "Increasing Crop Productivity":   "linear-gradient(135deg,#2e7d32,#7cb342)",
    "Improving Soil Health":          "linear-gradient(135deg,#6d4c2b,#a1887f)",
    "Insurance & Risk Protection":    "linear-gradient(135deg,#7b1fa2,#ab47bc)",
    "Plant Protection":               "linear-gradient(135deg,#558b2f,#9ccc65)",
    "Extension & Training":           "linear-gradient(135deg,#1565c0,#42a5f5)",
    "Seed Programmes":                "linear-gradient(135deg,#8d6e00,#d4a017)",
    "National Food Security Mission": "linear-gradient(135deg,#e07b00,#ffb74d)",
    "RKVY & Development Projects":    "linear-gradient(135deg,#283593,#5c6bc0)",
    "Enterprise & Infrastructure":    "linear-gradient(135deg,#00695c,#26a69a)",
    "Organic Farming":                "linear-gradient(135deg,#33691e,#8bc34a)",
}
def icon_of(s):  return ICON.get(s["id"], "🌾")
def tile_of(s):  return TILE.get(s["category_en"], "linear-gradient(135deg,#2e7d32,#7cb342)")
def esc(x):      return _html.escape(str(x))

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
RIGHT_SIDEBAR_CSS = """
/* move the sidebar (chat) to the RIGHT — experimental, toggle with CHAT_ON_RIGHT */
[data-testid="stAppViewContainer"] { flex-direction: row-reverse; }
section[data-testid="stSidebar"] { border-left: 1px solid #e6e6e6; border-right: none; }
""" if CHAT_ON_RIGHT else ""

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700&family=Inter:wght@400;600;700&family=Noto+Sans+Tamil:wght@400;600;700&display=swap');
html, body, [class*="css"] {{ font-family:'Inter','Noto Sans Tamil',sans-serif; }}
#MainMenu, footer {{ visibility:hidden; }}
.block-container {{ padding-top: 1rem; padding-bottom: 1rem; }}
{RIGHT_SIDEBAR_CSS}

/* remove the sidebar show/hide (collapse) arrow from the chat panel */
[data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"] {{ display:none !important; }}

/* header */
.gov-strip{{background:#4a0e0e;color:#fff;font-size:.78rem;letter-spacing:.5px;padding:5px 16px;border-radius:6px 6px 0 0;}}
.gov-header{{background:#14532d;color:#fff;padding:12px 20px;display:flex;align-items:center;gap:14px;border-bottom:3px solid #d4a017;border-radius:0 0 6px 6px;}}
.gov-emblem{{width:46px;height:46px;border-radius:50%;background:#fff;color:#14532d;display:flex;align-items:center;justify-content:center;font-size:23px;flex-shrink:0;}}
.gov-title{{font-family:'Poppins',sans-serif;font-size:1.25rem;font-weight:700;margin:0;line-height:1.15;}}
.gov-subtitle{{font-size:.86rem;opacity:.9;margin:1px 0 0 0;}}

/* compact hero with SVG field pattern (never a missing image) */
.hero{{position:relative;color:#fff;padding:20px 24px;border-radius:10px;margin:12px 0 4px 0;overflow:hidden;
      background:linear-gradient(120deg,#14532d,#1b7a43);}}
.hero .pat{{position:absolute;inset:0;width:100%;height:100%;opacity:.18;}}
.hero .in{{position:relative;z-index:1;}}
.hero .badge{{display:inline-block;background:#d4a017;color:#3a2a00;font-weight:700;font-size:.68rem;letter-spacing:.5px;padding:3px 12px;border-radius:14px;margin-bottom:7px;}}
.hero h2{{font-family:'Poppins',sans-serif;margin:0 0 3px 0;font-size:1.35rem;}}
.hero p{{margin:0;font-size:.92rem;opacity:.96;max-width:680px;line-height:1.5;}}

.cat-label{{color:#8d6e00;font-weight:700;text-transform:uppercase;letter-spacing:.6px;font-size:.78rem;margin:14px 0 2px 0;}}

/* cards */
.card{{background:#fff;border:1px solid #e4e0d3;border-radius:12px;overflow:hidden;margin-bottom:2px;box-shadow:0 1px 4px rgba(0,0,0,.05);}}
.card .tile{{height:92px;display:flex;align-items:center;justify-content:center;font-size:40px;background:var(--tile);text-shadow:0 2px 6px rgba(0,0,0,.35);}}
.card .cbody{{padding:11px 14px;}}
.card .ccat{{font-size:.68rem;text-transform:uppercase;letter-spacing:.5px;color:#8d6e00;font-weight:700;}}
.card h4{{font-family:'Poppins',sans-serif;margin:3px 0 4px 0;font-size:.96rem;color:#14532d;line-height:1.22;}}
.card .csum{{font-size:.82rem;color:#6b7169;margin:0;min-height:32px;}}

/* detail */
.detail-card{{background:#fff;border:1px solid #e4e0d3;border-radius:12px;padding:22px 26px;box-shadow:0 1px 4px rgba(0,0,0,.05);}}
.detail-card h2{{font-family:'Poppins',sans-serif;color:#14532d;margin-top:0;}}
.badge-cat{{display:inline-block;background:#14532d;color:#fff;font-size:.74rem;padding:3px 12px;border-radius:14px;margin-bottom:10px;}}
.detail-icon{{font-size:30px;margin-right:8px;}}
.field-label{{color:#14532d;font-weight:700;font-size:1.05rem;margin:16px 0 5px 0;}}
.nav-title{{color:#6b7169;text-transform:uppercase;letter-spacing:.6px;font-size:.72rem;font-weight:700;margin:2px 0 6px 0;}}

div.stButton > button{{border-radius:8px;font-weight:600;width:100%;}}

/* tab-style selector (horizontal radio) */
div[role="radiogroup"]{{gap:8px;}}

/* sidebar chat */
.chat-hd{{background:#14532d;color:#fff;padding:10px 13px;border-radius:10px 10px 0 0;display:flex;align-items:center;gap:7px;font-family:'Poppins',sans-serif;font-size:.95rem;}}
.chat-hd .dot{{width:8px;height:8px;border-radius:50%;background:#7bed9f;}}
.chat-hd .on{{margin-left:auto;font-size:.72rem;opacity:.85;font-weight:400;font-family:'Inter';}}
.chat-body{{display:flex;flex-direction:column-reverse;gap:8px;padding:11px;height:calc(100vh - 250px);min-height:160px;overflow-y:auto;background:#f6f7f4;border:1px solid #e4e0d3;border-top:none;border-radius:0 0 10px 10px;}}
.crow{{display:flex;gap:6px;align-items:flex-end;}}
.crow.user{{flex-direction:row-reverse;}}
.av{{width:24px;height:24px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:13px;background:#e2efe6;flex-shrink:0;}}
.crow.user .av{{background:#14532d;}}
.msg{{max-width:80%;padding:7px 10px;border-radius:12px;font-size:.85rem;line-height:1.4;}}
.msg.bot{{background:#fff;border:1px solid #e4e0d3;border-bottom-left-radius:2px;color:#1a1a1a;}}
.msg.user{{background:#14532d;color:#fff;border-bottom-right-radius:2px;}}
.msg .src{{display:block;margin-top:4px;font-size:.74rem;color:#6b7169;font-style:italic;}}

.gov-footer{{background:#0e3d20;color:#dfe8e0;font-size:.82rem;padding:14px 20px;border-radius:8px;margin-top:20px;line-height:1.55;}}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# BACKEND HELPERS
# ---------------------------------------------------------------------------
@st.cache_data(ttl=300)
def fetch_schemes():
    r = requests.get(f"{BACKEND_URL}/api/schemes", timeout=10)
    r.raise_for_status()
    return r.json()["schemes"]

@st.cache_data(ttl=300)
def fetch_scheme(scheme_id):
    r = requests.get(f"{BACKEND_URL}/api/schemes/{scheme_id}", timeout=10)
    r.raise_for_status()
    return r.json()

def ask_chatbot(question, lang, history):
    r = requests.post(f"{BACKEND_URL}/api/chat",
                      json={"question": question, "lang": lang, "history": history},
                      timeout=60)
    r.raise_for_status()
    return r.json()

# ---------------------------------------------------------------------------
# LANGUAGE + shortcuts
# ---------------------------------------------------------------------------
lang = st.session_state.lang
t = T[lang]
def title_of(s):    return s["title_ta"] if lang == "ta" else s["title_en"]
def category_of(s): return s["category_ta"] if lang == "ta" else s["category_en"]
def summary_of(s):  return s["summary_ta"] if lang == "ta" else s["summary_en"]

# Load schemes early (chat + pages need them)
try:
    schemes = fetch_schemes()
except Exception:
    st.error(t["connect_error"])
    st.stop()

# ===========================================================================
# SIDEBAR = CHAT (consistent placement on every screen; shifted right by CSS)
# ===========================================================================
with st.sidebar:
    if not st.session_state.chat_history:
        st.session_state.chat_history.append(("bot", t["chat_welcome"]))

    rows = ""
    for role, text in reversed(st.session_state.chat_history):
        if role == "user":
            rows += (f'<div class="crow user"><div class="av">🧑‍🌾</div>'
                     f'<div class="msg user">{esc(text)}</div></div>')
        else:
            rows += (f'<div class="crow bot"><div class="av">🌾</div>'
                     f'<div class="msg bot">{text}</div></div>')
    st.markdown(f"""
    <div class="chat-hd"><span class="dot"></span>{t["chat_heading"]}
        <span class="on">🟢 online</span></div>
    <div class="chat-body">{rows}</div>
    """, unsafe_allow_html=True)

    with st.form("chat_form", clear_on_submit=True):
        q = st.text_input(t["chat_input"], placeholder=t["chat_input"],
                          label_visibility="collapsed")
        sent = st.form_submit_button("➤  " + ("அனுப்பு" if lang == "ta" else "Send"),
                                     use_container_width=True)

    if sent and q.strip():
        history = []
        for role, text in st.session_state.chat_history:
            if text == t["chat_welcome"]:
                continue
            history.append({"role": "user" if role == "user" else "assistant",
                            "content": text})
        st.session_state.chat_history.append(("user", q))
        with st.spinner(t["chat_thinking"]):
            try:
                result = ask_chatbot(q, lang, history)
                answer = esc(result.get("answer", ""))
                sources = result.get("sources", [])
                if sources:
                    titles = [title_of(x) for sid in sources
                              for x in schemes if x["id"] == sid]
                    if titles:
                        answer += (f'<span class="src">{t["chat_sources"]}: '
                                   + esc("; ".join(titles)) + "</span>")
                st.session_state.chat_history.append(("bot", answer))
            except Exception:
                st.session_state.chat_history.append(("bot", t["connect_error"]))
        st.rerun()

# ===========================================================================
# MAIN  =  header + hero + tab selector + page
# ===========================================================================
# ---- header + language ----
st.markdown(f'<div class="gov-strip">{t["govt_strip"]}</div>', unsafe_allow_html=True)
head_col, lang_col = st.columns([6, 1])
with head_col:
    st.markdown(f"""
    <div class="gov-header">
        <div class="gov-emblem">🌾</div>
        <div>
            <p class="gov-title">{t["portal_title"]}</p>
            <p class="gov-subtitle">{t["portal_subtitle"]}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
with lang_col:
    choice = st.radio(t["lang_label"], options=["ta", "en"],
                      format_func=lambda x: "தமிழ்" if x == "ta" else "English",
                      index=0 if lang == "ta" else 1)
    if choice != st.session_state.lang:
        st.session_state.lang = choice
        st.rerun()

# ---- compact hero ----
st.markdown(f"""
<div class="hero">
    <svg class="pat" viewBox="0 0 100 100" preserveAspectRatio="none">
        <path d="M0 72 Q25 58 50 72 T100 72 V100 H0 Z" fill="#ffffff"/>
        <path d="M0 84 Q25 70 50 84 T100 84 V100 H0 Z" fill="#ffffff" opacity="0.55"/>
    </svg>
    <div class="in">
        <span class="badge">{t["hero_badge"]}</span>
        <h2>{t["hero_title"]}</h2>
        <p>{t["hero_text"]}</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ---- tab-style selector (controls st.session_state.page) ----
PAGES = {"browse": "🏠 " + t["browse_heading"], "detail": "📋 " + t["nav_schemes"]}
picked = st.radio(
    "view", options=list(PAGES.keys()),
    format_func=lambda k: PAGES[k],
    index=list(PAGES.keys()).index(st.session_state.page),
    horizontal=True, label_visibility="collapsed",
)
if picked != st.session_state.page:
    st.session_state.page = picked
    st.rerun()

st.write("")  # small spacer

# ===========================================================================
# PAGE: BROWSE
# ===========================================================================
if st.session_state.page == "browse":
    query = st.text_input("🔍 " + t["search_placeholder"], key="home_search").strip().lower()

    categories = {}
    for s in schemes:
        if query:
            hay = (title_of(s) + " " + summary_of(s) + " " +
                   s["title_en"] + " " + s["title_ta"]).lower()
            if query not in hay:
                continue
        categories.setdefault(s["category_en"], []).append(s)

    if not categories:
        st.info(t["no_results"])

    for cat_en, items in categories.items():
        st.markdown(f'<div class="cat-label">{category_of(items[0])}</div>', unsafe_allow_html=True)
        for i in range(0, len(items), 3):
            row = items[i:i+3]
            cols = st.columns(3)
            for col, s in zip(cols, row):
                with col:
                    st.markdown(f"""
                    <div class="card">
                        <div class="tile" style="--tile:{tile_of(s)}">{icon_of(s)}</div>
                        <div class="cbody">
                            <div class="ccat">{category_of(s)}</div>
                            <h4>{title_of(s)}</h4>
                            <p class="csum">{summary_of(s)}</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(t["view_details"] + " →", key="card_" + s["id"],
                                 use_container_width=True):
                        st.session_state.selected_scheme = s["id"]
                        st.session_state.page = "detail"
                        st.rerun()

# ===========================================================================
# PAGE: DETAIL
# ===========================================================================
else:
    # if no scheme chosen yet, default to the first
    if st.session_state.selected_scheme is None:
        st.session_state.selected_scheme = schemes[0]["id"]

    nav_col, content_col = st.columns([1, 2], gap="medium")

    with nav_col:
        st.markdown(f'<div class="nav-title">{t["all_schemes"]}</div>', unsafe_allow_html=True)
        nav_q = st.text_input("🔍", key="nav_search",
                              placeholder=t["search_placeholder"],
                              label_visibility="collapsed").strip().lower()
        # find which category the selected scheme is in, so ONLY that group
        # opens by default (the rest stay collapsed).
        sel = next((x for x in schemes if x["id"] == st.session_state.selected_scheme), None)
        sel_cat = sel["category_en"] if sel else None

        cats = {}
        for s in schemes:
            cats.setdefault(s["category_en"], []).append(s)
        for cat_en, items in cats.items():
            shown = []
            for s in items:
                if nav_q:
                    hay = (s["title_en"] + s["title_ta"] +
                           s["category_en"] + s["category_ta"]).lower()
                    if nav_q not in hay:
                        continue
                shown.append(s)
            if not shown:
                continue
            open_group = bool(nav_q) or (cat_en == sel_cat)
            with st.expander(f"{category_of(items[0])}  ({len(shown)})", expanded=open_group):
                for s in shown:
                    is_sel = (s["id"] == st.session_state.selected_scheme)
                    label = f"{icon_of(s)}  {title_of(s)}"
                    if st.button(label, key="nav_" + s["id"],
                                 type="primary" if is_sel else "secondary",
                                 use_container_width=True):
                        st.session_state.selected_scheme = s["id"]
                        st.rerun()

    with content_col:
        if st.button(t["back"], key="back_btn"):
            st.session_state.page = "browse"
            st.rerun()

        s = fetch_scheme(st.session_state.selected_scheme)
        title = s["title_ta"] if lang == "ta" else s["title_en"]
        category = s["category_ta"] if lang == "ta" else s["category_en"]
        summary = s["summary_ta"] if lang == "ta" else s["summary_en"]
        benefits = s["benefits_ta"] if lang == "ta" else s["benefits_en"]
        eligibility = s["eligibility_ta"] if lang == "ta" else s["eligibility_en"]
        officers = s["officers_ta"] if lang == "ta" else s["officers_en"]
        districts = s.get("districts_en", "")
        ic = ICON.get(s["id"], "🌾")

        b_html = "".join(f"<li>{x}</li>" for x in benefits)
        e_html = "".join(f"<li>{x}</li>" for x in eligibility)
        o_html = "".join(f"<li>{x}</li>" for x in officers)

        st.markdown(f"""
        <div class="detail-card">
            <span class="badge-cat">{t["category"]}: {category}</span>
            <h2><span class="detail-icon">{ic}</span>{title}</h2>
            <p style="color:#444;font-size:1.04rem;">{summary}</p>
            <div class="field-label">✅ {t["benefits"]}</div>
            <ul>{b_html}</ul>
            <div class="field-label">📋 {t["eligibility"]}</div>
            <ul>{e_html}</ul>
            <div class="field-label">👤 {t["officers"]}</div>
            <ul>{o_html}</ul>
            <div class="field-label">📍 {t["districts"]}</div>
            <p>{districts}</p>
        </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# FOOTER
# ---------------------------------------------------------------------------
st.markdown(f'<div class="gov-footer">{t["footer"]}</div>', unsafe_allow_html=True)
