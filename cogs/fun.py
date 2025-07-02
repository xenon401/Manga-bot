import discord, aiohttp, random

from discord.ext import commands

from discord import app_commands

class Fun(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

    @app_commands.command(name="meme", description="😂 Send a random meme")

    async def meme(self, interaction: discord.Interaction):

        await interaction.response.defer()

        async with aiohttp.ClientSession() as session:

            async with session.get("https://meme-api.com/gimme") as resp:

                if resp.status != 200:

                    return await interaction.followup.send("❌ Failed to fetch meme.")

                data = await resp.json()

        await interaction.followup.send(data.get("url", "❌ Meme not found."))

    @app_commands.command(name="quote", description="📖 Send an inspirational quote")

    async def quote(self, interaction: discord.Interaction):

        await interaction.response.defer()

        async with aiohttp.ClientSession() as session:

            async with session.get("https://zenquotes.io/api/random") as resp:

                if resp.status != 200:

                    return await interaction.followup.send("❌ Failed to fetch quote.")

                data = await resp.json()

        q = data[0].get("q", "No quote found.")

        a = data[0].get("a", "Unknown")

        await interaction.followup.send(f'📜 "{q}"\n— *{a}*')

    @app_commands.command(name="8ball", description="🎱 Ask the magic 8-ball a question")

    async def eightball(self, interaction: discord.Interaction, question: str):

        answers = [

            "Yes", "No", "Maybe", "Definitely", "Ask again later",

            "Absolutely not", "Without a doubt", "Better not tell you now"

        ]

        choice = random.choice(answers)

        await interaction.response.send_message(f'🎱 {choice}')

async def setup(bot):

    await bot.add_cog(Fun(bot))