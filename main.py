import discord
import google.generativeai as genai
import os
from flask import Flask
from threading import Thread

# ＝＝＝ Renderで24時間動かすためのWebサーバー設定 ＝＝＝
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is awake and running!"

def run():
    # Renderが指定するポートでWebサーバーを起動
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    # ボットの裏側でWebサーバーを動かし続ける処理
    t = Thread(target=run)
    t.start()

# ＝＝＝ ボットの基本設定 ＝＝＝
# セキュリティ対策：Renderの「環境変数（安全な金庫）」から鍵を読み込みます
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TARGET_CHANNEL_ID = 123456789012345678  # ※ここは後で実際のチャンネルIDの数字に変更します

# Geminiの初期設定（ペルソナ設計）
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
    'gemini-1.5-flash',
    system_instruction="あなたは「びーの鯖」のサポートアシスタントです。明るく親しみやすい口調で、ApexやVALORANTなどのゲームの話題にも楽しく乗ってください。"
)

# Discordの初期設定
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'{client.user} としてDiscordにログインしました！')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # ① 専用チャンネルの場合（メンション不要）
    if message.channel.id == TARGET_CHANNEL_ID:
        async with message.channel.typing():
            response = model.generate_content(message.content)
            await message.channel.send(response.text)
        return

    # ② それ以外のチャンネルの場合（メンション必須）
    if client.user in message.mentions:
        async with message.channel.typing():
            prompt = message.content.replace(f'<@{client.user.id}>', '').strip()
            if not prompt:
                await message.channel.send("呼びましたか？何でも聞いてくださいね！")
                return
            response = model.generate_content(prompt)
            await message.channel.send(response.text)

# ＝＝＝ ボットの起動処理 ＝＝＝
# 先にWebサーバーを立ち上げてから、Discordボットを起動します
keep_alive()
client.run(DISCORD_TOKEN)
