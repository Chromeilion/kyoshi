import discord
from discord.ext import commands
from Systems.levelsys import levelling
import os
from Systems.gettext_init import GettextInit

# Set up environment variables
SUCCESS_EMB_COLOUR = discord.Colour(int(os.environ["SUCCESS_EMB_COLOUR"]))
PREFIX = os.environ["BOT_PREFIX"]
ERROR_EMB_COLOUR = discord.Colour(int(os.environ["ERROR_EMB_COLOUR"]))

# Set up gettext
_ = GettextInit(__file__).generate()


# Spam system class
class xppermessage(commands.Cog):
    def __init__(self, client):
        self.client = client

    # Reset Command
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def xppermessage(self, ctx, xp=None):
        stats = levelling.find_one({"server": ctx.guild.id})
        if stats is None:
            new_server = {"server": ctx.guild.id, "xp_per_message": 10}
            levelling.insert_one(new_server)
        else:
            if xp is None:
                embed2 = discord.Embed(title=_(":x: SETUP FAILED"),
                                       description=_("You need to enter the amount of xp!"),
                                       colour=ERROR_EMB_COLOUR)
                embed2.add_field(name=_("Example:"), value=PREFIX + _("xppermessage <amount>"))
                await ctx.send(embed=embed2)
            elif xp:
                levelling.update_one({"server": ctx.guild.id}, {"$set": {"xp_per_message": int(xp)}})
                embed = discord.Embed(title=_(":white_check_mark: XP UPDATED!"),
                                      description=_("XP Per Message is now:") + xp,
                                      colour=SUCCESS_EMB_COLOUR)
                await ctx.send(embed=embed)


xppermessage.__doc__ = _('''\nxppermessage <amount> \n\nAbout:\nThe xppermessage command will allow you to change xp 
gain per level.''')


# Sets-up the cog for help
def setup(client):
    client.add_cog(xppermessage(client))
