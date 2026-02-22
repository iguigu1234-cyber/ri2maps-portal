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
    """環境（ローカル/クラウド）に合わせてクライアントを取得"""
    try:
        # 1. Streamlit Cloud の Secrets から読み込みを試行
        if "firebase" in st.secrets:
            key_dict = json.loads(st.secrets["firebase"]["key_json"])
            creds = service_account.Credentials.from_service_account_info(key_dict)
            db = firestore.Client(credentials=creds, project=PROJECT_ID)
            stg = storage.Client(credentials=creds, project=PROJECT_ID)
            return db, stg
        
        # 2. ローカル環境（service-account.jsonがある場合）
        key_path = "service-account.json"
        if os.path.exists(key_path):
            db = firestore.Client.from_service_account_json(key_path)
            stg = storage.Client.from_service_account_json(key_path)
            return db, stg
            
    except Exception as e:
        st.error(f"Firebase接続エラー: {e}")
    return None, None

# --- 以下、他の関数（get_portal_col, upload_to_storage 等）は変更なしでOK ---

def get_portal_col():
    clients = get_clients()
    if not clients: return None
    db, _ = clients
    return db.collection("artifacts").document(APP_ID).collection("public").document("data").collection("documents")

def upload_to_storage(uploaded_file, category_id):
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
    col = get_portal_col()
    if not col: return []
    docs = col.where("categoryId", "==", category_id).stream()
    items = []
    for d in docs:
        data = d.to_dict()
        data['id'] = d.id
        items.append(data)
    # 日付順（新しい順）にソート
    return sorted(items, key=lambda x: x.get('updatedAt') if x.get('updatedAt') else 0, reverse=True)

def delete_portal_item(doc_id):
    col = get_portal_col()
    if col:
        col.document(doc_id).delete()