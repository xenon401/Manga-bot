import discord

from discord.ext import commands

from discord import app_commands

class HelpMenu(discord.ui.View):

    def __init__(self):

        super().__init__(timeout=60)

        self.add_item(HelpSelect())

class HelpSelect(discord.ui.Select):

    def __init__(self):

        options = [

            discord.SelectOption(label="Admin & Config", emoji="🛠️", value="admin"),

            discord.SelectOption(label="AutoPost", emoji="🔁", value="autopost"),

            discord.SelectOption(label="Instagram", emoji="📸", value="ig"),

            discord.SelectOption(label="Manga", emoji="📚", value="manga"),

            discord.SelectOption(label="Fun & Utility", emoji="🎉", value="fun"),

        ]

        super().__init__(placeholder="📖 Choose a command category", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):

        embed = discord.Embed(color=discord.Color.blurple())

        if self.values[0] == "admin":

            embed.title = "🛠️ Admin & Config"

            embed.description = (

                "`/setchannel`, `/setadminrole`, `/reloadcog`, `/status`, `/channelstatus`, `/uptime`"

            )

        elif self.values[0] == "autopost":

            embed.title = "🔁 AutoPost Controls"

            embed.description = (

                "`/startautopost`, `/stopautopost`, `/setinterval`"

            )

        elif self.values[0] == "ig":

            embed.title = "📸 Instagram Tools"

            embed.description = "`/igrefresh`, `/debuginsta`"

        elif self.values[0] == "manga":

            embed.title = "📚 Manga Info & Search"

            embed.description = "`/manga`, `/topmanga`, `/randommanga`"

        elif self.values[0] == "fun":

            embed.title = "🎉 Fun & Utility"

            embed.description = "`/meme`, `/quote`, `/8ball`"

        await interaction.response.edit_message(embed=embed, view=self.view)

class Help(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

    @app_commands.command(name="help", description="📖 View help menu")

    async def help(self, interaction: discord.Interaction):

        embed = discord.Embed(

            title="Need help?",

            description="Use the menu below to explore command categories.",

            color=discord.Color.green()

        )

        await interaction.response.send_message(embed=embed, view=HelpMenu(), ephemeral=True)

async def setup(bot):

    await bot.add_cog(Help(bot))