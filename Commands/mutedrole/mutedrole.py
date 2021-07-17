import discord
from discord.ext import commands
from Systems.levelsys import levelling
import os
from Systems.gettext_init import GettextInit
import distutils.util

# Set up environment variables:
ANTISPAM_SYSTEM = bool(distutils.util.strtobool(os.environ["BOT_ANTISPAM_SYSTEM"]))
PREFIX = os.environ["BOT_PREFIX"]
ERROR_EMB_COLOUR = discord.Colour(int(os.environ["ERROR_EMB_COLOUR"]))
SUCCESS_EMB_COLOUR = discord.Colour(int(os.environ["SUCCESS_EMB_COLOUR"]))

# Set up gettext
_ = GettextInit(__file__).generate()


# Spam system class
class mutedrole(commands.Cog):
    def __init__(self, client):
        self.client = client

    # Reset Command
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def mutedrole(self, ctx, role=None):
        if ANTISPAM_SYSTEM is True:
            stats = levelling.find_one({"server": ctx.guild.id})
            if role is None:
                embed2 = discord.Embed(title=_(":x: SETUP FAILED"),
                                       description=_("You need to enter a valid name!"),
                                       colour=ERROR_EMB_COLOUR)
                embed2.add_field(name=_("Example:"), value=PREFIX + _("mutedrole <role>"))
                await ctx.send(embed=embed2)
            elif role:
                levelling.update_one({"server": ctx.guild.id}, {"$set": {"mutedRole": str(role)}})
                embed = discord.Embed(title=_(":white_check_mark: MUTED ROLE SET!"),
                                      description=_("Muted Role Now:") + role,
                                      colour=SUCCESS_EMB_COLOUR)
                await ctx.send(embed=embed)


mutedrole.__doc__ = _('''\nmutedrole <role> \n\nAbout:\nThe mutedrole command will allow you to set what role a 
muted person receives from Anti-Spam. *Admin Only*''')


# Sets-up the cog for help
def setup(client):
    client.add_cog(mutedrole(client))
