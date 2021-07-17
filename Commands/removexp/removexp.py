import discord
from discord.ext import commands
from Systems.levelsys import levelling
from Systems.gettext_init import GettextInit


# Set up gettext
_ = GettextInit(__file__).generate()


# Spam system class
class removexp(commands.Cog):
    def __init__(self, client):
        self.client = client

    # Rank Command
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def removexp(self, ctx, xpamount=None, member=None):
        if member is None:
            user = f"<@!{ctx.author.id}>"
        else:
            user = member
        user = user.replace('!', '')
        stats = levelling.find_one({"guildid": ctx.guild.id, "tag": user})
        if xpamount:
            xp = stats["xp"]
            levelling.update_one({"guildid": ctx.guild.id, "tag": user}, {"$set": {"xp": xp - int(xpamount)}})
            embed = discord.Embed(title=_(":white_check_mark: **REMOVED XP!**"),
                                  description=_("Removed") + xpamount + _("xp From:") + user)
            await ctx.channel.send(embed=embed)
        elif xpamount is None:
            embed3 = discord.Embed(title=_(":x: **SOMETHING WENT WRONG!**"),
                                   description=_("Please make sure you entered an integer."))
            await ctx.channel.send(embed=embed3)
        return


removexp.__doc__ = _('''\n<add|remove>xp <amount> <user> \n\nAbout:\nThe <add|remove>xp command will allow you to 
add or remove xp to a certain user. *Admin Only*''')


# Sets-up the cog for rank
def setup(client):
    client.add_cog(removexp(client))
