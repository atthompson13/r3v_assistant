import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import os
import asyncio

# ----------------------------
# Load .env variables
# ----------------------------
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
RECRUITER_ROLE_ID = int(os.getenv("RECRUITER_ROLE_ID"))  # ID of Recruiter role
DIRECTOR_ROLE_ID = int(os.getenv("DIRECTOR_ROLE_ID"))    # ID of Director role

# ----------------------------
# Intents
# ----------------------------
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# ----------------------------
# Bot setup
# ----------------------------
bot = commands.Bot(command_prefix="!", intents=intents)

# ----------------------------
# Utility: Logging
# ----------------------------
async def log_action(guild: discord.Guild, message: str):
    log_channel = discord.utils.get(guild.text_channels, name="bot-logs")
    if log_channel:
        await log_channel.send(f"📝 {message}")

# ----------------------------
# Bot Ready
# ----------------------------
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"Synced {len(synced)} commands to guild {GUILD_ID}.")
    except Exception as e:
        print(f"❌ Sync error: {e}")

# ----------------------------
# Welcome Message
# ----------------------------
@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="recruitment")
    if channel:
        await channel.send(
            f"👋 Welcome to **Rev3nants Wrath**, {member.mention}!\n\n"
            f"If you're looking to join up, type **/recruit**.\n\n"
            f"If you need to speak with leadership or a diplomat, type **/officer**."
        )
        await log_action(member.guild, f"{member.name} joined the server.")

# ----------------------------
# /recruit Command (5 min cooldown)
# ----------------------------
@bot.tree.command(
    name="recruit",
    description="Open a private recruitment thread.",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.checks.cooldown(1, 300.0, key=lambda i: i.user.id)
async def recruit(interaction: discord.Interaction):
    guild = interaction.guild
    channel = interaction.channel
    thread_name = f"Recruit-{interaction.user.name}"

    # Prevent duplicate threads
    for thread in channel.threads:
        if thread.name == thread_name:
            await interaction.response.send_message(
                "❌ You already have an open recruit thread.", ephemeral=True
            )
            return

    # Respond immediately to prevent interaction timeout
    await interaction.response.send_message(
        "✅ Creating your recruitment thread...", ephemeral=True
    )

    # Create private thread
    thread = await channel.create_thread(
        name=thread_name,
        type=discord.ChannelType.private_thread,
        invitable=False
    )

    # Ping Recruiter role directly
    recruiter_role = guild.get_role(RECRUITER_ROLE_ID)
    ping_text = recruiter_role.mention if recruiter_role else ""
    
    welcome_message = (
        f"{ping_text}\n"
        f"👋 {interaction.user.mention} has started a recruitment thread!\n\n"
        "We're glad you're interested in joining us! To get started, auth all your characters that "
        "you're going to recruit into the corporation with our alliance here: "
        "https://auth.black-rose.space\n\n"
        "Once that's finished, reply back here and let us know your in-game names that you registered. "
        "While you're at it, tell us a little bit about yourself!"
    )

    await thread.send(welcome_message)
    await log_action(guild, f"{interaction.user} created recruitment thread {thread.name}.")

# ----------------------------
# /officer Command (10 min cooldown)
# ----------------------------
@bot.tree.command(
    name="officer",
    description="Open a private thread for officer discussion.",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.checks.cooldown(1, 600.0, key=lambda i: i.user.id)
async def officer(interaction: discord.Interaction):
    guild = interaction.guild
    channel = interaction.channel
    thread_name = f"officer-{interaction.user.name}"

    # Prevent duplicate threads
    for thread in channel.threads:
        if thread.name == thread_name:
            await interaction.response.send_message(
                "❌ You already have an open officer thread.", ephemeral=True
            )
            return

    await interaction.response.send_message(
        "✅ Creating your officer thread...", ephemeral=True
    )

    thread = await channel.create_thread(
        name=thread_name,
        type=discord.ChannelType.private_thread,
        invitable=False
    )

    # Ping Director role directly
    director_role = guild.get_role(DIRECTOR_ROLE_ID)
    ping_text = director_role.mention if director_role else ""

    welcome_message = (
        f"{ping_text}\n"
        f"👋 {interaction.user.mention} has started a thread for officer discussion."
    )

    await thread.send(welcome_message)
    await log_action(guild, f"{interaction.user} created officer thread {thread.name}.")

# ----------------------------
# /close Command (Directors only)
# ----------------------------
@bot.tree.command(
    name="close",
    description="Close the current thread. (Directors only)",
    guild=discord.Object(id=GUILD_ID)
)
async def close(interaction: discord.Interaction):
    director_role = interaction.guild.get_role(DIRECTOR_ROLE_ID)
    if director_role not in interaction.user.roles:
        await interaction.response.send_message(
            "❌ You don’t have permission to use this command.", ephemeral=True
        )
        return

    thread = interaction.channel
    if isinstance(thread, discord.Thread):
        try:
            await thread.edit(archived=True, locked=True)
            await interaction.response.send_message("🗂️ Thread has been closed.", ephemeral=True)
            await log_action(interaction.guild, f"{interaction.user} closed thread {thread.name}.")
        except discord.Forbidden:
            await interaction.response.send_message(
                "⚠️ Cannot close the thread — it might already be archived.", ephemeral=True
            )
    else:
        await interaction.response.send_message(
            "⚠️ This command can only be used inside a thread.", ephemeral=True
        )

# ----------------------------
# /remind Command (Directors only)
# ----------------------------
@bot.tree.command(
    name="remind",
    description="Set a reminder. (Directors only)",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(days="Days until reminder", hours="Hours until reminder", minutes="Minutes until reminder", message="Reminder message")
async def remind(interaction: discord.Interaction, days: int = 0, hours: int = 0, minutes: int = 0, message: str = "Reminder!"):
    director_role = interaction.guild.get_role(DIRECTOR_ROLE_ID)
    if director_role not in interaction.user.roles:
        await interaction.response.send_message(
            "❌ You don’t have permission to use this command.", ephemeral=True
        )
        return

    total_seconds = days * 86400 + hours * 3600 + minutes * 60
    if total_seconds <= 0:
        await interaction.response.send_message("⚠️ Please specify a valid time.", ephemeral=True)
        return

    await interaction.response.send_message(
        f"⏰ Reminder set for {days}d {hours}h {minutes}m from now.", ephemeral=True
    )
    await log_action(interaction.guild, f"{interaction.user} set a reminder for {days}d {hours}h {minutes}m: {message}")

    await asyncio.sleep(total_seconds)
    await interaction.user.send(f"🔔 Reminder: {message}")

# ----------------------------
# Error Handler
# ----------------------------
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CommandOnCooldown):
        remaining = int(error.retry_after)
        minutes, seconds = divmod(remaining, 60)
        await interaction.response.send_message(
            f"⏳ You can use this command again in **{minutes}m {seconds}s**.", ephemeral=True
        )
    else:
        print(f"Unexpected error: {error}")
        try:
            await interaction.response.send_message("⚠️ An unexpected error occurred.", ephemeral=True)
        except:
            pass  # Interaction might have already expired

# ----------------------------
# Run the bot
# ----------------------------
bot.run(TOKEN)