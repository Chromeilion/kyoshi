import discord
from discord.ext import commands
from Systems.levelsys import levelling
from Systems.gettext_init import GettextInit


# Set up gettext
_ = GettextInit(__file__).generate()


# Spam system class
class circlepic(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def circlepic(self, ctx, value=None):
        await ctx.message.delete()
        if value == "True":
            levelling.update_one({"guildid": ctx.guild.id, "id": ctx.author.id}, {"$set": {"circle": True}})
            embed1 = discord.Embed(title=_(":white_check_mark: **PROFILE CHANGED!**"),
                                   description=_("Circle Profile Picture set to: `True`. Set to `False` to return to "
                                                 "default."))
            await ctx.channel.send(embed=embed1)
        elif value == "False":
            levelling.update_one({"guildid": ctx.guild.id, "id": ctx.author.id}, {"$set": {"circle": False}})
            embed2 = discord.Embed(title=_(":white_check_mark: **PROFILE CHANGED!**"),
                                   description=_("Circle Profile Picture set to: `False`. Set to `True` to change it to a "
                                                 "circle."))
            await ctx.channel.send(embed=embed2)
        elif value is None:
            embed3 = discord.Embed(title=_(":x: **SOMETHING WENT WRONG!**"),
                                   description=_("Please make sure you either typed: `True` or `False`."))
            await ctx.channel.send(embed=embed3)


circlepic.__doc__ = _('''\ncirclepic <True|False> \n\nAbout:\nThe Circlepic command will allow you to change your rank
cards profile picture to be circular if set to true.''')


# Sets-up the cog for help
def setup(client):
    client.add_cog(circlepic(client))
