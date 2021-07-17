import discord
from discord.ext import commands
from Systems.levelsys import levelling
from Systems.gettext_init import GettextInit


# Set up gettext
_ = GettextInit(__file__).generate()


# Spam system class
class background(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def background(self, ctx, link=None):
        await ctx.message.delete()
        if link:
            levelling.update_one({"guildid": ctx.guild.id, "id": ctx.author.id}, {"$set": {"background": f"{link}"}})
            embed = discord.Embed(title=_(":white_check_mark: **BACKGROUND CHANGED!**"),
                                  description=_("Your profile background has been set successfully! If your background does "
                                              "not update, please try a new image."))
            embed.set_thumbnail(url=link)
            await ctx.channel.send(embed=embed)
        elif link is None:
            embed3 = discord.Embed(title=_(":x: **SOMETHING WENT WRONG!**"),
                                   description=_("Please make sure you entered a link."))
            await ctx.channel.send(embed=embed3)


background.__doc__ = _('''\nbackground <link> \n\nAbout:\nThe Background command will allow you to change your rank 
cards background to the image of your choosing.\n\n*Note: Some links may not work! If this is the case, send the 
image to discord, then copy the media link!*''')


# Sets-up the cog for help
def setup(client):
    client.add_cog(background(client))
