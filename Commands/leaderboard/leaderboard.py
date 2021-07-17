import discord
from discord.ext import commands
import os
from Systems.gettext_init import GettextInit
from Systems.levelsys import levelling
import json

SUCCESS_EMB_COLOUR = discord.Colour(int(os.environ["SUCCESS_EMB_COLOUR"]))
LEADERBOARD_ALIAS = json.loads(os.environ["LEADERBOARD_ALIAS"])
LEADERBOARD_AMOUNT = int(os.environ["LEADERBOARD_AMOUNT"])
LEADERBOARD_EMB_COLOUR = discord.Colour(int(os.environ["LEADERBOARD_EMB_COLOUR"]))
LEADERBOARD_IMAGE = os.environ["LEADERBOARD_IMAGE"]

# Set up gettext
_ = GettextInit(__file__).generate()


# Spam system class
class leaderboard(commands.Cog):
    def __init__(self, client):
        self.client = client

    # Leaderboard Command
    @commands.command(aliases=LEADERBOARD_ALIAS)
    async def leaderboard(self, ctx):
        rankings = levelling.find({"guildid": ctx.guild.id}).sort("xp", -1)
        i = 1
        con = LEADERBOARD_AMOUNT
        embed = discord.Embed(title=_(":trophy: Leaderboard | Top") + str(con), colour=LEADERBOARD_EMB_COLOUR)
        
        for x in rankings:
            try:
                temp = ctx.guild.get_member(x["id"])
                tempxp = x["xp"]
                templvl = x["rank"]
                embed.add_field(name=f"#{i}: {temp.name}",
                                value=_("Level:") + str(templvl) + _("\nTotal XP:") + str(tempxp), inline=True)
                embed.set_thumbnail(url=LEADERBOARD_IMAGE)
                i += 1
            except:
                pass
            if i == LEADERBOARD_AMOUNT + 1:
                break
        await ctx.channel.send(embed=embed)


leaderboard.__doc__ = _('''\nleaderboard \n\nAbout:\nThe Leaderboard command displays the Top {top} users in that 
server, sorted by XP.''')


# Sets-up the cog for help
def setup(client):
    client.add_cog(leaderboard(client))
