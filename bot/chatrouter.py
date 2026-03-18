import os
import discord
from discord.ext import commands
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")
BASE_CHANNEL_ID = int(os.getenv("BASE_CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
openaiClient = OpenAI(api_key=OPENAI_KEY)


def determineTargetChannel(message: discord.Message, channels: list[discord.TextChannel]) -> discord.TextChannel | None:
    channelInfo = "\n".join([f"- ID: {ch.id}, Name: {ch.name}, Topic: {ch.topic or 'なし'}" for ch in channels])
    
    userContent = message.content
    if message.attachments:
        userContent += f"\n[添付ファイル: {len(message.attachments)}個]"

    prompt = f"""あなたはDiscordのメッセージルーティングbotです。
以下のユーザーメッセージを転送するのに最適なチャンネルを選択してください。

## サーバーのチャンネル一覧:
{channelInfo}

## ユーザーのメッセージ:
{userContent}

## 出力形式:
最も適切なチャンネルのIDのみを出力してください。数字のみで回答してください。"""

    response = openaiClient.chat.completions.create(
        model="gpt-5.4-nano",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=50,
        temperature=0.3
    )

    channelIdStr = response.choices[0].message.content.strip()
    
    try:
        channelId = int(channelIdStr)
        for channel in channels:
            if channel.id == channelId:
                return channel
    except ValueError:
        pass

    return None


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.channel.id != BASE_CHANNEL_ID:
        return

    guild = message.guild
    if not guild:
        return

    textChannels = [ch for ch in guild.text_channels if ch.id != BASE_CHANNEL_ID]

    if not textChannels:
        await message.reply("転送先のチャンネルが見つかりませんでした。")
        return

    targetChannel = determineTargetChannel(message, textChannels)

    if not targetChannel:
        await message.reply("適切な転送先チャンネルを特定できませんでした。")
        return

    files = []
    for attachment in message.attachments:
        file = await attachment.to_file()
        files.append(file)

    try:
        forwardedMessage = await targetChannel.send(content=message.content, files=files if files else None)
        jumpUrl = forwardedMessage.jump_url
        await message.reply(f"メッセージを転送しました: {jumpUrl}")
    except discord.Forbidden:
        await message.reply(f"チャンネル「{targetChannel.name}」への転送権限がありません。")
    except Exception as e:
        await message.reply(f"転送中にエラーが発生しました: {str(e)}")


if __name__ == "__main__":
    bot.run(BOT_TOKEN)
