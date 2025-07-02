import discord, aiohttp, random

from discord.ext import commands

from discord import app_commands

from utils.admin_config import is_admin

class Manga(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

    # Helper to query Jikan

    async def jikan_request(self, url):

        async with aiohttp.ClientSession() as session:

            async with session.get(url) as resp:

                if resp.status == 200:

                    return await resp.json()

        return None

    # Core embed builder

    def build_embed(self, manga):

        return discord.Embed(

            title=manga.get("title", "Unknown Title"),

            description=(manga.get("synopsis")[:300] or "No synopsis.") + "...",

            url=manga.get("url"),

            color=discord.Color.teal()

        ).set_image(url=manga.get("images", {}).get("jpg", {}).get("image_url", ""))

    # ——— COMMAND: /manga ———

    @app_commands.command(name="manga", description="📚 Search a manga and explore details")

    async def manga(self, interaction: discord.Interaction, query: str):

        await interaction.response.defer()

        data = await self.jikan_request(f"https://api.jikan.moe/v4/manga?q={query}&limit=1")

        if not data or not data.get("data"):

            return await interaction.followup.send("❌ No manga found.")

        manga = data["data"][0]

        embed = self.build_embed(manga)

        view = MangaDropdownView(manga["mal_id"], manga)

        await interaction.followup.send(embed=embed, view=view)

    # ——— COMMAND: /randommanga ———

    @app_commands.command(name="randommanga", description="🎲 Surprise manga pick")

    @app_commands.describe(genre="Optional genre to filter")

    async def randommanga(self, interaction: discord.Interaction, genre: str = None):

        await interaction.response.defer()

        manga = await self.fetch_random_manga(genre)

        if not manga:

            return await interaction.followup.send("❌ Could not fetch manga.")

        embed = self.build_embed(manga)

        view = RandomNextButton(self.fetch_random_manga, genre)

        await interaction.followup.send(embed=embed, view=view)

    async def fetch_random_manga(self, genre=None):

        # Fallback to seasonal/top if genre fails

        url = "https://api.jikan.moe/v4/top/manga?limit=25&type=manga"

        data = await self.jikan_request(url)

        if not data or not data.get("data"):

            return None

        pool = data["data"]

        if genre:

            genre = genre.lower()

            pool = [m for m in pool if genre in [g["name"].lower() for g in m.get("genres", [])]]

        return random.choice(pool) if pool else None

# ——— INTERACTIVE: Dropdown Menu for /manga ———

class MangaDropdownView(discord.ui.View):

    def __init__(self, mal_id, manga):

        super().__init__(timeout=60)

        self.add_item(MangaDropdown(mal_id, manga))

class MangaDropdown(discord.ui.Select):

    def __init__(self, mal_id, manga):

        self.mal_id = mal_id

        self.manga = manga

        options = [

            discord.SelectOption(label="📖 View Full Synopsis", value="synopsis"),

            discord.SelectOption(label="👤 View Character List", value="characters"),

            discord.SelectOption(label="🌐 Open MyAnimeList Page", value="link")

        ]

        super().__init__(placeholder="More about this manga...", options=options)

    async def callback(self, interaction: discord.Interaction):

        if self.values[0] == "synopsis":

            text = self.manga.get("synopsis", "No synopsis found.")

            embed = discord.Embed(title="📖 Full Synopsis", description=text[:4000], color=discord.Color.dark_teal())

            await interaction.response.edit_message(embed=embed, view=self.view)

        elif self.values[0] == "characters":

            data = await self.fetch_characters()

            if not data:

                return await interaction.response.send_message("❌ No characters found.", ephemeral=True)

            top_chars = data[:5]

            view = CharacterSelectView(top_chars)

            await interaction.response.edit_message(content="👥 Choose a character to explore:", view=view, embed=None)

        elif self.values[0] == "link":

            await interaction.response.send_message(self.manga["url"], ephemeral=True)

    async def fetch_characters(self):

        url = f"https://api.jikan.moe/v4/manga/{self.mal_id}/characters"

        async with aiohttp.ClientSession() as session:

            async with session.get(url) as resp:

                if resp.status != 200:

                    return None

                data = await resp.json()

                return data.get("data")

# ——— INTERACTIVE: Character Drilldown Buttons ———

class CharacterSelectView(discord.ui.View):

    def __init__(self, characters):

        super().__init__(timeout=90)

        for char in characters:

            name = char["character"]["name"]

            self.add_item(CharacterButton(label=name[:25], char=char))

class CharacterButton(discord.ui.Button):

    def __init__(self, label, char):

        super().__init__(label=label, style=discord.ButtonStyle.secondary)

        self.char = char

    async def callback(self, interaction: discord.Interaction):

        char = self.char["character"]

        role = self.char.get("role", "Unknown")

        va = self.char.get("voice_actors", [{}])[0].get("name", "—")

        embed = discord.Embed(

            title=char["name"],

            description=f"**Role:** {role}\n**Voice Actor:** {va}",

            color=discord.Color.blue()

        ).set_image(url=char.get("images", {}).get("jpg", {}).get("image_url", ""))

        await interaction.response.send_message(embed=embed, ephemeral=True)

# ——— INTERACTIVE: ⏭️ Button for /randommanga ———

class RandomNextButton(discord.ui.View):

    def __init__(self, fetch_func, genre):

        super().__init__(timeout=60)

        self.fetch_func = fetch_func

        self.genre = genre

        self.add_item(RandomButton(fetch_func, genre))

class RandomButton(discord.ui.Button):

    def __init__(self, fetch_func, genre):

        super().__init__(label="⏭️ Next Manga", style=discord.ButtonStyle.primary)

        self.fetch_func = fetch_func

        self.genre = genre

    async def callback(self, interaction: discord.Interaction):

        manga = await self.fetch_func(self.genre)

        if not manga:

            return await interaction.response.send_message("❌ No new manga found.", ephemeral=True)

        embed = Manga(None).build_embed(manga)

        view = RandomNextButton(self.fetch_func, self.genre)

        await interaction.response.edit_message(embed=embed, view=view)

async def setup(bot):

    await bot.add_cog(Manga(bot))
