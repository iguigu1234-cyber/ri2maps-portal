import streamlit as st
import view_portal

# ページ基本設定
st.set_page_config(page_title="RI2MAPS ポータル", layout="wide")

# UIデザイン
st.markdown("""
    <style>
    [data-testid="stSidebar"] div.stButton > button {
        height: 55px; font-weight: bold; font-size: 1.0rem !important;
        margin-bottom: 8px; border: 1px solid #cbd5e1; background-color: white;
        color: #475569; text-align: left; justify-content: flex-start;
        padding-left: 20px;
    }
    .main .block-container { padding-top: 2rem; max-width: 1200px; }
    </style>
""", unsafe_allow_html=True)

# セッション管理
if 'user' not in st.session_state:
    st.session_state.user = {"name": "井口 均", "office": "本部"}
if 'active_cat' not in st.session_state:
    st.session_state.active_cat = {"id": "news", "label": "新着情報"}

# --- サイドバー ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user['name']} 様")
    st.divider()
    
    menu = [
        {"id": "news", "label": "新着情報", "icon": "🔔"},
        {"id": "manuals", "label": "マニュアル解説動画", "icon": "🎥"},
        {"id": "cases", "label": "RI2MAPS活用事例", "icon": "💡"},
        {"id": "qa", "label": "Q＆A", "icon": "💬"},
    ]
    
    for item in menu:
        label = f"{item['icon']} {item['label']}"
        if st.session_state.active_cat['id'] == item['id']:
            label = f"▶️ {label}"
        if st.button(label, use_container_width=True):
            st.session_state.active_cat = item
            st.rerun()

# --- メインコンテンツ呼び出し ---
view_portal.show()