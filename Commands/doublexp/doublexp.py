import discord
from discord.ext import commands
from Systems.levelsys import levelling
import os
from Systems.gettext_init import GettextInit


# Set up environment variables:
PREFIX = os.environ["BOT_PREFIX"]
ERROR_EMB_COLOUR = discord.Colour(int(os.environ["ERROR_EMB_COLOUR"]))
SUCCESS_EMB_COLOUR = discord.Colour(int(os.environ["SUCCESS_EMB_COLOUR"]))

# Set up gettext
_ = GettextInit(__file__).generate()


# Spam system class
class doublexp(commands.Cog):
    def __init__(self, client):
        self.client = client

    # Reset Command
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def doublexp(self, ctx, *, role=None):
        stats = levelling.find_one({"server": ctx.guild.id})
        if stats is None:
            newserver = {"server": ctx.guild.id, "double_xp_role": " "}
            levelling.insert_one(newserver)
        else:
            if role is None:
                embed2 = discord.Embed(title=_(":x: SETUP FAILED"),
                                       description=_("You need to enter a role name!"),
                                       colour=ERROR_EMB_COLOUR)
                embed2.add_field(name=_("Example:"), value=PREFIX + _("doublexp <rolename>"))
                await ctx.send(embed=embed2)
            elif role:
                levelling.update_one({"server": ctx.guild.id}, {"$set": {"double_xp_role": role}})
                embed = discord.Embed(title=_(":white_check_mark: DOUBLE XP ROLE!"),
                                      description=_("The new Double XP Role:") + role,
                                      colour=SUCCESS_EMB_COLOUR)
                await ctx.send(embed=embed)


doublexp.__doc__ = _('''\ndoublexp <rolename> \n\nAbout:\nThe DoubleXP command will let you set what role will earn 
x2 XP *Admin Only*''')


# Sets-up the cog for help
def setup(client):
    client.add_cog(doublexp(client))
