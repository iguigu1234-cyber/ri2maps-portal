import streamlit as st
import database

def show():
    """
    ポータル画面のメイン表示関数。
    動画再生の互換性をさらに高め、URLの不備にも対応しました。
    """
    cat = st.session_state.active_cat
    
    # --- ヘッダー ---
    st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 20px; margin-bottom: 10px;">
            <div style="background-color: #ffedd5; padding: 15px; border-radius: 15px; color: #f97316;">
                <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93l-2.72-2.72A2 2 0 0 0 5.93 2H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2z"></path>
                </svg>
            </div>
            <h1 style="font-size: 3.5rem; font-weight: 800; color: #334155; margin: 0;">{cat['label']}</h1>
        </div>
        <div style="height: 4px; background-color: #1e3a8a; width: 100%; margin-bottom: 25px;"></div>
    """, unsafe_allow_html=True)

    # 検索機能
    search_query = st.text_input("🔍 カテゴリ内を検索", placeholder="タイトルで検索...", label_visibility="collapsed")

    # 資料登録
    with st.expander(f"➕ {cat['label']}に新規登録", expanded=False):
        with st.form("portal_reg_form", clear_on_submit=True):
            title = st.text_input("タイトル")
            # Firebaseの「ダウンロードURL」を貼る場所
            link_url = st.text_input("動画URL (https://... で始まるトークン付きURLを貼ってください)") if cat['id'] == 'manuals' else None
            uploaded_file = st.file_uploader("ファイルを添付", type=['pdf', 'png', 'jpg', 'xlsx', 'docx', 'pptx', 'mp4'])
            
            if st.form_submit_button("登録"):
                if title:
                    with st.spinner("保存中..."):
                        file_url = database.upload_to_storage(uploaded_file, cat['id']) if uploaded_file else None
                        database.add_portal_item(title, cat['id'], st.session_state.user['name'], file_url, link_url)
                        st.success("登録されました")
                        st.rerun()

    # データ取得
    items = database.get_portal_items(cat['id'])
    if search_query:
        items = [i for i in items if search_query.lower() in (i.get('title') or "").lower()]

    st.markdown("---")
    
    if not items:
        st.info("データがありません")
    else:
        for item in items:
            with st.container():
                c1, c2, c3, c4 = st.columns([4, 2, 1, 1])
                
                # 安全なURL取得
                f_url = item.get('fileUrl') or ""
                l_url = item.get('linkUrl') or ""
                target = str(f_url if f_url else l_url).strip()
                
                # アイコンと動画判定
                is_vid = False
                icon = "📄"
                
                if target:
                    t_low = target.lower()
                    if ".pdf" in t_low: icon = "📕"
                    elif ".xls" in t_low or ".xlsx" in t_low: icon = "📗"
                    elif ".mp4" in t_low or "firebasestorage" in t_low or "youtube" in t_low or "youtu.be" in t_low:
                        icon = "🎥"
                        is_vid = True
                
                c1.markdown(f"{icon} **{item.get('title') or '無題'}**")
                
                ts = item.get('updatedAt')
                date_str = ts.strftime('%Y/%m/%d') if ts and hasattr(ts, 'strftime') else "---"
                c2.write(f"<small>{date_str}</small>", unsafe_allow_html=True)
                
                if target:
                    c3.link_button("開く", target, use_container_width=True)
                
                if c4.button("🗑️", key=f"del_{item['id']}", use_container_width=True):
                    database.delete_portal_item(item['id'])
                    st.rerun()

                # --- 動画プレビューエリア ---
                if is_vid and target:
                    with st.expander("▶️ 動画プレビューを表示"):
                        # 動画URLが正しいかチェック
                        if not target.startswith("http"):
                            st.error("URLの形式が正しくありません。https:// から始まるURLを登録してください。")
                        else:
                            # st.videoで再生を試みる
                            st.video(target)
                            st.caption("※再生できない場合は、右上の「開く」ボタンから直接動画を確認してください。")
                
                st.divider()