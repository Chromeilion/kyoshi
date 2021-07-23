# kyoshi

A discord bot 

This bot was originally forked from https://github.com/KumosLab/Discord-Levels-Bot.
It additionally uses https://github.com/eibex/reaction-light for role react features.

The bot in its current state uses a mongodb database, as well as a local database. 
When updating, take care not to lose the local database, as you'll have to redo all your role react setup if you do. 

This documentation is a work in progress, if you'd like to see all commands, atm the best way is to go to the 
reaction-light or Discord-Levels-Bot repositories and see the commands there. 

The bot is coded in python 3.8, so having python 3.8 installed is the best option, however, it will probably work in
most new python versions. Pip is also needed in order to install all module requirements. Pip usually comes with python 
so you probably dont need to install it seperataly. 

You will also need a mongodb database. Simply sign up for a free cluster on there, then create a user for your bot. 
You can then click on "connect" on the main cluster dashboard, connect your application, and choose python 3.6+.
This will give you your mongodb uri, you just need to specify the username and password within the link where
it specifies it. 

To install, simply clone the repository or download a release. Then copy .env_template of your choosing into the root folder
of the project. Open up .env_template with your favourite text editor and put in all values, there are some defaults already
in there. 
Once done editing, rename the .env_template to .env.
Then run install.bat / install.sh or open up terminal, cd into the bot directory and run pip install -r requirements.txt

Once complete, either double click start.bat or open terminal, cd to bot directory and do "python main.py", if you get an error, 
try "python3 main.py".
