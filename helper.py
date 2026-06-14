import discord
from discord.ext import commands
import asyncio
import os
import re
import datetime
import logging
import aiohttp  # <-- ADD THIS IMPORT
from flask import Flask
from threading import Thread

# --- CONFIGURATION ---
# ⚠️ NEVER hardcode your token in the file! Use environment variables.
# For testing, you can keep it, but switch to os.getenv("BOT_TOKEN") for production.
BOT_TOKEN = ("MTUwOTQ3OTIxMDY0Mzc1NTEyOA.G6PZIm.AisPCMMhGdIrOdBD2T-bnXDCM92WDdmxG34o1w")

TARGET_BOT_ID = 716390085896962058      # Pokétwo
ADMIN_IDS = [1483484788181569758, 876746134352183336, 1489464610565390336]

DEFAULT_TIMEOUT_HOURS = 2
AUTO_FREEZE_ENABLED = True
ALERT_WEBHOOK_URL = ( "https://discord.com/api/webhooks/1515434876944252979/0j5IUVMGsdkIVFL84TOEafumrXo0dbWKz7-oBT8CdYFcshxGCj4HoVjR2YAyFw36byds")

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Flask keep-alive
app = Flask('')
@app.route('/')
def home():
    return "P2 Helper is alive!"

def run():
    port = int(os.environ.get("PORT", 7860))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run, daemon=True)
    t.start()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix=".", intents=intents)

timeout_hours = DEFAULT_TIMEOUT_HOURS

@bot.event
async def on_ready():
    print(f"🚀 [P2 HELPER ONLINE] {bot.user.name} ({bot.user.id})", flush=True)
    logging.info(f"Bot online as {bot.user.name}")
    
    for guild in bot.guilds:
        me = guild.me
        if not me.guild_permissions.moderate_members:
            warning = f"⚠️ Missing 'Timeout Members' permission in {guild.name} (ID: {guild.id})"
            print(warning)
            logging.warning(warning)
            for admin_id in ADMIN_IDS:
                try:
                    admin = await bot.fetch_user(admin_id)
                    await admin.send(f"⚠️ Helper bot missing `Timeout Members` in `{guild.name}`.")
                except:
                    pass
        else:
            print(f"✅ Has permissions in {guild.name}")

# --- FIXED WEBHOOK FUNCTION ---
async def send_webhook_alert(message, alert_type="captcha"):
    """Send an aesthetic black/white themed embed via webhook."""
    if not ALERT_WEBHOOK_URL:
        return

    if alert_type == "captcha":
        # Custom emojis (replace with your own from your server)
        emoji_shield = "<:black_def:1515635832382554267>"   # black/white shield emoji ID
        emoji_warning = "<a:4a:1515635614928601141>" # black/white warning
        emoji_channel = "<a:1223156908853170207:1515636594407641181>" # black/white channel
        emoji_time = "<:79071_starrymoon:1515635746008989826>"       # black/white clock
        emoji_link = "<:questor_pin:1515636330942562318>"       # black/white link
        emoji_action = "<:pyar_black_gun:1515636222360424548>"   # black/white action

        embed = discord.Embed(
            title=f"{emoji_warning} **__CAPTCHA DETECTED__** {emoji_warning}",
            description=f"{emoji_shield} **Server:** `{message.guild.name}`\n"
            color=0x2C2C2C,  # dark grey/black (or 0xFFFFFF for white)
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.add_field(
            name=f"{emoji_channel} Channel",
            value=f"<#{message.channel.id}>\n`{message.channel.id}`",
            inline=False
        )
        embed.add_field(
            name=f"{emoji_time} Time",
            value=f"<t:{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}:F>",
            inline=True
        )
        embed.add_field(
            name=f"{emoji_action} Action",
            value=f"`{'Freezing Pokétwo' if AUTO_FREEZE_ENABLED else 'Alert only'}`",
            inline=True
        )
        embed.add_field(
            name=f"{emoji_link} Solve Link",
            value=f"[Click to solve captcha]({message.jump_url})",
            inline=False
        )
        embed.set_footer(
            text="P2 Helper • Captcha Monitor",
            icon_url=bot.user.display_avatar.url
        )
        embed.set_thumbnail(url="https://i.imgur.com/lcJiglU.jpeg")
        embed.set_image(url="https://i.imgur.com/lcJiglU.jpeg")# optional
        # You can also set an image: embed.set_image(url="...")

    else:
        embed = None

    try:
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(ALERT_WEBHOOK_URL, session=session)
            if embed:
                await webhook.send(embed=embed, username="P2 Helper", avatar_url=bot.user.display_avatar.url)
            else:
                await webhook.send(message_content)
            print("Webhook embed sent.")
    except Exception as e:
        print(f"Webhook error: {e}")

@bot.event
async def on_message(message):
    if message.author.id == bot.user.id:
        return

    if message.author.id == TARGET_BOT_ID:
        low = message.content.lower()
        if "captcha" in low or "verify" in low:
            print(f"🚨 Captcha detected in {message.guild.name}", flush=True)
            logging.info(f"Captcha in {message.guild.name}")

            alert_text = (
                f"🚨 **CAPTCHA ALERT**\n"
                f"**Server:** {message.guild.name}\n"
                f"**Channel:** <#{message.channel.id}> (ID: {message.channel.id})\n"
                f"**Time:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
                f"**Link:** {message.jump_url}\n"
                f"**Action:** {'Freezing Pokétwo' if AUTO_FREEZE_ENABLED else 'Alert only'}"
            )
            await send_webhook_alert(alert_text)

            if AUTO_FREEZE_ENABLED:
                target = message.guild.get_member(TARGET_BOT_ID)
                if not target:
                    target = await message.guild.fetch_member(TARGET_BOT_ID)
                if target:
                    try:
                        duration = datetime.timedelta(hours=timeout_hours)
                        await target.timeout(duration, reason="Helper: Captcha detected")
                        print(f"✅ Frozen Pokétwo for {timeout_hours} hours in {message.guild.name}")
                        logging.info(f"Froze Pokétwo in {message.guild.name} for {timeout_hours}h")
                        await message.channel.send(f"🚨 **Spawns frozen for {timeout_hours} hours** due to captcha. Use `.unfreeze` when solved.")
                    except discord.Forbidden:
                        print(f"❌ Forbidden to timeout in {message.guild.name}")
                    except Exception as e:
                        print(f"Timeout error: {e}")

    await bot.process_commands(message)

# --- ADMIN COMMANDS (unchanged) ---
@bot.command(name="status")
async def status(ctx):
    if ctx.author.id not in ADMIN_IDS:
        return
    target = ctx.guild.get_member(TARGET_BOT_ID)
    if not target:
        target = await ctx.guild.fetch_member(TARGET_BOT_ID)
    if target and target.is_timed_out():
        until = target.timed_out_until
        now = datetime.datetime.now(datetime.timezone.utc)
        remaining = until - now
        minutes = int(remaining.total_seconds() // 60)
        await ctx.send(f"⏳ Pokétwo is timed out for **{minutes} more minutes** (until {until.strftime('%H:%M UTC')}).")
    else:
        await ctx.send("✅ Pokétwo is active (no timeout).")

@bot.command(name="set_timeout")
async def set_timeout(ctx, hours: int):
    if ctx.author.id not in ADMIN_IDS:
        return
    global timeout_hours
    timeout_hours = hours
    await ctx.send(f"⏲️ Future timeouts will be **{hours} hour(s)**.")

@bot.command(name="freeze")
async def manual_freeze(ctx, hours: int = None):
    if ctx.author.id not in ADMIN_IDS:
        return
    duration_hours = hours if hours is not None else timeout_hours
    target = ctx.guild.get_member(TARGET_BOT_ID)
    if not target:
        target = await ctx.guild.fetch_member(TARGET_BOT_ID)
    if target:
        try:
            await target.timeout(datetime.timedelta(hours=duration_hours))
            await ctx.send(f"❄️ Manually froze Pokétwo for **{duration_hours} hour(s)**.")
            logging.info(f"Manual freeze in {ctx.guild.name} for {duration_hours}h by {ctx.author}")
        except Exception as e:
            await ctx.send(f"❌ Failed: {e}")

@bot.command(name="unfreeze")
async def unfreeze(ctx):
    if ctx.author.id not in ADMIN_IDS:
        return
    target = ctx.guild.get_member(TARGET_BOT_ID)
    if not target:
        target = await ctx.guild.fetch_member(TARGET_BOT_ID)
    if target and target.is_timed_out():
        await target.timeout(None)
        await ctx.send("✅ **Unfroze** Pokétwo. Spawns will resume normally.")
        logging.info(f"Unfroze Pokétwo in {ctx.guild.name} by {ctx.author}")
    else:
        await ctx.send("ℹ️ Pokétwo is not currently timed out.")

@bot.command(name="servers")
async def list_servers(ctx):
    if ctx.author.id not in ADMIN_IDS:
        return
    servers = [f"{guild.name} (ID: {guild.id})" for guild in bot.guilds]
    await ctx.send(f"📋 **Helper is in {len(servers)} servers:**\n" + "\n".join(servers))

@bot.command(name="ping")
async def ping(ctx):
    if ctx.author.id not in ADMIN_IDS:
        return
    await ctx.send(f"🏓 Pong! `{round(bot.latency * 1000)}ms`")

if __name__ == "__main__":
    keep_alive()
    if BOT_TOKEN:
        bot.run(BOT_TOKEN)
    else:
        print("❌ Missing BOT_TOKEN environment variable.")
