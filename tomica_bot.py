import requests
from bs4 import BeautifulSoup
import json
import os

# --- 設定部分 ---
# GitHubの金庫からLINEの鍵を自動で引き出します
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_USER_ID = os.environ.get("LINE_USER_ID", "")

# 監視したいサイトのURLリスト（例：タカラトミーモール）
TARGET_URLS = [
    "https://takaratomymall.jp/shop/c/cTomica/",
]

# 過去に通知した情報を記録するファイル
HISTORY_FILE = "tomica_history.json"

def send_line_message(message_text):
    """LINEに通知を送る関数 (新しいMessaging API版)"""
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
        print("LINEの鍵が設定されていません。")
        return
        
    endpoint = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "to": LINE_USER_ID,
        "messages": [
            {
                "type": "text",
                "text": message_text
            }
        ]
    }
    
    response = requests.post(endpoint, headers=headers, json=payload)
    if response.status_code != 200:
        print(f"LINE通知エラー: {response.text}")

def load_history():
    """過去の通知履歴を読み込む"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_history(history):
    """通知履歴を保存する"""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)

def check_new_tomica():
    """サイトをチェックして新着があれば通知するメイン処理"""
    print("トミカの最新情報をチェック中...")
    history = load_history()
    new_items_found = False

    for url in TARGET_URLS:
        try:
            headers = {'User-Agent': 'Mozilla/5.0'} 
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a')
            
            for link in links:
                title = link.text.strip()
                href = link.get('href')
                
                if "トミカ" in title and href:
                    if href.startswith('/'):
                        domain = "/".join(url.split("/")[:3])
                        full_url = domain + href
                    else:
                        full_url = href

                    item_id = full_url 
                    
                    if item_id not in history:
                        message = f"🚗 新着トミカ情報！\n{title}\n{full_url}"
                        print(message)
                        send_line_message(message)
                        
                        history.append(item_id)
                        new_items_found = True
                        
        except Exception as e:
            print(f"エラーが発生しました ({url}): {e}")

    if new_items_found:
        save_history(history[-200:])
        print("チェック完了。新着情報を通知しました。")
    else:
        print("チェック完了。新着情報はありませんでした。")

if __name__ == "__main__":
    check_new_tomica()
