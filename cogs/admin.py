import discord, os, json, platform

from discord.ext import commands

from discord import app_commands

from datetime import datetime

from utils.admin_config import is_admin

CONFIG_FILE = os.path.join("config", "autopost_config.json")

ADMIN_CONFIG = os.path.join("config", "admin_roles.json")

class Admin(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

        self.bot.launch_time = datetime.utcnow()

    @is_admin()

    @app_commands.command(name="setchannel", description="📌 Set post channel (meme, quote, insta)")

    async def setchannel(self, interaction: discord.Interaction, type: str, channel: discord.TextChannel):

        await interaction.response.defer(ephemeral=True)

        if type not in ("meme", "quote", "insta"):

            return await interaction.followup.send("❌ Use: meme, quote, or insta")

        data = {}

        if os.path.exists(CONFIG_FILE):

            with open(CONFIG_FILE) as f:

                data = json.load(f)

        gid = str(interaction.guild.id)

        data.setdefault(gid, {})[f"{type}_channel"] = channel.id

        with open(CONFIG_FILE, "w") as f:

            json.dump(data, f, indent=2)

        await interaction.followup.send(f"✅ `{type}` channel set to {channel.mention}")

    @is_admin()

    @app_commands.command(name="setadminrole", description="🛡️ Set admin role for this server")

    async def setadminrole(self, interaction: discord.Interaction, role: discord.Role):

        await interaction.response.defer(ephemeral=True)

        gid = str(interaction.guild.id)

        data = {}

        if os.path.exists(ADMIN_CONFIG):

            with open(ADMIN_CONFIG) as f:

                data = json.load(f)

        data[gid] = role.id

        with open(ADMIN_CONFIG, "w") as f:

            json.dump(data, f, indent=2)

        await interaction.followup.send(f"✅ Admin role set to {role.mention}")

    @is_admin()

    @app_commands.command(name="listadminroles", description="🔍 Show the current admin role")

    async def listadminroles(self, interaction: discord.Interaction):

        await interaction.response.defer(ephemeral=True)

        gid = str(interaction.guild.id)

        if not os.path.exists(ADMIN_CONFIG):

            return await interaction.followup.send("⚠️ No admin config file found.")

        with open(ADMIN_CONFIG) as f:

            data = json.load(f)

        rid = data.get(gid)

        if rid:

            role = interaction.guild.get_role(rid)

            if role:

                return await interaction.followup.send(f"🛡️ Admin role: {role.mention}")

            return await interaction.followup.send(f"🛡️ Admin role ID: `{rid}` (not found in this server)")

        await interaction.followup.send("ℹ️ No admin role has been set for this server.")

    @is_admin()

    @app_commands.command(name="removeadminrole", description="❌ Remove admin role restriction")

    async def removeadminrole(self, interaction: discord.Interaction):

        await interaction.response.defer(ephemeral=True)

        gid = str(interaction.guild.id)

        if not os.path.exists(ADMIN_CONFIG):

            return await interaction.followup.send("⚠️ Admin config file missing.")

        with open(ADMIN_CONFIG) as f:

            data = json.load(f)

        if gid in data:

            data.pop(gid)

            with open(ADMIN_CONFIG, "w") as f:

                json.dump(data, f, indent=2)

            await interaction.followup.send("✅ Admin role removed.")

        else:

            await interaction.followup.send("ℹ️ No admin role was set for this server.")

    @is_admin()

    @app_commands.command(name="channelstatus", description="📋 Show current autopost channel settings")

    async def channelstatus(self, interaction: discord.Interaction):

        await interaction.response.defer(ephemeral=True)

        gid = str(interaction.guild.id)

        if not os.path.exists(CONFIG_FILE):

            return await interaction.followup.send("⚠️ No channel config file found.")

        with open(CONFIG_FILE) as f:

            data = json.load(f)

        server = data.get(gid)

        if not server:

            return await interaction.followup.send("ℹ️ No channels configured yet.")

        status = [f"• **{k}** → <#{v}>" for k, v in server.items()]

        await interaction.followup.send("\n".join(status))

    @is_admin()

    @app_commands.command(name="status", description="🔁 Show autopost loop status")

    async def status(self, interaction: discord.Interaction):

        await interaction.response.defer()

        loops = []

        cog = self.bot.get_cog("Autopost")

        if cog:

            loops.append("🟢 Meme Loop" if cog.meme_loop.is_running() else "🔴 Meme Loop")

            loops.append("🟢 Quote Loop" if cog.quote_loop.is_running() else "🔴 Quote Loop")

        else:

            loops.append("❌ Autopost cog not loaded.")

        await interaction.followup.send("🔧 **Loop Status**:\n" + "\n".join(loops))

    @is_admin()

    @app_commands.command(name="uptime", description="⏱️ Show how long the bot's been online")

    async def uptime(self, interaction: discord.Interaction):

        now = datetime.utcnow()

        diff = now - self.bot.launch_time

        hrs, rem = divmod(diff.total_seconds(), 3600)

        mins, secs = divmod(rem, 60)

        await interaction.response.send_message(f"🕒 Uptime: {int(hrs)}h {int(mins)}m {int(secs)}s")

    @is_admin()

    @app_commands.command(name="setstatus", description="🧾 Set the bot's visible status")

    @app_commands.describe(

        activity_type="Type: Playing, Watching, Listening, Streaming, Competing",

        custom_status="Status text"

    )

    async def setstatus(self, interaction: discord.Interaction, activity_type: str, custom_status: str):

        await interaction.response.defer(ephemeral=True)

        types = {

            "playing": discord.ActivityType.playing,

            "watching": discord.ActivityType.watching,

            "listening": discord.ActivityType.listening,

            "streaming": discord.ActivityType.streaming,

            "competing": discord.ActivityType.competing

        }

        activity = types.get(activity_type.lower())

        if not activity:

            return await interaction.followup.send("❌ Invalid type. Use: Playing, Watching, Listening, Streaming, Competing")

        if activity_type.lower() == "streaming":

            await self.bot.change_presence(activity=discord.Streaming(

                name=custom_status,

                url="https://www.twitch.tv/monstercat"

            ))

        else:

            await self.bot.change_presence(activity=discord.Activity(type=activity, name=custom_status))

        await interaction.followup.send(f"✅ Status set to `{activity_type.title()} {custom_status}`")

    @is_admin()

    @app_commands.command(name="reloadcog", description="♻️ Reload a single cog module")

    async def reloadcog(self, interaction: discord.Interaction, name: str):

        await interaction.response.defer(ephemeral=True)

        try:

            await self.bot.unload_extension(f"cogs.{name}")

            await self.bot.load_extension(f"cogs.{name}")

            await interaction.followup.send(f"✅ Reloaded `cogs.{name}`")

        except Exception as e:

            await interaction.followup.send(f"❌ Failed to reload `{name}`:\n`{type(e).__name__}: {e}`")

    @is_admin()

    @app_commands.command(name="reloadall", description="🔁 Reload all cogs")

    async def reloadall(self, interaction: discord.Interaction):

        await interaction.response.defer(ephemeral=True)

        success, failed = [], []

        for file in os.listdir("cogs"):

            if file.endswith(".py"):

                name = file[:-3]

                try:

                    await self.bot.unload_extension(f"cogs.{name}")

                    await self.bot.load_extension(f"cogs.{name}")

                    success.append(name)

                except Exception as e:

                    failed.append(f"`{name}` → {type(e).__name__}: {e}")

        msg = f"✅ Reloaded: {', '.join(success)}"

        if failed:

            msg += f"\n❌ Errors:\n" + "\n".join(failed)

        await interaction.followup.send(msg)

    @is_admin()

    @app_commands.command(name="debugall", description="🧪 View bot diagnostics")

    async def debugall(self, interaction: discord.Interaction):

        await interaction.response.defer(ephemeral=True)

        latency = round(self.bot.latency * 1000)

        cog_list = list(self.bot.cogs.keys())

        uptime = datetime.utcnow() - self.bot.launch_time

        hrs, rem = divmod(uptime.total_seconds(), 3600)

        mins, secs = divmod(rem, 60)

        embed = discord.Embed(

            title="🔍 Bot Diagnostic Panel",

            color=discord.Color.brand_green()

        )

        embed.add_field(name="⏱️ Uptime", value=f"{int(hrs)}h {int(mins)}m", inline=True)

        embed.add_field(name="📶 Ping", value=f"{latency} ms", inline=True)

        embed.add_field(name="🔌 Cogs", value=", ".join(cog_list) or "None", inline=False)

        embed.set_footer(text=f"Python {platform.python_version()} • discord.py {discord.__version__}")

        await interaction.followup.send(embed=embed)

    @is_admin()

    @app_commands.command(name="shutdown", description="💣 Shut down the bot safely")

    async def shutdown(self, interaction: discord.Interaction):

        await interaction.response.defer(ephemeral=True)

        await interaction.followup.send("🛑 Shutting down gracefully...")

        await self.bot.close()

async def setup(bot):

    await bot.add_cog(Admin(bot))