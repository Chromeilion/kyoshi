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
class mutemessages(commands.Cog):
    def __init__(self, client):
        self.client = client

    # Reset Command
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def mutemessages(self, ctx, amount=None):
        if ANTISPAM_SYSTEM is True:
            if amount is None:
                embed2 = discord.Embed(title=_(":x: SETUP FAILED"),
                                       description=_("You need to enter a valid integer!"),
                                       colour=ERROR_EMB_COLOUR)
                embed2.add_field(name=_("Example:"), value=PREFIX + _("mutemessages <amount>`"))
                await ctx.send(embed=embed2)
            elif amount:
                levelling.update_one({"server": ctx.guild.id}, {"$set": {"muteMessages": int(amount)}})
                embed = discord.Embed(title=_(":white_check_mark: MUTE MESSAGES SET!"),
                                      description=_("Mute Messages Now:") + amount,
                                      colour=SUCCESS_EMB_COLOUR)
                await ctx.send(embed=embed)


mutemessages.__doc__ = _('''\nmutemessages <integer> \n\nAbout:\nThe mutemessage command will allow you to set how 
many messages to receive a mute from Anti-Spam. *Admin Only*''')


# Sets-up the cog for help
def setup(client):
    client.add_cog(mutemessages(client))
