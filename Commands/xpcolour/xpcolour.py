import discord
from discord.ext import commands
from Systems.levelsys import levelling
import os
from Systems.gettext_init import GettextInit

# Set up environment variables:
PREFIX = os.environ["BOT_PREFIX"]

# Set up gettext
_ = GettextInit(__file__).generate()


# Spam system class
class xpcolour(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def xpcolour(self, ctx, colour=None):
        await ctx.message.delete()
        if colour:
            levelling.update_one({"guildid": ctx.guild.id, "id": ctx.author.id}, {"$set": {"xp_colour": f"{colour}"}})
            embed = discord.Embed(title=_(":white_check_mark: **XP COLOUR CHANGED!**"),
                                  description=_("Your xp colour has been changed. If you type ") + PREFIX +
                                  _("rank and nothing appears, try a new hex code. \n**Example**:\n*#0000FF* = "
                                    "*Blue*"))
            embed.set_thumbnail(
                url="https://cdn.discordapp.com/attachments/812895798496591882/825363205853151252/ML_1.png")
            await ctx.send(embed=embed)
        elif colour is None:
            embed = discord.Embed(title=_(":x: **SOMETHING WENT WRONG!**"),
                                  description=_("Please make sure you typed a hex code in!."))
            await ctx.send(embed=embed)
            return


xpcolour.__doc__ = _('''\nxpcolour <hex code> \n\nAbout:\nThe XPColour command will allow you to change your rank 
cards xp bar colour to any hex code of your choosing.''')


# Sets-up the cog for help
def setup(client):
    client.add_cog(xpcolour(client))
