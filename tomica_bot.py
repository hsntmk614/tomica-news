import requests
from bs4 import BeautifulSoup
import json
import os
import xml.etree.ElementTree as ET

# --- 設定部分 ---
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_USER_ID = os.environ.get("LINE_USER_ID", "")

HISTORY_FILE = "tomica_history.json"

def send_line_message(message_text):
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
        "messages": [{"type": "text", "text": message_text}]
    }
    
    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"LINE通知エラー: {response.text}")
    except Exception as e:
        print(f"LINE送信エラー: {e}")

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)

def check_new_tomica():
    print("トミカの最新情報をチェック中...")
    history = load_history()
    new_items_found = False

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    } 

    # --- ① タカラトミー公式 ＆ トミカごーごー のチェック ---
    HTML_TARGETS = [
        "https://takaratomymall.jp/shop/c/cTomica/",
        "https://tomicagogo.com/"  # ←ご指定の最強サイトを追加しました！
    ]

    for url in HTML_TARGETS:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for link in soup.find_all('a'):
                title = link.text.strip()
                href = link.get('href')
                
                # 「トミカ」という文字が含まれるリンクを拾う
                if title and href and "トミカ" in title:
                    if href.startswith('/'):
                        domain = "/".join(url.split("/")[:3])
                        full_url = domain + href
                    else:
                        full_url = href

                    if full_url not in history and full_url.startswith("http"):
                        message = f"🚗 新着トミカ情報！\n{title}\n{full_url}"
                        print(message)
                        send_line_message(message)
                        history.append(full_url)
                        new_items_found = True
        except requests.exceptions.Timeout:
            print(f"通信エラー ({url}): 応答が遅いためスキップしました。")
        except Exception as e:
            print(f"サイトチェックエラー ({url}): {e}")

    # --- ② Googleニュース のチェック ---
    # 「トミカ 特注」「オリジナルトミカ」「トミカ 予約」で検索した最新ニュースを拾います
    GOOGLE_NEWS_URL = "https://news.google.com/rss/search?q=トミカ+特注+OR+オリジナルトミカ+OR+トミカ+予約&hl=ja&gl=JP&ceid=JP:ja"
    try:
        response = requests.get(GOOGLE_NEWS_URL, headers=headers, timeout=10)
        response.raise_for_status()
        
        # ニュース用の特別なデータ(XML)を解読する処理
        root = ET.fromstring(response.text)
        for item in root.findall('.//item'):
            title = item.find('title').text
            link = item.find('link').text
            
            if link not in history:
                message = f"📰 ニュース発見！\n{title}\n{link}"
                print(message)
                send_line_message(message)
                history.append(link)
                new_items_found = True
    except Exception as e:
        print(f"Googleニュースチェックエラー: {e}")

    # --- 保存処理 ---
    if new_items_found:
        save_history(history[-400:]) # 履歴が増えすぎないよう最新400件だけ覚える
        print("チェック完了。新着情報を通知しました。")
    else:
        print("チェック完了。新着情報はありませんでした。")

if __name__ == "__main__":
    check_new_tomica()
