import discord
from discord.ext import commands
import os
from Systems.gettext_init import GettextInit


# Set up gettext
_ = GettextInit(__file__).generate()

prefix = os.getenv("BOT_PREFIX")
owner = os.getenv("BOT_OWNER")
version = os.getenv("BOT_VERSION")


# Spam system class
class help(commands.Cog):
    def __init__(self, client):
        self.client = client

    # Help Command
    @commands.command(aliases=["h", "help_t"])
    async def help(self, ctx, *params):
        if not params:
            # starting to build embed
            emb = discord.Embed(title=_('Help'), color=0xc54245,
                                description=_("'Use") + prefix + _("<module>` to gain more information about that "
                                                                   "module :smiley:\n"))
        elif len(params) == 1:

            # iterating trough cogs
            for cog in self.client.cogs:
                # check if cog is the matching one
                if cog.lower() == params[0].lower():

                    # making title - getting description from doc-string below class
                    emb = discord.Embed(title=cog + _("- commands"), description=self.client.cogs[cog].__doc__,
                                        color=0xc54245)

                    # getting commands from cog
                    for command in self.client.get_cog(cog).get_commands():
                        # if cog is not hidden
                        if not command.hidden:
                            emb.add_field(name=f"{prefix}{command.name}", value=command.help, inline=False)
                    # found cog - breaking loop
                    break

            # if input not found
            # yes, for-loops have an else statement, it's called when no 'break' was issued
            else:
                emb = discord.Embed(title=_("What's that?!"),
                                    description=_("I've never heard from a module called") + params[0] + _("before :scream:"),
                                    color=0xc54245)

        # too many cogs requested - only one at a time allowed
        elif len(params) > 1:
            emb = discord.Embed(title=_("That's too much."),
                                description=_("Please request only one module at once :sweat_smile:"),
                                color=0xc54245)

        else:
            emb = discord.Embed(title=_("It's a magical place."),
                                description=_("I don't know how you got here. But I didn't see this coming at all.\n"
                                            "Would you please be so kind to report that issue to me on github?\n"
                                            "https://github.com/Chromeilion/Discord-Levels-Bot\n"
                                            "Thank you! ~Chrome"),
                                color=0xc54245)

        await ctx.send(embed=emb)


# Sets-up the cog for help
def setup(client):
    client.add_cog(help(client))
