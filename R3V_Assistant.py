import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

# Intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# Bot setup
bot = commands.Bot(command_prefix="!", intents=intents)

# When bot is ready
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(f"Sync error: {e}")

# Welcome message
@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="recruitment")  # Change to your welcome channel name
    if channel:
        await channel.send(f"👋 Welcome to the server, {member.mention}! Feel free to use `/recruit` or `/officer` if you need help.")

# /recruit command
@bot.tree.command(name="recruit", description="Open a private recruitment thread.")
async def recruit(interaction: discord.Interaction):
    guild = interaction.guild
    channel = interaction.channel

    recruiter_role = discord.utils.get(guild.roles, name="Recruiter")  # Adjust to your actual role name
    thread_name = f"recruit-{interaction.user.name}"

    thread = await channel.create_thread(
        name=thread_name,
        type=discord.ChannelType.private_thread,
        invitable=False
    )

    await thread.add_user(interaction.user)
    if recruiter_role:
        for member in recruiter_role.members:
            await thread.add_user(member)

    await interaction.response.send_message(f"✅ Created a private recruitment thread: {thread.mention}", ephemeral=True)

# /officer command
@bot.tree.command(name="officer", description="Open a private thread for officer discussion.")
async def officer(interaction: discord.Interaction):
    guild = interaction.guild
    channel = interaction.channel

    officer_role = discord.utils.get(guild.roles, name="Director")  # Adjust to your actual role name
    thread_name = f"officer-{interaction.user.name}"

    thread = await channel.create_thread(
        name=thread_name,
        type=discord.ChannelType.private_thread,
        invitable=False
    )

    await thread.add_user(interaction.user)
    if officer_role:
        for member in officer_role.members:
            await thread.add_user(member)

    await interaction.response.send_message(f"✅ Created a private officer thread: {thread.mention}", ephemeral=True)

bot.run(TOKEN)