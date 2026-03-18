import os
import logging
import discord
from discord.ext import commands
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")
BASE_CHANNEL_ID = int(os.getenv("BASE_CHANNEL_ID"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("log/bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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

    logger.info(f"Routing request - Author: {message.author}, Content preview: {message.content[:50]}...")

    response = openaiClient.chat.completions.create(
        model="gpt-5.4-nano",
        messages=[{"role": "user", "content": prompt}],
        max_completion_tokens=50,
        temperature=0.3
    )

    channelIdStr = response.choices[0].message.content.strip()
    logger.info(f"AI response - Channel ID: {channelIdStr}")
    
    try:
        channelId = int(channelIdStr)
        for channel in channels:
            if channel.id == channelId:
                logger.info(f"Target channel found: {channel.name} (ID: {channel.id})")
                return channel
    except ValueError:
        logger.warning(f"Invalid channel ID returned: {channelIdStr}")

    return None


@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    logger.info(f"Base channel ID: {BASE_CHANNEL_ID}")
    logger.info("------")


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.channel.id != BASE_CHANNEL_ID:
        return

    guild = message.guild
    if not guild:
        return

    logger.info(f"Message received - Author: {message.author}, Channel: {message.channel.name}")
    logger.info(f"Message content: {message.content[:100]}{'...' if len(message.content) > 100 else ''}")

    textChannels = [ch for ch in guild.text_channels if ch.id != BASE_CHANNEL_ID]
    logger.info(f"Available channels for routing: {len(textChannels)}")

    if not textChannels:
        logger.error("No target channels available")
        await message.reply("転送先のチャンネルが見つかりませんでした。")
        return

    targetChannel = determineTargetChannel(message, textChannels)

    if not targetChannel:
        logger.error("Failed to determine target channel")
        await message.reply("適切な転送先チャンネルを特定できませんでした。")
        return

    try:
        forwardedMessage = await message.forward(targetChannel)
        logger.info(f"Message forwarded successfully - From: {message.channel.name} To: {targetChannel.name}")
        logger.info(f"Forwarded message URL: {forwardedMessage.jump_url}")
        await message.reply(f"メッセージを転送しました: {forwardedMessage.jump_url}")
    except discord.Forbidden:
        logger.error(f"Permission denied for channel: {targetChannel.name}")
        await message.reply(f"チャンネル「{targetChannel.name}」への転送権限がありません。")
    except Exception as e:
        logger.error(f"Error during forwarding: {str(e)}", exc_info=True)
        await message.reply(f"転送中にエラーが発生しました: {str(e)}")


if __name__ == "__main__":
    bot.run(BOT_TOKEN)
