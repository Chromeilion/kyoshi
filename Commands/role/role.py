import discord
from discord.ext import commands
from Systems.levelsys import levelling
import os
from Systems.gettext_init import GettextInit

# Set up environment variables:
ERROR_EMB_COLOUR = discord.Colour(int(os.environ["ERROR_EMB_COLOUR"]))
SUCCESS_EMB_COLOUR = discord.Colour(int(os.environ["SUCCESS_EMB_COLOUR"]))
PREFIX = os.environ["BOT_PREFIX"]

roles = []
level = []

# Set up gettext
_ = GettextInit(__file__).generate()

# Spam system class
class role(commands.Cog):
    def __init__(self, client):
        self.client = client

    # Reset Command
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def role(self, ctx, addorremove=None, levels=None, *, rolez=None):
        stats = levelling.find_one({"server": ctx.guild.id})
        if stats is None:
            newserver = {"server": ctx.guild.id, f"role": " ", "level": 0}
            levelling.insert_one(newserver)
        if addorremove is None:

            embed2 = discord.Embed(title=_(":x: SETUP FAILED"),
                                   description=_("You need to define if you want to add or remove a role!"),
                                   colour=ERROR_EMB_COLOUR)
            embed2.add_field(name=_("Example:"), value=PREFIX + _("role <add|remove> <level> <rolename>`"))
            await ctx.send(embed=embed2)
        else:
            if addorremove == "add":
                if levels is None:
                    embed2 = discord.Embed(title=_(":x: SETUP FAILED"),
                                           description=_("You need to define a level that the user will unlock the "
                                                         "role at!"),
                                           colour=ERROR_EMB_COLOUR)
                    embed2.add_field(name=_("Example:"), value=PREFIX + _("role <add|remove> <level> <rolename>`"))
                    await ctx.send(embed=embed2)
                    return
                else:
                    roles.append(str(rolez))
                    if rolez is None:
                        embed2 = discord.Embed(title=_(":x: SETUP FAILED"),
                                               description=_("You need to define a role the user unlocks!"),
                                               colour=ERROR_EMB_COLOUR)
                        embed2.add_field(name=_("Example:"), value=PREFIX + _("role <add|remove> <level> <rolename>`"))
                        await ctx.send(embed=embed2)
                        return
                    else:
                        level.append(int(levels))

                        levelling.update_one({"server": ctx.guild.id}, {"$set": {f"role": roles, "level": level}})
                        embed = discord.Embed(title=_(":white_check_mark: ADDED ROLE!"),
                                              description=_("Added Role:") + rolez + _("At Level:") + levels,
                                              colour=SUCCESS_EMB_COLOUR)
                        await ctx.send(embed=embed)
            elif addorremove == "remove":
                if rolez is None:
                    embed2 = discord.Embed(title=_(":x: SETUP FAILED"),
                                           description=_("You need to define a role name!"),
                                           colour=ERROR_EMB_COLOUR)
                    embed2.add_field(name=_("Example:"), value=PREFIX + _("role <add|remove> <levele> <rolename>`"))
                    await ctx.send(embed=embed2)
                    return
                else:
                    roles.remove(str(rolez))
                    if levels is None:
                        embed2 = discord.Embed(title=_(":x: SETUP FAILED"),
                                               description=_("You need to define a level the user unlocks the level!"),
                                               colour=ERROR_EMB_COLOUR)
                        embed2.add_field(name=_("Example:"), value=PREFIX + _("role <add|remove> <rolename> <level>`"))
                        await ctx.send(embed=embed2)
                        return
                    else:
                        level.remove(int(levels))
                        stats = levelling.find_one({"server": ctx.guild.id})
                        levelling.update_one({"server": ctx.guild.id}, {"$set": {"role": roles, "level": level}})
                        await ctx.send({addorremove} + _("and") + rolez + _("and") + levels)
                        embed = discord.Embed(title=_(":white_check_mark: REMOVED ROLE"),
                                              description=_("Removed Role:") + rolez + _("At Level:") + levels,
                                              colour=SUCCESS_EMB_COLOUR)
                        await ctx.send(embed=embed)
                return


role.__doc__ = _('''\nrole <add|remove> <level> <rolename> \n\nAbout:\nThe Role command will let you add/remove 
roles when a user reaches the set level *Admin Only*''')


# Sets-up the cog for help
def setup(client):
    client.add_cog(role(client))
