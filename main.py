# Imports
from discord.ext import commands
from discord.ext.commands import CommandNotFound, MissingRequiredArgument, CommandInvokeError, MissingRole
import discord
import logging
import os
from dotenv import load_dotenv
import daiquiri
import glob

daiquiri.setup(level=logging.INFO)
load_dotenv()

# Opens the config and reads it, no need for changes unless you'd like to change the library (no need to do so unless
# having issues with ruamel)


# Command Prefix + Removes the default discord.py help command
prefix = os.environ["BOT_PREFIX"]
client = commands.Bot(command_prefix=prefix, intents=discord.Intents.all(), case_insensitive=True)
client.remove_command('help')

# sends discord logging files which could potentially be useful for catching errors.
logging = daiquiri.getLogger(__name__)
logging.debug('Started Logging')
logging.info('Connecting to Discord.')


@client.event  # On Bot Startup, Will send some details about the bot and sets it's activity and status. Feel free to
# remove the print messages, but keep everything else.
async def on_ready():
    config_status = os.environ['BOT_STATUS_TEXT']
    config_activity = os.environ['BOT_ACTIVITY']
    activity = discord.Game(name=config_status)
    logging.info('Getting Bot Activity from Config')
    print("If you encounter any bugs, please let me know.")
    print('------')
    print('Logged In As:')
    print(f"Username: {client.user.name}\nID: {client.user.id}")
    print('------')
    print(f"Status: {config_status}\nActivity: {config_activity}")
    print('------')
    await client.change_presence(status=config_activity, activity=activity)


@client.event  # Stops Certain errors from being thrown in the console (Don't remove as it'll cause command error
# messages to not send! - Only remove if adding features and needed for testing (Don't forget to re-add)!)
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        logging.error('Command Not Found')
        return
    if isinstance(error, MissingRequiredArgument):
        logging.error('Argument Error - Missing Arguments')
        return
    if isinstance(error, CommandInvokeError):
        logging.error('Command Invoke Error')
        return
    if isinstance(error, MissingRole):
        logging.error('A user has missing roles!')
        return
    if isinstance(error, PermissionError):
        logging.error('A user has missing permissions!')
    if isinstance(error, KeyError):
        logging.error('Key Error')
        return
    if isinstance(error, TypeError):
        logging.error('Type Error - Probably caused as server was being registered while anti-spam or double-xp tried '
                      'triggering')
    raise error


logging.info("------------- Loading -------------")
for path in glob.glob("Commands/*/*"):
    folders = []
    while 1:
        path, folder = os.path.split(path)

        if folder != "":
            folders.append(folder)
        elif path == "":
            break
    folders.reverse()
    fn = ".".join(folders)

    if fn.endswith(".py"):
        logging.info(f"Loading {fn}")
        client.load_extension(fn[:-3:])
        logging.info(f"Loaded {fn}")

logging.info(f"Loading Level System")
client.load_extension("Systems.levelsys")
logging.info(f"Loaded Level System")

if os.environ['BOT_ANTISPAM_SYSTEM'] is True:
    logging.info(f"Loading Anti-Spam System")
    client.load_extension("Systems.spamsys")
    logging.info(f"Loaded Anti-Spam System")

logging.info("------------- Finished Loading -------------")

# Uses the bot token to login, so don't remove this.
token = os.getenv("DISCORD_TOKEN")
client.run(token)

# End Of Main
