import discord, aiohttp, os, json

from discord.ext import commands, tasks

from discord import app_commands

from utils.admin_config import is_admin

CONFIG_FILE = os.path.join("config", "autopost_config.json")

SCHEDULE_FILE = os.path.join("config", "autopost_schedule.json")
MANGADEX_LAST_POST_FILE = os.path.join("config", "mangadex_last_post.json")

MEME_URL = "https://meme-api.com/gimme"

QUOTE_URL = "https://zenquotes.io/api/random"

class Autopost(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

        self.intervals = {}  # per guild schedule

        self.load_intervals()
        self.last_mangadex_post_id = self.get_last_mangadex_post_id()

        self.meme_loop.change_interval(seconds=self.intervals.get("meme", 21600))

        self.quote_loop.change_interval(seconds=self.intervals.get("quote", 21600))
        self.mangadex_loop.change_interval(seconds=self.intervals.get("mangadex", 1800))

        self.meme_loop.start()

        self.quote_loop.start()
        self.mangadex_loop.start()

    def cog_unload(self):

        self.meme_loop.cancel()

        self.quote_loop.cancel()
        self.mangadex_loop.cancel()

    def load_intervals(self):

        if os.path.exists(SCHEDULE_FILE):

            with open(SCHEDULE_FILE) as f:

                data = json.load(f)

            self.intervals["meme"] = list(data.values())[0].get("meme", 21600)
            self.intervals["quote"] = list(data.values())[0].get("quote", 21600)
            self.intervals["mangadex"] = list(data.values())[0].get("mangadex", 1800)


        else:

            self.intervals = {"meme": 21600, "quote": 21600, "mangadex": 1800}

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

    def get_last_mangadex_post_id(self):
        if not os.path.exists(MANGADEX_LAST_POST_FILE):
            return None
        with open(MANGADEX_LAST_POST_FILE) as f:
            data = json.load(f)
            return data.get("last_post_id")

    def set_last_mangadex_post_id(self, post_id):
        with open(MANGADEX_LAST_POST_FILE, "w") as f:
            json.dump({"last_post_id": post_id}, f)

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

    @tasks.loop(minutes=30)
    async def mangadex_loop(self):
        await self.bot.wait_until_ready()
        
        # Fetch the latest chapters
        url = "https://api.mangadex.org/chapter?limit=20&order[publishAt]=desc&translatedLanguage[]=en"
        latest_chapters = await self.fetch_json(url)
        if not latest_chapters or not latest_chapters.get("data"):
            return

        # We process chapters oldest to newest to maintain order
        for chapter_data in reversed(latest_chapters["data"]):
            chapter_id = chapter_data["id"]
            
            # Avoid posting duplicates
            if chapter_id == self.last_mangadex_post_id:
                continue

            # Fetch manga details
            manga_id = next((rel["id"] for rel in chapter_data["relationships"] if rel["type"] == "manga"), None)
            if not manga_id:
                continue
            
            manga_details = await self.fetch_json(f"https://api.mangadex.org/manga/{manga_id}")
            if not manga_details or not manga_details.get("data"):
                continue

            manga_title = manga_details["data"]["attributes"]["title"].get("en", "Unknown Title")
            
            # Fetch cover art
            cover_id = next((rel["id"] for rel in manga_details["data"]["relationships"] if rel["type"] == "cover_art"), None)
            cover_filename = ""
            if cover_id:
                cover_details = await self.fetch_json(f"https://api.mangadex.org/cover/{cover_id}")
                if cover_details and cover_details.get("data"):
                    cover_filename = cover_details["data"]["attributes"]["fileName"]

            cover_url = f"https://uploads.mangadex.org/covers/{manga_id}/{cover_filename}" if cover_filename else None

            # Prepare embed
            chapter_title = chapter_data["attributes"]["title"]
            chapter_num = chapter_data["attributes"]["chapter"]
            chapter_url = f"https://mangadex.org/chapter/{chapter_id}"
            
            embed = discord.Embed(
                title=f"New Chapter: {manga_title} - Ch. {chapter_num}",
                description=f"**Title:** {chapter_title}",
                url=chapter_url,
                color=discord.Color.blue()
            )
            if cover_url:
                embed.set_thumbnail(url=cover_url)
            embed.set_footer(text="Posted from MangaDex")
            
            # Post to all configured guilds
            for guild in self.bot.guilds:
                cid = self.get_channel_id(guild.id, "mangadex_channel")
                if not cid:
                    continue
                channel = guild.get_channel(cid)
                if channel:
                    await channel.send(embed=embed)
            
            # Update the last post ID to avoid re-posting
            self.set_last_mangadex_post_id(chapter_id)
            self.last_mangadex_post_id = chapter_id

async def setup(bot):

    await bot.add_cog(Autopost(bot))
