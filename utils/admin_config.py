import os, json

from discord import app_commands

ADMIN_CONFIG = os.path.join("config", "admin_roles.json")

def is_admin():

    async def predicate(interaction):

        gid = str(interaction.guild.id)

        if not os.path.exists(ADMIN_CONFIG):

            return False

        with open(ADMIN_CONFIG, "r") as f:

            data = json.load(f)

        rid = data.get(gid)

        if not rid:

            return False

        return any(role.id == rid for role in interaction.user.roles)

    return app_commands.check(predicate)
