import discord
from discord.ext import commands
from Systems.levelsys import levelling
import os
from Systems.gettext_init import GettextInit
import distutils.util

# Get environment variables:
ANTISPAM_SYSTEM = bool(distutils.util.strtobool(os.environ["BOT_ANTISPAM_SYSTEM"]))
PREFIX = os.environ["BOT_PREFIX"]
ERROR_EMB_COLOUR = discord.Colour(int(os.environ["ERROR_EMB_COLOUR"]))
SUCCESS_EMB_COLOUR = discord.Colour(int(os.environ["SUCCESS_EMB_COLOUR"]))

# Set up gettext
_ = GettextInit(__file__).generate()


# Spam system class
class mutetime(commands.Cog):
    def __init__(self, client):
        self.client = client

    # Reset Command
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def mutetime(self, ctx, time=None):
        if ANTISPAM_SYSTEM is True:
            stats = levelling.find_one({"server": ctx.guild.id})
            if time is None:
                embed2 = discord.Embed(title=_(":x: SETUP FAILED"),
                                       description=_("You need to enter a valid integer!"),
                                       colour=ERROR_EMB_COLOUR)
                embed2.add_field(name=_("Example:"), value=PREFIX + _("mutetime <seconds>`"))
                await ctx.send(embed=embed2)
            elif time:
                levelling.update_one({"server": ctx.guild.id}, {"$set": {"mutedTime": int(time)}})
                embed = discord.Embed(title=_(":white_check_mark: MUTED TIME SET!"),
                                      description=_("Mute Time:") + time + _("s"),
                                      colour=SUCCESS_EMB_COLOUR)
                await ctx.send(embed=embed)


mutetime.__doc__ = _('''\nmutetime <seconds> \n\nAbout:\nThe mutetime command will allow you to set how long you get 
muted for from Anti-Spam. *Admin Only*''')


# Sets-up the cog for help
def setup(client):
    client.add_cog(mutetime(client))
