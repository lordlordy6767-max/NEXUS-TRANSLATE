import os
import re
import threading
import discord
from discord.ext import commands
from dotenv import load_dotenv
from deep_translator import GoogleTranslator, MyMemoryTranslator
from http.server import HTTPServer, BaseHTTPRequestHandler

load_dotenv()

# ===== FAKE WEBSITE FOR RENDER =====
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"<h1>NEXUS TRANSLATE is Online</h1><p>Bot is running</p>")
    def log_message(self, format, *args):
        return

def keep_alive():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"Fake website running on port {port}")

keep_alive()
# ===================================
# ================= CONFIG FROM RENDER ENV =================
TOKEN = os.getenv("DISCORD_TOKEN")

OWNER_IDS = []
raw_owners = os.getenv("OWNER_IDS", "")
if raw_owners:
    OWNER_IDS = [int(x.strip()) for x in raw_owners.split(",") if x.strip().isdigit()]

PREMIUM_GUILDS = set()
raw_premium = os.getenv("PREMIUM_GUILD_IDS", "")
if raw_premium:
    PREMIUM_GUILDS = set([int(x.strip()) for x in raw_premium.split(",") if x.strip().isdigit()])

print(f"[NEXUS TRANSLATE] Owners loaded: {OWNER_IDS}")
print(f"[NEXUS TRANSLATE] Premium guilds loaded: {PREMIUM_GUILDS}")

# ================= BOT SETUP =================
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command("help")

# auto-translate channels: {channel_id: target_lang_code}
auto_channels = {}

# ================= LANGUAGES =================
LANGS = {
    "english": "en", "italian": "it", "spanish": "es", "french": "fr",
    "german": "de", "arabic": "ar", "japanese": "ja", "korean": "ko",
    "chinese": "zh-CN", "hindi": "hi", "portuguese": "pt", "russian": "ru",
    "turkish": "tr", "dutch": "nl", "polish": "pl", "albanian": "sq",
    "romanian": "ro", "greek": "el", "swedish": "sv", "norwegian": "no",
    "danish": "da", "finnish": "fi", "czech": "cs", "ukrainian": "uk",
    "thai": "th", "vietnamese": "vi", "indonesian": "id", "malay": "ms",
    "hebrew": "he", "bengali": "bn", "tamil": "ta", "urdu": "ur"
}

FLAGS = {
    "en": "🇬🇧", "it": "🇮🇹", "es": "🇪🇸", "fr": "🇫🇷", "de": "🇩🇪",
    "ar": "🇸🇦", "ja": "🇯🇵", "ko": "🇰🇷", "zh-CN": "🇨🇳", "hi": "🇮🇳",
    "pt": "🇵🇹", "ru": "🇷🇺", "tr": "🇹🇷", "nl": "🇳🇱", "pl": "🇵🇱",
    "sq": "🇦🇱", "ro": "🇷🇴", "el": "🇬🇷", "sv": "🇸🇪", "no": "🇳🇴"
}

# ================= HELPERS =================
def get_lang_code(name):
    if not name:
        return None
    name = name.lower().strip()
    if name in LANGS:
        return LANGS[name]
    if name in LANGS.values():
        return name
    return None

def do_translate(text, target):
    target = target.lower().strip()
    try:
        return GoogleTranslator(source='auto', target=target).translate(text)
    except Exception:
        try:
            # MyMemory needs codes like en-GB, not en
            mymap = {'en': 'en-GB', 'it': 'it-IT', 'es': 'es-ES', 'fr': 'fr-FR', 'de': 'de-DE', 'pt': 'pt-PT', 'ar': 'ar-SA'}
            mm_target = mymap.get(target, target)
            return MyMemoryTranslator(source='auto', target=mm_target).translate(text)
        except Exception as e:
            return f"Error: {e}"
            
def is_owner_id(user_id):
    return user_id in OWNER_IDS

def is_premium_guild(guild_id):
    return guild_id in PREMIUM_GUILDS

# ================= EVENTS =================
@bot.event
async def on_ready():
    print(f"NEXUS TRANSLATE online as {bot.user} | Guilds: {len(bot.guilds)}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.author.bot:
        return
    if message.content.startswith("!"):
        await bot.process_commands(message)
        return

    # AUTO TRANSLATE - PREMIUM ONLY
    if message.channel.id in auto_channels:
        target = auto_channels[message.channel.id]
        if message.content and len(message.content) > 1:
            translated = do_translate(message.content, target)
            if translated and translated.lower() != message.content.lower():
                try:
                    await message.reply(
                        f"{FLAGS.get(target,'🌍')} **Translated to {target}:** {translated}",
                        mention_author=False
                    )
                except:
                    pass

    await bot.process_commands(message)

# ================= HELP =================
@bot.command(name="help")
async def help_cmd(ctx, *, topic: str = None):
    embed = discord.Embed(
        title="🌍 NEXUS TRANSLATE - Help",
        color=0x00ff88,
        description="Translate any language, any message."
    )
    embed.add_field(
        name="📝 Translate Text",
        value="`!translate come stai in English`\n`!translate hello in Italian`\n`!translate bonjour to Spanish`",
        inline=False
    )
    embed.add_field(
        name="💬 Translate Message",
        value="Reply to a message with:\n`!translate to English`\n\nOr by ID:\n`!translate 123456789012345678 to English`",
        inline=False
    )
    embed.add_field(
        name="🌍 Languages",
        value="`!translate list` / `!langs` - See all 30+ languages\n`!translate detect <text>` - Detect language",
        inline=False
    )
    embed.add_field(
        name="⚡ Auto-Translate [PREMIUM]",
        value="`!translate auto on` - Auto in this channel\n`!translate auto off` - Turn off\n`!translate channel #general to English` - Auto a channel",
        inline=False
    )
    embed.add_field(
        name="💎 Premium",
        value="`!premium check` - Check if server is premium\nFREE = Manual translate unlimited\nPREMIUM = Auto-translate",
        inline=False
    )
    embed.add_field(
        name="👑 Admin",
        value="`!premium give` / `!premium remove` - Owner only\n`!premium-give-id <id>` / `!premium-remove-id <id>` - Owner DM",
        inline=False
    )
    embed.set_footer(text="NEXUS TRANSLATE | Made by NEXUS")
    await ctx.send(embed=embed)

@bot.command(name="t-help", aliases=["translate-help", "thelp"])
async def t_help_alias(ctx):
    await help_cmd(ctx)

# ================= TRANSLATE MAIN =================
@bot.command(name="translate")
async def translate_cmd(ctx, *, args: str = None):
    # CASE 1: Reply to a message -> !translate to English
    if ctx.message.reference and ctx.message.reference.message_id:
        target_text = args or "to English"
        m = re.search(r'to\s+(\w+)', target_text, re.IGNORECASE)
        target_lang = m.group(1) if m else "English"
        code = get_lang_code(target_lang) or "en"
        try:
            original_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            original = original_msg.content
            if not original:
                await ctx.send("That message has no text to translate.")
                return
            translated = do_translate(original, code)
            embed = discord.Embed(title=f"{FLAGS.get(code,'🌍')} Translated to {target_lang.title()}", color=0x00ff88)
            embed.add_field(name="Original", value=original[:1000], inline=False)
            embed.add_field(name="Translated", value=translated[:1000], inline=False)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}")
            await ctx.send(embed=embed)
            return
        except Exception as e:
            await ctx.send(f"Couldn't fetch that message: {e}")
            return

    if not args:
        await ctx.send("Usage: `!translate come stai in English` or reply to a message with `!translate to English`\nType `!help` for all commands.")
        return

    low = args.lower().strip()

    # LIST
    if low in ["list", "langs"]:
        langs_list = ", ".join([k.title() for k in LANGS.keys()])
        await ctx.send(f"**🌍 Languages:**\n{langs_list}\n\nUse: `!translate <text> to <language>`")
        return

    # DETECT
    if low.startswith("detect "):
        text = args[7:].strip()
        await ctx.send(f"Text: `{text}`\nTry: `!translate {text} to English` to translate it.")
        return

    # AUTO ON / OFF
    if low.startswith("auto on"):
        if not is_premium_guild(ctx.guild.id):
            await ctx.send("🔒 Auto-translate is PREMIUM. Manual translate is FREE.\nOwner: `!premium give` to unlock.")
            return
        # optional target: !translate auto on to Italian
        m = re.search(r'to\s+(\w+)', args, re.IGNORECASE)
        code = get_lang_code(m.group(1)) if m else "en"
        if not code:
            code = "en"
        auto_channels[ctx.channel.id] = code
        await ctx.send(f"✅ Auto-translate ON in this channel -> {code} 💎")
        return

    if low.startswith("auto off"):
        auto_channels.pop(ctx.channel.id, None)
        await ctx.send("❌ Auto-translate OFF")
        return

    # CHANNEL AUTO
    if low.startswith("channel "):
        m = re.search(r'<#(\d+)>.*?to\s+(\w+)', args, re.IGNORECASE)
        if m and is_premium_guild(ctx.guild.id):
            ch_id = int(m.group(1))
            code = get_lang_code(m.group(2)) or "en"
            auto_channels[ch_id] = code
            await ctx.send(f"✅ Auto-translate ON for <#{ch_id}> -> {m.group(2).title()} (PREMIUM)")
        else:
            await ctx.send("🔒 Channel auto-translate is PREMIUM. Owner: `!premium give`")
        return

    # MESSAGE ID: !translate 123... to English
    id_match = re.match(r'^(\d{17,19})\s+to\s+(\w+)', args, re.IGNORECASE)
    if id_match:
        msg_id = int(id_match.group(1))
        target_lang = id_match.group(2)
        code = get_lang_code(target_lang) or "en"
        try:
            original_msg = await ctx.channel.fetch_message(msg_id)
            original = original_msg.content
            if not original:
                await ctx.send("That message has no text.")
                return
            translated = do_translate(original, code)
            embed = discord.Embed(title=f"{FLAGS.get(code,'🌍')} Translated to {target_lang.title()}", color=0x00ff88)
            embed.add_field(name="Original", value=original[:1000], inline=False)
            embed.add_field(name="Translated", value=translated[:1000], inline=False)
            await ctx.send(embed=embed)
        except:
            await ctx.send("Message ID not found in this channel.")
        return

    # TEXT: !translate <text> to/in <language>
    m = re.search(r'(.+?)\s+(?:to|in)\s+(\w+)\s*$', args, re.IGNORECASE)
    if not m:
        await ctx.send("Usage: `!translate come stai in English`\nType `!help` for all commands.")
        return

    text = m.group(1).strip()
    target_lang = m.group(2).strip()
    code = get_lang_code(target_lang)
    if not code:
        await ctx.send(f"Language `{target_lang}` not found. Try `!translate list`")
        return

    translated = do_translate(text, code)
    embed = discord.Embed(title=f"🌍 Translated to {target_lang.title()}", color=0x00ff88)
    embed.add_field(name="Original", value=text[:1000], inline=False)
    embed.add_field(name="Translated", value=translated[:1000], inline=False)
    embed.set_footer(text=f"Requested by {ctx.author.display_name} | NEXUS TRANSLATE")
    await ctx.send(embed=embed)

@bot.command(name="langs")
async def langs_cmd(ctx):
    langs_list = ", ".join([k.title() for k in LANGS.keys()])
    await ctx.send(f"**🌍 Languages:**\n{langs_list}")

# ================= PREMIUM =================
@bot.command(name="premium")
async def premium_cmd(ctx, action: str = None):
    if not action:
        await ctx.send("Usage: `!premium check` | `!premium give` | `!premium remove` | `!premium list`")
        return
    action = action.lower()

    if action == "check":
        is_prem = is_premium_guild(ctx.guild.id)
        status = "💎 PREMIUM ✅ - Auto-translate unlocked" if is_prem else "🆓 FREE - Manual translate only, Auto-translate locked"
        await ctx.send(f"**Server:** {ctx.guild.name}\n**Status:** {status}")
        return

    if action == "list":
        if not is_owner_id(ctx.author.id):
            await ctx.send("❌ Only owner can see premium list.")
            return
        if not PREMIUM_GUILDS:
            await ctx.send("No premium servers yet.")
            return
        lst = "\n".join([f"- {gid}" for gid in PREMIUM_GUILDS])
        await ctx.send(f"**💎 Premium Servers:**\n{lst}")
        return

    if action == "give":
        if not is_owner_id(ctx.author.id):
            await ctx.send("❌ Only NEXUS owner can give premium.")
            return
        PREMIUM_GUILDS.add(ctx.guild.id)
        await ctx.send(
            f"✅ **PREMIUM GIVEN** to {ctx.guild.name} 💎\n"
            f"Auto-translate unlocked! Use `!translate auto on`\n"
            f"⚠️ Add this ID to Render Env `PREMIUM_GUILD_IDS` to keep it after restart:\n`{ctx.guild.id}`"
        )
        return

    if action == "remove":
        if not is_owner_id(ctx.author.id):
            await ctx.send("❌ Only NEXUS owner can remove premium.")
            return
        PREMIUM_GUILDS.discard(ctx.guild.id)
        for ch_id in list(auto_channels.keys()):
            ch = bot.get_channel(ch_id)
            if ch and ch.guild and ch.guild.id == ctx.guild.id:
                del auto_channels[ch_id]
        await ctx.send(
            f"❌ **PREMIUM REMOVED** from {ctx.guild.name}\n"
            f"Back to FREE. Auto-translate turned OFF.\n"
            f"⚠️ Remove `{ctx.guild.id}` from Render Env `PREMIUM_GUILD_IDS` too."
        )
        return

    await ctx.send("Unknown: use `!premium check` / `!premium give` / `!premium remove`")

@bot.command(name="premium-give-id")
async def premium_give_id(ctx, guild_id: int = None):
    if not is_owner_id(ctx.author.id):
        await ctx.send("❌ Owner only.")
        return
    if not guild_id:
        await ctx.send("Usage: `!premium-give-id <server ID>`")
        return
    PREMIUM_GUILDS.add(guild_id)
    await ctx.send(f"✅ Premium given to server ID: {guild_id}\n⚠️ Add it to Render Env `PREMIUM_GUILD_IDS` to keep after restart.")

@bot.command(name="premium-remove-id")
async def premium_remove_id(ctx, guild_id: int = None):
    if not is_owner_id(ctx.author.id):
        await ctx.send("❌ Owner only.")
        return
    if not guild_id:
        await ctx.send("Usage: `!premium-remove-id <server ID>`")
        return
    PREMIUM_GUILDS.discard(guild_id)
    await ctx.send(f"❌ Premium removed from server ID: {guild_id}\n⚠️ Remove it from Render Env `PREMIUM_GUILD_IDS` too.")

# ================= RUN =================
if not TOKEN:
    print("ERROR: DISCORD_TOKEN not found in Render Env!")
else:
    bot.run(TOKEN)
