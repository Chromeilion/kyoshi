# Imports
import discord
from discord.ext import commands
from pymongo import MongoClient
import vacefron
import os
from dotenv import load_dotenv
from Systems.gettext_init import GettextInit
import distutils.util

# Set up gettext
_ = GettextInit(__file__).generate()

# Loads the .env file and gets the required information
load_dotenv()
MONGODB_URI = os.environ['MONGODB_URI']
COLLECTION = os.getenv("COLLECTION")
DB_NAME = os.getenv("DATABASE_NAME")
PREFIX = os.environ["BOT_PREFIX"]
XP_PER_LEVEL = int(os.environ["XP_PER_LEVEL"])
EMB_COLOUR = discord.Colour(int(os.environ["EMB_COLOUR"]))
LEVEL_UP_PING = bool(distutils.util.strtobool(os.environ['LEVEL_UP_PING']))

# Please enter your mongodb details in the .env file.
cluster = MongoClient(MONGODB_URI)
levelling = cluster[COLLECTION][DB_NAME]

# Vac-API, no need for altering!
vac_api = vacefron.Client()

# Set up gettext
_ = GettextInit(__file__).generate()


class levelsys(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, ctx):
        stats = levelling.find_one({"guildid": ctx.guild.id, "id": ctx.author.id})
        serverstats = levelling.find_one({"server": ctx.guild.id})
        if not ctx.author.bot:
            if serverstats is None:
                member = ctx.author
                newserver = {"server": ctx.guild.id, "xp_per_message": 10, "double_xp_role": "NA",
                             "level_channel": "private", "Antispam": False, "mutedRole": "Muted", "mutedTime": 300,
                             "warningMessages": 5, "muteMessages": 6, "ignoredRole": "Ignored"}
                overwrites = {
                    ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    ctx.guild.me: discord.PermissionOverwrite(read_messages=True)
                }
                await ctx.guild.create_text_channel('private', overwrites=overwrites)
                levelling.insert_one(newserver)
                channel = discord.utils.get(member.guild.channels, name="private")
                await channel.send(_(" Hey!\n\n You will only see this message **once**.\n To change the channel where "
                                   "levelup messages get sent to:\n\n`{PREFIX}levelchannel <channelname>` -- Please "
                                   "do NOT use the hashtag and enter any -'s!\n\nYou can also set a role which earns 2x "
                                   "XP by doing the following:\n\n`{PREFIX}doublexp <rolename>`\n\nYou can also add "
                                   "or remove roles after levelling up by doing the following\n\n`{PREFIX}role "
                                   "<add|remove> <level> <rolename>`\n\nYou can also change how much xp you earn per "
                                   "message by doing:\n\n`{PREFIX}xppermessage <amount>`\n\nFor help with "
                                   "commands:\n\n`{PREFIX}help` "))
            if stats is None:
                member = ctx.author
                user = f"<@{member.id}>"
                newuser = {"guildid": ctx.guild.id, "id": ctx.author.id, "tag": user, "xp": serverstats["xp_per_message"],
                           "rank": 1, "background": " ", "circle": False, "xp_colour": "#ffffff", "name": f"{ctx.author}",
                           "pfp": f"{ctx.author.avatar_url}", "warnings": 0}
                print(_("User:") + ctx.author.id + _("has been added to the database! "))
                levelling.insert_one(newuser)
            else:
                if PREFIX in ctx.content:
                    stats = levelling.find_one({"guildid": ctx.guild.id, "id": ctx.author.id})
                    xp = stats["xp"]
                    levelling.update_one({"guildid": ctx.guild.id, "id": ctx.author.id}, {"$set": {"xp": xp}})
                else:
                    stats = levelling.find_one({"server": ctx.guild.id})
                    if stats is None:
                        return
                    else:
                        user = ctx.author
                        role = discord.utils.get(ctx.guild.roles, name=serverstats["double_xp_role"])
                    if role in user.roles:
                        stats = levelling.find_one({"guildid": ctx.guild.id, "id": ctx.author.id})
                        xp = stats["xp"] + serverstats['xp_per_message'] * 2
                        levelling.update_one({"guildid": ctx.guild.id, "id": ctx.author.id}, {"$set": {"xp": xp}})
                    else:
                        stats = levelling.find_one({"guildid": ctx.guild.id, "id": ctx.author.id})
                        xp = stats["xp"] + serverstats['xp_per_message']
                        levelling.update_one({"guildid": ctx.guild.id, "id": ctx.author.id}, {"$set": {"xp": xp}})
                lvl = 0
                while True:
                    if xp < ((XP_PER_LEVEL / 2 * (lvl ** 2)) +
                             (XP_PER_LEVEL / 2 * lvl)):
                        break
                    lvl += 1
                xp -= ((XP_PER_LEVEL / 2 * ((lvl - 1) ** 2)) +
                       (XP_PER_LEVEL / 2 * (lvl - 1)))
                if stats["xp"] < 0:
                    levelling.update_one({"guildid": ctx.guild.id, "id": ctx.author.id}, {"$set": {"xp": 0}})
                if stats["rank"] != lvl:
                    levelling.update_one({"guildid": ctx.guild.id, "id": ctx.author.id}, {"$set": {"rank": lvl + 1}})
                    embed2 = discord.Embed(title=_(":tada: **LEVEL UP!**"),
                                           description=ctx.author.mention + _("just reached Level:") + str(lvl),
                                           colour=EMB_COLOUR)
                    xp = stats["xp"]
                    levelling.update_one({"guildid": ctx.guild.id, "id": ctx.author.id},
                                         {"$set": {"rank": lvl, "xp": xp + serverstats['xp_per_message'] * 2}})
                    print(_("User:") + str(ctx.author) + _("| Leveled UP To:") + str(lvl))
                    embed2.add_field(name=_("Next Level:"),
                                     value=f"`{int(XP_PER_LEVEL * 2 * ((1 / 2) * lvl))}xp`")
                    embed2.set_thumbnail(url=ctx.author.avatar_url)
                    member = ctx.author
                    channel = discord.utils.get(member.guild.channels, name=serverstats["level_channel"])
                    if LEVEL_UP_PING is True:
                        await channel.send(f"{ctx.author.mention}")
                    msg = await channel.send(embed=embed2)
                    level_roles = serverstats["role"]
                    level_roles_num = serverstats["level"]
                    for i in range(len(level_roles)):
                        if lvl == level_roles_num[i]:
                            await ctx.author.add_roles(
                                discord.utils.get(ctx.author.guild.roles, name=level_roles[i]))
                            embed = discord.Embed(title=_(":tada: **LEVEL UP**"),
                                                  description=ctx.author.mention + _("just reached Level:") + str(lvl),
                                                  colour=EMB_COLOUR)
                            embed.add_field(name=_("Next Level:"),
                                            value=f"`{int(XP_PER_LEVEL * 2 * ((1 / 2) * lvl))}xp`")
                            embed.add_field(name=_("Role Unlocked"), value=f"`{level_roles[i]}`")
                            print(_("User:") + str(ctx.author) + _("| Unlocked Role:") + str(level_roles[i]))
                            embed.set_thumbnail(url=ctx.author.avatar_url)
                            await msg.edit(embed=embed)
                        for i in range(len(level_roles)):
                            if lvl == level_roles_num[i]:
                                await ctx.author.add_roles(
                                    discord.utils.get(ctx.author.guild.roles, name=level_roles[i]))
                                embed = discord.Embed(title=_(":tada: **LEVEL UP**"),
                                                      description=ctx.author.mention + _("just reached Level:") + str(lvl),
                                                      colour=EMB_COLOUR)
                                embed.add_field(name=_("Next Level:"),
                                                value=f"`{int(XP_PER_LEVEL * 2 * ((1 / 2) * lvl))}xp`")
                                embed.add_field(name=_("Role Unlocked"), value=f"`{level_roles[i]}`")
                                print(_("User:") + str(ctx.author) + _("| Unlocked Role:") + str(level_roles[i]))
                                embed.set_thumbnail(url=ctx.author.avatar_url)
                                await msg.edit(embed=embed)

    on_message.__doc__ = _('''''')


def setup(client):
    client.add_cog(levelsys(client))

# End Of Level System
