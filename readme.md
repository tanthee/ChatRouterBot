**Discord Bot "ChatRouter"**

## 1. 概要

チャンネルが膨大なサーバーで、メッセージの送信チャンネルを探す手間を削減するbot

## 2. 動作フロー

- ユーザーは専用のチャンネルにメッセージ・画像を投稿する
- botはその内容を読み取り、適切なチャンネルにメッセージを転送する
- 専用チャンネルに最初に送信したメッセージに対するリプライで、転送先のチャンネルのリンクを送信する

## 3. 技術スタック

- Discord.py
- ルーティングはOpenAI APIの"gpt-5.4-nano"を使用

## 4. 環境変数

APIキーなどは.envから読み出し

| 変数名 | 説明 |
|--------|------|
| BOT_TOKEN | Discord Botのトークン |
| OPENAI_KEY | OpenAI APIキー |
| BASE_CHANNEL_ID | ユーザーが投稿するチャンネルID |

## 5. セットアップ

```bash
# 依存パッケージのインストール
pip install -r requirements.txt

# .envファイルの作成
# BOT_TOKEN=your_bot_token
# OPENAI_KEY=your_openai_key
# BASE_CHANNEL_ID=your_channel_id

# Botの起動
python bot/chatrouter.py
```
