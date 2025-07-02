import discord, aiohttp, os, json

from discord.ext import commands, tasks

from discord import app_commands

from utils.admin_config import is_admin

CONFIG_FILE = os.path.join("config", "autopost_config.json")

SCHEDULE_FILE = os.path.join("config", "autopost_schedule.json")

MEME_URL = "https://meme-api.com/gimme"

QUOTE_URL = "https://zenquotes.io/api/random"

class Autopost(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

        self.intervals = {}  # per guild schedule

        self.load_intervals()

        self.meme_loop.change_interval(seconds=self.intervals.get("meme", 21600))

        self.quote_loop.change_interval(seconds=self.intervals.get("quote", 21600))

        self.meme_loop.start()

        self.quote_loop.start()

    def cog_unload(self):

        self.meme_loop.cancel()

        self.quote_loop.cancel()

    def load_intervals(self):

        if os.path.exists(SCHEDULE_FILE):

            with open(SCHEDULE_FILE) as f:

                data = json.load(f)

            self.intervals["meme"] = list(data.values())[0].get("meme", 21600)

            self.intervals["quote"] = list(data.values())[0].get("quote", 21600)

        else:

            self.intervals = {"meme": 21600, "quote": 21600}

    def get_channel_id(self, guild_id, key):

        if not os.path.exists(CONFIG_FILE):

            return None

        with open(CONFIG_FILE) as f:

            data = json.load(f)

        return data.get(str(guild_id), {}).get(key)

    async def fetch_json(self, url):

        async with aiohttp.ClientSession() as session:

            async with session.get(url) as resp:

                if resp.status == 200:

                    return await resp.json()

        return None

    @tasks.loop(seconds=21600)

    async def meme_loop(self):

        await self.bot.wait_until_ready()

        for guild in self.bot.guilds:

            cid = self.get_channel_id(guild.id, "meme_channel")

            if not cid:

                continue

            channel = guild.get_channel(cid)

            if not channel:

                continue

            data = await self.fetch_json(MEME_URL)

            if data:

                embed = discord.Embed(

                    title=data.get("title", "Random Meme"),

                    url=data.get("postLink", ""),

                    color=discord.Color.purple()

                )

                embed.set_image(url=data.get("url"))

                embed.set_footer(text=f"👍 {data.get('ups', 0)} • r/{data.get('subreddit', 'unknown')}")

                await channel.send(embed=embed)

    @tasks.loop(seconds=21600)

    async def quote_loop(self):

        await self.bot.wait_until_ready()

        for guild in self.bot.guilds:

            cid = self.get_channel_id(guild.id, "quote_channel")

            if not cid:

                continue

            channel = guild.get_channel(cid)

            if not channel:

                continue

            data = await self.fetch_json(QUOTE_URL)

            if data:

                quote = data[0].get("q", "No quote found.")

                author = data[0].get("a", "Unknown")

                embed = discord.Embed(

                    description=f'📜 *"{quote}"*\n\n— **{author}**',

                    color=discord.Color.gold()

                )

                await channel.send(embed=embed)

    @is_admin()

    @app_commands.command(name="startautopost", description="▶️ Start auto-post loops manually")

    async def startautopost(self, interaction: discord.Interaction):

        await interaction.response.defer(ephemeral=True)

        if not self.meme_loop.is_running():

            self.meme_loop.start()

        if not self.quote_loop.is_running():

            self.quote_loop.start()

        await interaction.followup.send("✅ Meme & quote loops started.")

    @is_admin()

    @app_commands.command(name="stopautopost", description="⏸️ Stop all auto-post loops")

    async def stopautopost(self, interaction: discord.Interaction):

        await interaction.response.defer(ephemeral=True)

        if self.meme_loop.is_running():

            self.meme_loop.cancel()

        if self.quote_loop.is_running():

            self.quote_loop.cancel()

        await interaction.followup.send("⏸️ Auto-posting paused.")

    @is_admin()

    @app_commands.command(name="setinterval", description="⏱️ Set meme/quote post frequency")

    @app_commands.describe(

        meme_hours="Hours for meme post",

        meme_minutes="Minutes for meme post",

        quote_hours="Hours for quote post",

        quote_minutes="Minutes for quote post"

    )

    async def setinterval(self, interaction: discord.Interaction,

        meme_hours: int = 0, meme_minutes: int = 0,

        quote_hours: int = 0, quote_minutes: int = 0):

        await interaction.response.defer(ephemeral=True)

        meme_secs = meme_hours * 3600 + meme_minutes * 60

        quote_secs = quote_hours * 3600 + quote_minutes * 60

        gid = str(interaction.guild.id)

        data = {}

        if os.path.exists(SCHEDULE_FILE):

            with open(SCHEDULE_FILE) as f:

                data = json.load(f)

        data[gid] = {"meme": meme_secs, "quote": quote_secs}

        with open(SCHEDULE_FILE, "w") as f:

            json.dump(data, f, indent=2)

        self.meme_loop.change_interval(seconds=meme_secs)

        self.quote_loop.change_interval(seconds=quote_secs)

        await interaction.followup.send(

            f"✅ Intervals updated:\n• Meme: {meme_hours}h {meme_minutes}m\n• Quote: {quote_hours}h {quote_minutes}m"

        )

async def setup(bot):

    await bot.add_cog(Autopost(bot))