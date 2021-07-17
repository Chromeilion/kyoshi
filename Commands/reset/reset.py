import discord
from discord.ext import commands
from Systems.levelsys import levelling
import os
from Systems.gettext_init import GettextInit

# Set up variables from environment
PREFIX = os.environ["BOT_PREFIX"]
ERROR_EMB_COLOUR = discord.Colour(int(os.environ["ERROR_EMB_COLOUR"]))
SUCCESS_EMB_COLOUR = discord.Colour(int(os.environ["SUCCESS_EMB_COLOUR"]))

# Set up gettext
_ = GettextInit(__file__).generate()


# Spam system class
class reset(commands.Cog):
    def __init__(self, client):
        self.client = client

    # Reset Command
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def reset(self, ctx, user=None):
        if user:
            userget = user.replace('!', '')
            levelling.delete_one({"guildid": ctx.guild.id, "tag": userget})
            embed = discord.Embed(title=_(":white_check_mark: RESET USER"), description=_("Reset User:") + user,
                                  colour=SUCCESS_EMB_COLOUR)
            print(f"{userget} was reset!")
            await ctx.send(embed=embed)
        else:
            prefix = PREFIX
            embed2 = discord.Embed(title=_(":x: RESET USER FAILED"),
                                   description=_("Couldn't Reset! The User:") + user + _("doesn't exist or you didn't "
                                                                                         "mention a user!"),
                                   colour=ERROR_EMB_COLOUR)
            embed2.add_field(name=_("Example:"), value=prefix + _("reset") + ctx.message.author.mention)
            print(_("Resetting Failed. A user was either not declared or doesn't exist!"))
            await ctx.send(embed=embed2)


reset.__doc__ = _('''\nreset <@user> \n\nAbout:\nThe Reset command will allow you to reset any user back to the 
bottom level. *Admin Only*''')


# Sets-up the cog for help
def setup(client):
    client.add_cog(reset(client))
