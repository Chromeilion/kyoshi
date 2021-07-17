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
class ignoredrole(commands.Cog):
    def __init__(self, client):
        self.client = client

    # Reset Command
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def ignoredrole(self, ctx, role=None):
        if ANTISPAM_SYSTEM is True:
            if role is None:
                embed2 = discord.Embed(title=_(":x: SETUP FAILED"),
                                       description=_("You need to enter a valid name!"),
                                       colour=ERROR_EMB_COLOUR)
                embed2.add_field(name=_("Example:"), value=PREFIX + _("ignoredrole <role>"))
                await ctx.send(embed=embed2)
            elif role:
                levelling.update_one({"server": ctx.guild.id}, {"$set": {"ignoredRole": str(role)}})
                embed = discord.Embed(title=_(":white_check_mark: IGNORED ROLE SET!"),
                                      description=_("Ignored Role Now:") + role,
                                      colour=SUCCESS_EMB_COLOUR)
                await ctx.send(embed=embed)


ignoredrole.__doc__ = _('''\nignoredrole <role> \n\nAbout:\nThe ignoredrole command will allow you to set a role 
that gets ignored by Anti-Spam. *Admin Only*''')


# Sets-up the cog for help
def setup(client):
    client.add_cog(ignoredrole(client))
