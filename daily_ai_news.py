#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import feedparser
import smtplib
import json
import os
import sys
import webbrowser
from pathlib import Path
from email.mime.text import MIMEText
from email.utils import formatdate
from datetime import datetime
import hashlib
import re
from html import escape

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "config.json"
OUTPUT_DIR = SCRIPT_DIR / "output"

# 邮箱：优先读环境变量（GitHub Actions Secrets），本地可回退到 config.json
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "")
SENDER_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL", "")
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.qq.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))
SMTP_USE_SSL = os.environ.get("SMTP_USE_SSL", "true").lower() != "false"

RSS_FEEDS = [
    ("MIT AI", "https://www.technologyreview.com/feed/ai/"),
    ("Hacker News (AI)", "https://hnrss.org/frontpage?q=ai"),
    ("机器之心", "https://www.jiqizhixin.com/feed"),
    ("量子位", "https://www.qbitai.com/feed"),
]

MAX_ITEMS_PER_FEED = 5
MAX_TOTAL_ITEMS = 30

IS_CI = os.environ.get("GITHUB_ACTIONS") == "true" or os.environ.get("CI") == "true"


def load_config():
    cfg = {
        "sender_email": SENDER_EMAIL,
        "sender_password": SENDER_PASSWORD,
        "receiver_email": RECEIVER_EMAIL,
        "smtp_server": SMTP_SERVER,
        "smtp_port": SMTP_PORT,
        "smtp_use_ssl": SMTP_USE_SSL,
        "save_local_html": not IS_CI,
        "open_in_browser": not IS_CI,
    }

    if CONFIG_PATH.exists():
        with CONFIG_PATH.open(encoding="utf-8") as f:
            file_cfg = json.load(f)
        for key, value in file_cfg.items():
            if key in ("sender_email", "sender_password", "receiver_email"):
                if not str(cfg.get(key, "")).strip() and value:
                    cfg[key] = value
            elif value is not None and value != "":
                cfg[key] = value

    return cfg


def email_config_ready(cfg):
    return all(str(cfg.get(k, "")).strip() for k in (
        "sender_email", "sender_password", "receiver_email"
    ))


def fetch_news():
    all_entries = []
    seen_hashes = set()

    for source_name, feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:MAX_ITEMS_PER_FEED]:
                title = entry.get("title", "无标题")
                link = entry.get("link", "#")
                summary = entry.get("summary", "")
                clean_summary = re.sub("<[^<]+?>", "", summary)
                if len(clean_summary) > 200:
                    clean_summary = clean_summary[:200] + "…"

                title_hash = hashlib.md5(title.encode("utf-8")).hexdigest()
                if title_hash in seen_hashes:
                    continue
                seen_hashes.add(title_hash)

                all_entries.append(
                    {
                        "source": source_name,
                        "title": title,
                        "link": link,
                        "summary": clean_summary,
                        "published": entry.get(
                            "published",
                            datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT"),
                        ),
                    }
                )
        except Exception as e:
            print(f"抓取 {source_name} 失败: {e}")

    all_entries.sort(key=lambda x: x["published"], reverse=True)
    return all_entries[:MAX_TOTAL_ITEMS]


def build_html_body(news_list):
    today_str = datetime.now().strftime("%Y年%m月%d日")
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI 每日简报 · {today_str}</title>
</head>
<body style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
<h2 style="color:#2c3e50;">🤖 AI 每日简报 · {today_str}</h2>
<p style="color:#7f8c8d;">共收录 {len(news_list)} 条最新动态</p>
<hr>
"""
    for idx, item in enumerate(news_list, 1):
        html += f"""
<div style="margin-bottom: 25px; border-bottom: 1px solid #eee; padding-bottom: 10px;">
    <h3 style="margin:5px 0;"><a href="{item['link']}" style="color:#2980b9; text-decoration:none;">{idx}. {escape(item['title'])}</a></h3>
    <p style="margin:5px 0; color:#555;"><strong>{item['source']}</strong> · {item['published'][:16]}</p>
    <p style="margin:8px 0; color:#333;">{escape(item['summary'])}</p>
</div>
"""
    html += """
<hr>
<p style="color:#95a5a6; font-size:12px;">本简报由自动化脚本每日生成，数据来自公开RSS源。</p>
</body>
</html>"""
    return html


def save_local_html(html_content):
    OUTPUT_DIR.mkdir(exist_ok=True)
    filename = OUTPUT_DIR / f"ai_news_{datetime.now().strftime('%Y-%m-%d')}.html"
    filename.write_text(html_content, encoding="utf-8-sig")
    print(f"本地简报已保存: {filename}")
    return filename.resolve()


def open_html_in_browser(path):
    try:
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            os.system(f'open "{path}"')
        else:
            webbrowser.open(path.as_uri())
    except Exception as e:
        print(f"无法自动打开浏览器：{e}")
        print(f"请手动双击打开：{path}")


def send_email(cfg, html_content):
    msg = MIMEText(html_content, "html", "utf-8")
    msg["From"] = cfg["sender_email"]
    msg["To"] = cfg["receiver_email"]
    msg["Date"] = formatdate(localtime=True)
    msg["Subject"] = f"AI 每日简报 - {datetime.now().strftime('%Y-%m-%d')}"

    server_host = cfg["smtp_server"]
    server_port = int(cfg["smtp_port"])
    use_ssl = bool(cfg.get("smtp_use_ssl", True))

    try:
        if use_ssl:
            with smtplib.SMTP_SSL(server_host, server_port, timeout=30) as server:
                server.login(cfg["sender_email"], cfg["sender_password"])
                server.send_message(msg)
        else:
            with smtplib.SMTP(server_host, server_port, timeout=30) as server:
                server.starttls()
                server.login(cfg["sender_email"], cfg["sender_password"])
                server.send_message(msg)
        print(f"邮件已发送至 {cfg['receiver_email']}")
        return True
    except smtplib.SMTPAuthenticationError:
        print("邮件发送失败：账号或授权码错误。")
        raise SystemExit(1)
    except Exception as e:
        print(f"邮件发送失败：{e}")
        raise SystemExit(1)


def main():
    cfg = load_config()
    print("开始抓取 AI 资讯...")
    news = fetch_news()
    print(f"共抓取到 {len(news)} 条新闻")
    if not news:
        print("无新闻，跳过发送。")
        return

    html_body = build_html_body(news)

    if cfg.get("save_local_html", True):
        local_path = save_local_html(html_body)
        if cfg.get("open_in_browser", True):
            open_html_in_browser(local_path)

    if not email_config_ready(cfg):
        hint = (
            "请设置环境变量 SENDER_EMAIL、SMTP_PASSWORD、RECEIVER_EMAIL，"
            "或在本地 config.json 中填写邮箱信息。"
        )
        print(f"邮件未发送：{hint}")
        raise SystemExit(1)

    send_email(cfg, html_body)


if __name__ == "__main__":
    main()
