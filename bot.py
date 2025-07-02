import discord, os

from discord.ext import commands

from dotenv import load_dotenv

from discord import app_commands

import platform

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

intents = discord.Intents.default()

intents.message_content = True

intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event

async def setup_hook():

    # Load all cogs dynamically from the cogs/ folder

    for file in os.listdir("cogs"):

        if file.endswith(".py"):

            try:

                await bot.load_extension(f"cogs.{file[:-3]}")

                print(f"🧩 Loaded cog: {file}")

            except Exception as e:

                print(f"❌ Failed to load {file}: {type(e).__name__}: {e}")

    # Sync slash commands globally

    synced = await bot.tree.sync()

    print(f"🔁 Synced {len(synced)} slash commands globally.")

@bot.event

async def on_ready():

    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")

    print(f"🧠 Python {platform.python_version()} • discord.py {discord.__version__}")

@bot.tree.error

async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):

    if isinstance(error, app_commands.CheckFailure):

        await interaction.response.send_message(

            "⛔ You don't have permission to use this command.",

            ephemeral=True

        )

    else:

        await interaction.response.send_message(

            f"⚠️ An error occurred: `{type(error).__name__}` - {error}",

            ephemeral=True

        )

        raise error  # Optional: allows logging full trace in console

bot.run(TOKEN)