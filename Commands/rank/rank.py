import discord
from discord.ext import commands
from Systems.levelsys import levelling
from Systems.levelsys import vac_api
import os
from Systems.gettext_init import GettextInit
import json

RANK_ALIAS = json.loads(os.environ["RANK_ALIAS"])
XP_PER_LEVEL = int(os.environ["XP_PER_LEVEL"])
ERROR_EMB_COLOUR = discord.Colour(int(os.environ["ERROR_EMB_COLOUR"]))
RANK_EMB_COLOUR = discord.Colour(int(os.environ["RANK_EMB_COLOUR"]))

# Set up gettext
_ = GettextInit(__file__).generate()


# Spam system class
class rank(commands.Cog):
    def __init__(self, client):
        self.client = client

    # Rank Command
    @commands.command(aliases=RANK_ALIAS)
    async def rank(self, ctx, member=None):
        if member is None:
            user = f"<@!{ctx.author.id}>"
        else:
            user = member
        userget = user.replace('!', '')
        stats = levelling.find_one({"guildid": ctx.message.guild.id, "tag": userget})
        if stats is None:
            embed = discord.Embed(description=_(":x: No Data Found!"),
                                  colour=ERROR_EMB_COLOUR)
            await ctx.channel.send(embed=embed)
        else:
            xp = stats["xp"]
            user_lvl = 0
            user_rank = 0
            while True:
                if xp < ((XP_PER_LEVEL / 2 * (user_lvl ** 2)) + (XP_PER_LEVEL / 2 * user_lvl)):
                    break
                user_lvl += 1
            xp -= ((XP_PER_LEVEL / 2 * (user_lvl - 1) ** 2) + (XP_PER_LEVEL / 2 * (user_lvl - 1)))
            rankings = levelling.find({"guildid": ctx.guild.id}).sort("xp", -1)
            for x in rankings:
                user_rank += 1
                if stats["id"] == x["id"]:
                    break
            levelling.update_one({"guildid": ctx.guild.id, "id": ctx.author.id},
                                 {'$set': {"pfp": f"{ctx.author.avatar_url}", "name": f"{ctx.author}"}})
            stats2 = levelling.find_one({"guildid": ctx.message.guild.id, "tag": userget})
            background = stats2["background"]
            circle = stats2["circle"]
            xpcolour = stats2["xp_colour"]
            member = ctx.author
            gen_card = await vac_api.rank_card(
                username=str(stats2['name']),
                avatar=stats['pfp'],
                level=int(user_lvl),
                rank=int(user_rank),
                current_xp=int(xp),
                next_level_xp=int(XP_PER_LEVEL * 2 * ((1 / 2) * user_lvl)),
                previous_level_xp=0,
                xp_color=str(xpcolour),
                custom_background=str(background),
                is_boosting=bool(member.premium_since),
                circle_avatar=circle
            )
            embed = discord.Embed(colour=RANK_EMB_COLOUR)
            embed.set_image(url=gen_card.url)
            await ctx.send(embed=embed)


# For help function
rank.__doc__ = _('''\nrank or rank <@user> \n\nAbout:\nThe Rank command will show the user their current level,
server ranking and how much xp you have. Your rank card can be customisable with other commands.''')


# Sets-up the cog for rank
def setup(client):
    client.add_cog(rank(client))
