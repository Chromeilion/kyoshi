import discord
from discord.ext import commands
from Systems.levelsys import levelling


# Set up gettext
from Systems.gettext_init import GettextInit
_ = GettextInit(__file__).generate()


# Spam system class
class addxp(commands.Cog):
    def __init__(self, client):
        self.client = client

    # Rank Command
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def addxp(self, ctx, xpamount=None, member=None):
        if member is None:
            user = f"<@!{ctx.author.id}>"
        else:
            user = member
        userget = user.replace('!', '')
        stats = levelling.find_one({"guildid": ctx.guild.id, "tag": userget})
        if xpamount:
            xp = stats["xp"]
            levelling.update_one({"guildid": ctx.guild.id, "tag": userget}, {"$set": {"xp": xp + int(xpamount)}})
            embed = discord.Embed(title=_(":white_check_mark: **ADDED XP!**"),
                                  description=_("Added") + xpamount + _("xp To:") + userget)
            await ctx.channel.send(embed=embed)
        elif xpamount is None:
            embed3 = discord.Embed(title=_(":x: **SOMETHING WENT WRONG!**"),
                                   description=_("Please make sure you entered an integer."))
            await ctx.channel.send(embed=embed3)
        return


addxp.__doc__ = _('''\nadd <amount> <user> \n\nAbout:\nThe add command will allow you to add xp to a
certain user. *Admin Only*''')


# Sets-up the cog for rank
def setup(client):
    client.add_cog(addxp(client))
