import discord
from discord.ext import commands
from Systems.levelsys import levelling
import os
from Systems.gettext_init import GettextInit

# Set up environment variables:

ERROR_EMB_COLOUR = discord.Colour(int(os.environ["ERROR_EMB_COLOUR"]))
SUCCESS_EMB_COLOUR = discord.Colour(int(os.environ["SUCCESS_EMB_COLOUR"]))

# Set up gettext
_ = GettextInit(__file__).generate()


# Spam system class
class fix(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def fix(self, ctx, type=None):
        counter = 0
        if type is None:
            embed = discord.Embed(title=_(":x: ERROR!"),
                                  description=_("You must enter a valid type to fix!\n\n**Example:**\n`{prefix}fix <users"
                                                "|server|kingdoms>`"),
                                  colour=SUCCESS_EMB_COLOUR)
            await ctx.send(embed=embed)
            return
        embed = discord.Embed(title=_(":white_check_mark: | Fixed User"),
                              colour=SUCCESS_EMB_COLOUR)
        msg = await ctx.send(embed=embed)
        if type == "users".lower():
            for member in ctx.guild.members:
                counter += 1
                levelling.update_one({"name": f"{member}", "guildid": ctx.guild.id},
                                     {"$set": {"tag": f"<@{member.id}>", "guildid": ctx.guild.id, "warnings": 0}})
                embed = discord.Embed(title=_(":white_check_mark: Fixed User |") + counter/ctx.guild.member_count,
                                      description=member,
                                      colour=SUCCESS_EMB_COLOUR)
                await msg.edit(embed=embed)
            embed = discord.Embed(title=_(":white_check_mark: | Fixed User |") + counter/ctx.guild.member_count,
                                  description=_("Fixing has completed."))
            await msg.edit(embed=embed)
        elif type == "server".lower():
            counter += 1
            levelling.update_one({"server": ctx.guild.id}, {"$set": {"Antispam": False, "mutedRole": "Muted",
                                                                     "mutedTime": 300, "warningMessages": 5,
                                                                     "muteMessages": 6, "ignoredRole": "Ignored"}})
            embed = discord.Embed(title=_(":white_check_mark: Fixing Server"),
                                  description=_("Fixing.."),
                                  colour=SUCCESS_EMB_COLOUR)
            await msg.edit(embed=embed)
            embed = discord.Embed(title=_(":white_check_mark: | Fixed Server "),
                                  description=_("Fixing has completed."))
            await msg.edit(embed=embed)
        elif type == "kingdoms".lower():
            for member in ctx.guild.members:
                counter += 1
                levelling.update_one({"name": "{member}", "guildid": ctx.guild.id},
                                     {"$set": {"healPotions": 0, "coins": 0}})
                embed = discord.Embed(title=_(":white_check_mark: Fixed User For Kingdoms |") +
                                      counter/ctx.guild.member_count, description={member},
                                      colour=SUCCESS_EMB_COLOUR)
                await msg.edit(embed=embed)
            embed = discord.Embed(title=_(":white_check_mark: | Fixed Kingdoms |") + counter/ctx.guild.member_count,
                                  description=_("Fixing has completed."))
            await msg.edit(embed=embed)


fix.__doc__ = _('''\nfix <users|server|kingdoms> \n\nAbout:\nThe Fix command will try and fix either users, 
the server you're in or support Kingdoms integration *Admin Only*\n\n*Note: This may not always work due to 
certain ways the bot has been built. If so, please do this manually.*''')


# Sets-up the cog for help
def setup(client):
    client.add_cog(fix(client))
