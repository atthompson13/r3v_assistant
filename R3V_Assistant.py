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

    # Prevent duplicate threads (case-insensitive)
    for thread in channel.threads:
        if thread.name.lower() == thread_name.lower():
            await interaction.response.send_message(
                "❌ You already have an open recruit thread.", ephemeral=True
            )
            return

    # Respond immediately to prevent interaction timeout
    await interaction.response.send_message(
        "✅ Creating your recruitment thread...", ephemeral=True
    )

    try:
        # Create private thread
        thread = await channel.create_thread(
            name=thread_name,
            type=discord.ChannelType.private_thread,
            invitable=False
        )

        # Add the user to the thread so they can see it
        await thread.add_user(interaction.user)

        # Ping Recruiter role directly
        recruiter_role = guild.get_role(RECRUITER_ROLE_ID)
        if recruiter_role:
            # Add all members with recruiter role to thread
            for member in recruiter_role.members:
                await thread.add_user(member)
            ping_text = recruiter_role.mention
        else:
            ping_text = ""
        
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
    except discord.Forbidden:
        await interaction.followup.send("❌ I don't have permission to create threads.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Failed to create thread: {e}", ephemeral=True)
        print(f"Thread creation error: {e}")

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

    # Prevent duplicate threads (case-insensitive)
    for thread in channel.threads:
        if thread.name.lower() == thread_name.lower():
            await interaction.response.send_message(
                "❌ You already have an open officer thread.", ephemeral=True
            )
            return

    await interaction.response.send_message(
        "✅ Creating your officer thread...", ephemeral=True
    )

    try:
        thread = await channel.create_thread(
            name=thread_name,
            type=discord.ChannelType.private_thread,
            invitable=False
        )

        # Add the user to the thread so they can see it
        await thread.add_user(interaction.user)

        # Ping Director role directly
        director_role = guild.get_role(DIRECTOR_ROLE_ID)
        if director_role:
            # Add all members with director role to thread
            for member in director_role.members:
                await thread.add_user(member)
            ping_text = director_role.mention
        else:
            ping_text = ""

        welcome_message = (
            f"{ping_text}\n"
            f"👋 {interaction.user.mention} has started a thread for officer discussion."
        )

        await thread.send(welcome_message)
        await log_action(guild, f"{interaction.user} created officer thread {thread.name}.")
    except discord.Forbidden:
        await interaction.followup.send("❌ I don't have permission to create threads.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Failed to create thread: {e}", ephemeral=True)
        print(f"Thread creation error: {e}")

# ----------------------------
# /close Command (Directors only)
# ----------------------------
@bot.tree.command(
    name="close",
    description="Close the current thread. (Directors only)",
    guild=discord.Object(id=GUILD_ID)
)
async def close(interaction: discord.Interaction):
    # Check if user has director role by ID
    if not any(role.id == DIRECTOR_ROLE_ID for role in interaction.user.roles):
        await interaction.response.send_message(
            "❌ You don't have permission to use this command.", ephemeral=True
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
    # Check if user has director role by ID
    if not any(role.id == DIRECTOR_ROLE_ID for role in interaction.user.roles):
        await interaction.response.send_message(
            "❌ You don't have permission to use this command.", ephemeral=True
        )
        return

    total_seconds = days * 86400 + hours * 3600 + minutes * 60
    if total_seconds <= 0:
        await interaction.response.send_message("⚠️ Please specify a valid time.", ephemeral=True)
        return
    
    # Store channel reference before async sleep
    reminder_channel = interaction.channel
    reminder_user = interaction.user

    await interaction.response.send_message(
        f"⏰ Reminder set for {days}d {hours}h {minutes}m from now.", ephemeral=True
    )
    await log_action(interaction.guild, f"{interaction.user} set a reminder for {days}d {hours}h {minutes}m: {message}")

    await asyncio.sleep(total_seconds)
    
    # Post reminder in the same channel/thread where it was set
    try:
        await reminder_channel.send(f"🔔 {reminder_user.mention} Reminder: {message}")
    except:
        # Fallback to DM if channel is no longer accessible
        try:
            await reminder_user.send(f"🔔 Reminder from {interaction.guild.name}: {message}")
        except:
            pass  # User has DMs disabled

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
