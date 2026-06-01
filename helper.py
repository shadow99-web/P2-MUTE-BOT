import discord
from discord.ext import commands
import asyncio
import os
import datetime
from flask import Flask
from threading import Thread

# --- CONFIGURATION ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_BOT_TO_TIMEOUT = 716390085896962058  # The bot you want to freeze (e.g., Pokétwo)

# Admin IDs that will receive DM alerts and can run commands
ADMIN_IDS = [
    1378954077462986772,  # Your Main ID
    876746134352183336,
    1489464610565390336
]

# Set up standard bot intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents)


# --- IMPROVED KEEP ALIVE SERVER ---
app = Flask('')

@app.route('/')
def home():
    return "Aura Farmer is active and healthy!"

def run():
    # Render automatically tells the bot which port to use. 
    # If it's not set, we use 10000 (safe for Render).
    port = int(os.environ.get("PORT", 7860))
    try:
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        print(f"⚠️ Flask Server suppressed (likely already running): {e}")

def keep_alive():
    t = Thread(target=run, daemon=True) # daemon=True ensures it dies when main script dies
    t.start()
# --- EVENTS ---
@bot.event
async def on_ready():
    print(f"🚀 [P2 HELPER ONLINE] Logged in as {bot.user.name} ({bot.user.id})", flush=True)

@bot.event
async def on_message(message):
    if message.author.id == bot.user.id:
        return

    # 1. AUTO-TIMEOUT & DM ALERT PROTOCOL
    if message.author.id == TARGET_BOT_TO_TIMEOUT and message.guild:
        low_msg = message.content.lower()
        
        if "captcha" in low_msg or "verify" in low_msg:
            print(f"🚨 [CAPTCHA DETECTED] Spawns freezing in guild: {message.guild.name}", flush=True)
            
            # Direct link to the exact captcha message
            jump_url = message.jump_url 
            
            try:
                # Execute immediate Server Timeout to protect the running incense
                target_member = message.guild.get_member(TARGET_BOT_TO_TIMEOUT)
                if not target_member:
                    target_member = await message.guild.fetch_member(TARGET_BOT_TO_TIMEOUT)
                
                if target_member:
                    duration = datetime.timedelta(hours=24)
                    await target_member.timeout(duration, reason="P2 Helper: Emergency Incense Pause")
                    print("⚡ [FREEZE] Target bot successfully isolated via API timeout.")
                    await message.channel.send("🚨 **SPAWNS FROZEN** 🚨\nCaptcha detected! Spawns paused for 24 hours to save your incense cycle.")
            except discord.Forbidden:
                print("❌ [PERMISSION ERROR] Ensure my role is dragged higher than the target bot's role!")
            except Exception as e:
                print(f"⚠️ Timeout execution failure: {e}")

            # BROADCAST DM ALERTS TO ALL ASSIGNED ADMINS
            for admin_id in ADMIN_IDS:
                try:
                    admin_user = await bot.fetch_user(admin_id)
                    if admin_user:
                        await admin_user.send(
                            f"⚠️ 🔔 **P2 HELPER: DETECTED CAPTCHA ALERT**\n\n"
                            f"📌 **Server:** `{message.guild.name}`\n"
                            f"🔒 **Status:** Target bot timed out for 1 hour to protect your active incense.\n"
                            f"🔗 **Solve Here:** {jump_url}"
                        )
                        print(f"📥 DM notification forwarded successfully to Admin ID: {admin_id}")
                except Exception as dm_err:
                    print(f"❌ Failed sending private broadcast transmission to Admin ID {admin_id}: {dm_err}")

    await bot.process_commands(message)

# --- ADMIN MANUAL COMMANDS ---
@bot.command(name="unfreeze")
async def unfreeze(ctx):
    if ctx.author.id not in ADMIN_IDS:
        return

    if ctx.guild:
        try:
            target_member = ctx.guild.get_member(TARGET_BOT_TO_TIMEOUT)
            if not target_member:
                target_member = await ctx.guild.fetch_member(TARGET_BOT_TO_TIMEOUT)
            
            if target_member and target_member.is_timed_out():
                await target_member.timeout(None, reason="Restored by P2 Helper Admin Command")
                await ctx.send("✅ **Target bot restriction lifted!** Spawns can continue layout updates.")
                print("⚡ [UNFREEZE] Target bot structural restrictions removed.")
            else:
                await ctx.send("ℹ️ Target bot does not possess a system timeout active right now.")
        except Exception as e:
            await ctx.send(f"❌ Handshake failed to clear timeout structure: {e}")

@bot.command(name="ping")
async def ping(ctx):
    if ctx.author.id not in ADMIN_IDS:
        return
    
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 **P2 Helper Pong!** `{latency}ms`")

if __name__ == "__main__":
    keep_alive()
    if BOT_TOKEN:
        try:
            print("🚀 Launching secure connection sequence...", flush=True)
            bot.run(BOT_TOKEN)
        except Exception as e:
            print(f"Fatal Session Boot Error: {e}", flush=True)
    else:
        print("❌ Error: Missing BOT_TOKEN environment variable variable inside Space Settings.", flush=True)
