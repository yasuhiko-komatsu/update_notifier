# ✅ website_update_checker.py
# 毎朝7時に指定したURLのHTMLを取得・前日と比較し、
# 差分があればメールで通知するPythonスクリプト

import requests
import difflib
import smtplib
from email.mime.text import MIMEText
from email.utils import formatdate
import os
from pathlib import Path
from datetime import datetime

# ----------- 設定 -------------
TARGET_URL = "https://hitohana.tokyo/"
EMAIL_TO = "y.komatsu@domuz.jp"
EMAIL_FROM = os.environ.get("GMAIL_USER")  # Gmailアカウント
EMAIL_PASS = os.environ.get("GMAIL_PASS")  # アプリパスワード推奨
STORAGE_DIR = "./html_snapshots"
THRESHOLD_LINES = 10  # この行数以上の差分があれば通知
# --------------------------------

def fetch_html(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        return f"[ERROR] {e}"

def send_email(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg["Date"] = formatdate()

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_FROM, EMAIL_PASS)
        server.send_message(msg)

def load_previous_snapshot(path):
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""

def save_current_snapshot(path, html):
    path.write_text(html, encoding="utf-8")

def main():
    Path(STORAGE_DIR).mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    snapshot_path = Path(f"{STORAGE_DIR}/snapshot_{today}.html")
    current_html = fetch_html(TARGET_URL)
    if current_html.startswith("[ERROR]"):
        send_email("[ERROR] Webサイト取得失敗", current_html)
        return

    # 前日のファイルを探す
    prev_files = sorted(Path(STORAGE_DIR).glob("snapshot_*.html"))
    prev_html = ""
    if len(prev_files) >= 1:
        prev_html = prev_files[-1].read_text(encoding="utf-8")

    diff = list(difflib.unified_diff(prev_html.splitlines(), current_html.splitlines()))

    if len(diff) >= THRESHOLD_LINES:
        diff_text = "\n".join(diff[:50])  # 長すぎると迷惑なので最大50行に抑える
        subject = "[更新検知] HitoHana トップページが変更されました"
        body = f"URL: {TARGET_URL}\n\n差分の一部:\n\n{diff_text}"
        send_email(subject, body)

    save_current_snapshot(snapshot_path, current_html)

if __name__ == "__main__":
    main()