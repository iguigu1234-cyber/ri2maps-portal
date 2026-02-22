import streamlit as st
from google.cloud import firestore, storage
from google.oauth2 import service_account
import json
import os
from datetime import datetime

# Firebase設定
PROJECT_ID = "mybulletinboard-6e716"
BUCKET_NAME = "mybulletinboard-6e716.firebasestorage.app"
APP_ID = "mybulletinboard-6e716"

@st.cache_resource
def get_clients():
    """Secretsから認証情報を読み込み、クライアントを生成"""
    try:
        # Streamlit Cloud の Secrets を確認
        if "firebase" in st.secrets:
            key_info = st.secrets["firebase"]["key_json"]
            
            # key_json が文字列(str)ならJSONとしてパース、すでに辞書(dict)ならそのまま使う
            if isinstance(key_info, str):
                key_dict = json.loads(key_info)
            else:
                key_dict = key_info
                
            creds = service_account.Credentials.from_service_account_info(key_dict)
            db = firestore.Client(credentials=creds, project=PROJECT_ID)
            stg = storage.Client(credentials=creds, project=PROJECT_ID)
            return db, stg
        
        # ローカル環境用（ファイルがある場合）
        key_path = "service-account.json"
        if os.path.exists(key_path):
            db = firestore.Client.from_service_account_json(key_path)
            stg = storage.Client.from_service_account_json(key_path)
            return db, stg
            
    except Exception as e:
        # エラー内容を画面に出すためにあえて表示（公開時は消すのが望ましい）
        st.error(f"【Firebase接続エラー】: {e}")
    return None, None

def get_portal_col():
    """ドキュメント用コレクション取得"""
    clients = get_clients()
    if not clients: return None
    db, _ = clients
    # 正しいコレクションパス：artifacts/APP_ID/public/data/documents
    return db.collection("artifacts").document(APP_ID).collection("public").document("data").collection("documents")

def upload_to_storage(uploaded_file, category_id):
    """Storageにファイルをアップロード"""
    clients = get_clients()
    if not clients or not uploaded_file: return None
    _, stg = clients
    bucket = stg.bucket(BUCKET_NAME)
    file_path = f"portal/{category_id}/{datetime.now().strftime('%Y%m%d%H%M%S')}_{uploaded_file.name}"
    blob = bucket.blob(file_path)
    blob.upload_from_string(uploaded_file.getvalue(), content_type=uploaded_file.type)
    try:
        blob.make_public()
        return blob.public_url
    except:
        return f"https://storage.googleapis.com/{BUCKET_NAME}/{file_path}"

def add_portal_item(title, category_id, user_name, file_url=None, link_url=None):
    """資料情報をFirestoreに登録"""
    col = get_portal_col()
    if col:
        col.add({
            "title": title,
            "categoryId": category_id,
            "userName": user_name,
            "fileUrl": file_url,
            "linkUrl": link_url,
            "updatedAt": firestore.SERVER_TIMESTAMP
        })

def get_portal_items(category_id):
    """資料リスト取得（エラー回避処理付き）"""
    col = get_portal_col()
    if col is None: return []
    try:
        docs = col.where("categoryId", "==", category_id).stream()
        items = []
        for d in docs:
            data = d.to_dict()
            data['id'] = d.id
            items.append(data)
        return sorted(items, key=lambda x: x.get('updatedAt', 0) if x.get('updatedAt') else 0, reverse=True)
    except Exception as e:
        st.warning(f"データ取得中にエラーが発生しました: {e}")
        return []

def delete_portal_item(doc_id):
    """資料削除"""
    col = get_portal_col()
    if col:
        col.document(doc_id).delete()