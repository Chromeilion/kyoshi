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
class antispam(commands.Cog):
    def __init__(self, client):
        self.client = client

    # Reset Command
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def antispam(self, ctx, state=None):
        if ANTISPAM_SYSTEM is True:
            stats = levelling.find_one({"server": ctx.guild.id})
            if state is None:
                embed2 = discord.Embed(title=_(":x: SETUP FAILED"),
                                       description=_("You need to enter a valid state!"),
                                       colour=ERROR_EMB_COLOUR)
                embed2.add_field(name=_("Example:"), value=PREFIX + _("antispam <true|false>`"))
                await ctx.send(embed=embed2)
            elif state == "true":
                levelling.update_one({"server": ctx.guild.id}, {"$set": {"Antispam": True}})
                embed = discord.Embed(title=_(":white_check_mark: ANTISPAM ENABLED!"),
                                      description=_("Anti-Spam now set to:") + state,
                                      colour=SUCCESS_EMB_COLOUR)
                await ctx.send(embed=embed)
            elif state == "false":
                levelling.update_one({"server": ctx.guild.id}, {"$set": {"Antispam": False}})
                embed = discord.Embed(title=_(":white_check_mark: ANTISPAM DISABLED!"),
                                      description=_("Anti-Spam now set to:") + state,
                                      colour=SUCCESS_EMB_COLOUR)
                await ctx.send(embed=embed)


antispam.__doc__ = _('''\nantispam <enable|disable> \n\nAbout:\nThe antispam command will allow you to see the current
stats about AntiSpam *Admin Only*''')


# Sets-up the cog for help
def setup(client):
    client.add_cog(antispam(client))
