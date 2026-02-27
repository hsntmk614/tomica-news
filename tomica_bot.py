import requests
from bs4 import BeautifulSoup
import json
import os

# --- 設定部分 ---
# LINE Notifyのトークンを環境変数から取得します
LINE_NOTIFY_TOKEN = os.environ.get("LINE_TOKEN", "")

# 監視したいサイトのURLリスト（例：タカラトミーモール）
TARGET_URLS = [
    "https://takaratomymall.jp/shop/c/cTomica/",
]

# 過去に通知した情報を記録するファイル
HISTORY_FILE = "tomica_history.json"

def send_line_notify(message):
    """LINEに通知を送る関数"""
    if not LINE_NOTIFY_TOKEN:
        print("LINEトークンが設定されていません。")
        return
        
    line_notify_api = 'https://notify-api.line.me/api/notify'
    headers = {'Authorization': f'Bearer {LINE_NOTIFY_TOKEN}'}
    data = {'message': f'\n{message}'}
    requests.post(line_notify_api, headers=headers, data=data)

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
            # サイトへの負荷を下げるための設定
            headers = {'User-Agent': 'Mozilla/5.0'} 
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            # HTMLを解析
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # リンク(aタグ)から「トミカ」という文字を含むものを探す
            links = soup.find_all('a')
            
            for link in links:
                title = link.text.strip()
                href = link.get('href')
                
                # タイトルに「トミカ」が含まれていて、まだ通知していない場合
                if "トミカ" in title and href:
                    if href.startswith('/'):
                        domain = "/".join(url.split("/")[:3])
                        full_url = domain + href
                    else:
                        full_url = href

                    item_id = full_url 
                    
                    if item_id not in history:
                        # 新しいトミカ情報発見！
                        message = f"🚗 新着トミカ情報！\n{title}\n{full_url}"
                        print(message)
                        send_line_notify(message)
                        
                        history.append(item_id)
                        new_items_found = True
                        
        except Exception as e:
            print(f"エラーが発生しました ({url}): {e}")

    # 履歴を更新（最新の200件だけ保持）
    if new_items_found:
        save_history(history[-200:])
        print("チェック完了。新着情報を通知しました。")
    else:
        print("チェック完了。新着情報はありませんでした。")

if __name__ == "__main__":
    check_new_tomica()
