import discord
from discord.ext import commands
from Systems.levelsys import levelling
import os
from Systems.gettext_init import GettextInit

# Set up environment variables:
SUCCESS_EMB_COLOUR = discord.Colour(int(os.environ["SUCCESS_EMB_COLOUR"]))
ERROR_EMB_COLOUR = os.environ['ERROR_EMB_COLOUR']
BOT_ANTISPAM_SYSTEM = os.environ['BOT_ANTISPAM_SYSTEM']
PREFIX = os.environ['BOT_PREFIX']

# Set up gettext
_ = GettextInit(__file__).generate()


# Spam system class
class warningmessages(commands.Cog):
    def __init__(self, client):
        self.client = client

    # Reset Command
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def warningmessages(self, ctx, amount=None):
        if BOT_ANTISPAM_SYSTEM:
            if amount is None:
                embed2 = discord.Embed(title=_(":x: SETUP FAILED"),
                                       description=_("You need to enter a valid integer!"),
                                       colour=ERROR_EMB_COLOUR)
                embed2.add_field(name=_("Example:"), value=PREFIX + _("warningmessages <amount>`"))
                await ctx.send(embed=embed2)
            elif amount:
                levelling.update_one({"server": ctx.guild.id}, {"$set": {"warningMessages": int(amount)}})
                embed = discord.Embed(title=_(":white_check_mark: WARNING MESSAGES SET!"),
                                      description=_("Warning Messages Now:") + amount,
                                      colour=SUCCESS_EMB_COLOUR)
                await ctx.send(embed=embed)


warningmessages.__doc__ = _('''\nwarniningmessages <integer> \n\nAbout:\nThe warningmessages command will allow 
you to set how many messages to receive a warning from Anti-Spam. *Admin Only*''')

# Sets-up the cog for help
def setup(client):
    client.add_cog(warningmessages(client))
