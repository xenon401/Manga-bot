import discord, aiohttp, json, os

from discord.ext import commands, tasks

from discord import app_commands

from utils.admin_config import is_admin

USERNAME = "xenon.otakus"

CONFIG_FILE = os.path.join("config", "autopost_config.json")

LAST_POST_FILE = os.path.join("config", "ig_last_post.json")

DEBUG = True

class Instagram(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

        self.auto_fetch.start()

    def cog_unload(self):

        self.auto_fetch.cancel()

    def get_channel_id(self, guild_id):

        if not os.path.exists(CONFIG_FILE):

            return None

        with open(CONFIG_FILE) as f:

            data = json.load(f)

        return data.get(str(guild_id), {}).get("insta_channel")

    def get_last_post_id(self):

        if not os.path.exists(LAST_POST_FILE):

            return None

        with open(LAST_POST_FILE) as f:

            return json.load(f).get("last_post_id")

    def set_last_post_id(self, post_id):

        with open(LAST_POST_FILE, "w") as f:

            json.dump({"last_post_id": post_id}, f)

    async def fetch_latest_post(self):

        url = f"https://www.instagram.com/{USERNAME}/?__a=1&__d=dis"

        headers = {"User-Agent": "Mozilla/5.0"}

        async with aiohttp.ClientSession() as session:

            async with session.get(url, headers=headers) as resp:

                content_type = resp.headers.get("Content-Type", "")

                if DEBUG:

                    print(f"[IG] Status: {resp.status} | Content-Type: {content_type}")

                if resp.status == 201 or "text/html" in content_type:

                    html = await resp.text()

                    with open("ig_debug.html", "w", encoding="utf-8") as f:

                        f.write(html)

                    print("[IG] 🚨 Received HTML instead of JSON. Dumped to ig_debug.html.")

                    return None

                if resp.status != 200:

                    print("[IG] ❌ Instagram returned non-200 status.")

                    return None

                try:

                    data = await resp.json()

                    edges = data["graphql"]["user"]["edge_owner_to_timeline_media"]["edges"]

                    return edges[0]["node"] if edges else None

                except Exception as e:

                    print(f"[IG] 💥 Failed to parse Instagram JSON: {e}")

                    return None

    async def send_post(self, guild, post):

        cid = self.get_channel_id(guild.id)

        if not cid:

            return

        channel = guild.get_channel(cid)

        if not channel:

            return

        caption_data = post.get("edge_media_to_caption", {}).get("edges", [])

        caption = caption_data[0]["node"]["text"] if caption_data else "No caption."

        media_urls = []

        if post.get("edge_sidecar_to_children"):

            media_urls = [n["node"]["display_url"] for n in post["edge_sidecar_to_children"]["edges"]]

        else:

            media_urls = [post.get("display_url")]

        embed = discord.Embed(

            title=f"📸 New Post from @{USERNAME}",

            description=caption[:1024],

            color=discord.Color.orange(),

            url=f"https://www.instagram.com/p/{post['shortcode']}/"

        )

        embed.set_image(url=media_urls[0])

        embed.set_footer(text="Instagram Auto-Post")

        await channel.send(embed=embed)

        for extra in media_urls[1:]:

            await channel.send(extra)

    @tasks.loop(hours=12)

    async def auto_fetch(self):

        await self.bot.wait_until_ready()

        post = await self.fetch_latest_post()

        if not post:

            return

        last = self.get_last_post_id()

        if post["id"] == last:

            return

        self.set_last_post_id(post["id"])

        for guild in self.bot.guilds:

            await self.send_post(guild, post)

    @is_admin()

    @app_commands.command(name="igrefresh", description="🔄 Fetch and post the latest Instagram update")

    async def igrefresh(self, interaction: discord.Interaction):

        await interaction.response.defer(ephemeral=True)

        post = await self.fetch_latest_post()

        if not post:

            return await interaction.followup.send("❌ No valid Instagram post found.")

        if post["id"] == self.get_last_post_id():

            return await interaction.followup.send("ℹ️ Already posted. No new content.")

        self.set_last_post_id(post["id"])

        await self.send_post(interaction.guild, post)

        await interaction.followup.send("✅ Latest Instagram content posted.")

    @is_admin()

    @app_commands.command(name="debuginsta", description="🛠️ Debug info for latest Instagram post")

    async def debuginsta(self, interaction: discord.Interaction):

        await interaction.response.defer(ephemeral=True)

        post = await self.fetch_latest_post()

        if not post:

            return await interaction.followup.send("❌ Failed to retrieve post data.")

        cap = post.get("edge_media_to_caption", {}).get("edges", [])

        cap_text = cap[0]["node"]["text"] if cap else "No caption"

        count = len(post.get("edge_sidecar_to_children", {}).get("edges", [])) or 1

        await interaction.followup.send(

            f"🧪 Debug Info:\n• ID: `{post['id']}`\n• Media: {count} item(s)\n• Shortcode: `{post['shortcode']}`\n• Caption: {cap_text[:150]}..."

        )

async def setup(bot):

    await bot.add_cog(Instagram(bot))