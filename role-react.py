"""
MIT License

Copyright (c) 2019-2021 eibex

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os
import datetime
import asyncio
from shutil import copy
from sys import platform
import discord
from discord.ext import tasks
import Systems.levelsys
from core import database, activity, github, schema
from discord.ext import commands
from core import database, activity, github, schema, i18n

class RoleBot(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.directory = os.path.dirname(os.path.realpath(__file__))
        with open(f"{self.directory}/.version") as f:
            __version__ = f.read().rstrip("\n").rstrip("\r")
        self.logo = "https://cdn.discordapp.com/attachments/671738683623473163/693451064904515645/spell_holy_weaponmastery.jpg"
        self.prefix = os.environ["BOT_PREFIX"]
        self.language = "en-gb"
        self.botcolour = discord.Colour(int("0xffff00", 16))
        self.folder = f"{self.directory}/files"
        self.language = "en-gb"
        self.response = i18n.Response(f"{self.folder}/i18n", self.language, self.prefix)
        self.botname = "kyoshi"
        self.activities_file = f"{self.directory}/files/activities.csv"
        self.activities = activity.Activities(self.activities_file)
        self.db_file = f"{self.directory}/files/reactionlight.db"
        self.db = database.Database(self.db_file)
        self.botcolour = discord.Colour(int(os.environ["EMB_COLOUR"]))

    class Locks:
        def __init__(self):
            self.locks = {}
            self.main_lock = asyncio.Lock()

        async def get_lock(self, user_id):
            async with self.main_lock:
                if not user_id in self.locks:
                    self.locks[user_id] = asyncio.Lock()

                return self.locks[user_id]

    lock_manager = Locks()

    def isadmin(self, member, guild_id):
        # Checks if command author has an admin role that was added with rl!admin
        admins = self.db.get_admins(guild_id)

        if isinstance(admins, Exception):
            print(self.response.get("db-error-admin-check").format(exception=admins))
            return False

        try:
            member_roles = [role.id for role in member.roles]
            return [admin_role for admin_role in admins if admin_role in member_roles]

        except AttributeError:
            # Error raised from 'fake' users, such as webhooks
            return False

    async def getchannel(self, channel_id):
        channel = self.client.get_channel(channel_id)

        if not channel:
            channel = await self.client.fetch_channel(channel_id)

        return channel

    async def getguild(self, guild_id):
        guild = self.client.get_guild(guild_id)

        if not guild:
            guild = await self.client.fetch_guild(guild_id)

        return guild

    async def getuser(self, user_id):
        user = self.client.get_user(user_id)

        if not user:
            user = await self.client.fetch_user(user_id)

        return user

    def restart(self):
        # Create a new python process of bot.py and stops the current one
        os.chdir(self.directory)
        python = "python" if platform == "win32" else "python3"
        cmd = os.popen(f"nohup {python} main.py &")
        cmd.close()

    async def database_updates(self):
        handler = schema.SchemaHandler(self.db_file, self.client)
        if handler.version == 0:
            handler.zero_to_one()
            messages = self.db.fetch_all_messages()
            for message in messages:
                channel_id = message[1]
                channel = await self.getchannel(channel_id)
                self.db.add_guild(channel.id, channel.guild.id)

        if handler.version == 1:
            handler.one_to_two()

        if handler.version == 2:
            handler.two_to_three()

    async def system_notification(self, guild_id, text, embed=None):
        # Send a message to the system channel (if set)
        if guild_id:
            server_channel = discord.utils.get(Systems.levelsys.ctx.author.guild.channels, name="private")

            if isinstance(server_channel, Exception):
                await self.system_notification(
                    None,
                    self.response.get("db-error-fetching-systemchannels-server").format(
                        exception=server_channel, text=text
                    ),
                )
                return

            if server_channel:
                server_channel = server_channel[0][0]

            if server_channel:
                try:
                    target_channel = await self.getchannel(server_channel)
                    if embed:
                        await target_channel.send(text, embed=embed)
                    else:
                        await target_channel.send(text)

                except discord.Forbidden:
                    await self.system_notification(None, text)

            else:
                if embed:
                    await self.system_notification(None, text, embed=embed)
                else:
                    await self.system_notification(None, text)

        elif system_channel:
            try:
                target_channel = await self.getchannel(system_channel)
                if embed:
                    await target_channel.send(text, embed=embed)
                else:
                    await target_channel.send(text)

            except discord.NotFound:
                print(self.response.get("systemchannel-404"))

            except discord.Forbidden:
                print(self.response.get("systemchannel-403"))

        else:
            print(text)

    async def formatted_channel_list(self, channel):
        all_messages = self.db.fetch_messages(channel.id)
        if isinstance(all_messages, Exception):
            await self.system_notification(
                channel.guild.id,
                self.response.get("db-error-fetching-messages").format(exception=all_messages),
            )
            return

        formatted_list = []
        counter = 1
        for msg_id in all_messages:
            try:
                old_msg = await channel.fetch_message(int(msg_id))

            except discord.NotFound:
                # Skipping reaction-role messages that might have been deleted without updating CSVs
                continue

            entry = (
                f"`{counter}`"
                f" {old_msg.embeds[0].title if old_msg.embeds else old_msg.content}"
            )
            formatted_list.append(entry)
            counter += 1

        return formatted_list

    @tasks.loop(hours=24)
    async def cleandb(self):
        # Cleans the database by deleting rows of reaction role messages that don't exist anymore
        messages = self.db.fetch_all_messages()
        guilds = self.db.fetch_all_guilds()
        # Get the cleanup queued guilds
        cleanup_guild_ids = self.db.fetch_cleanup_guilds(guild_ids_only=True)

        if isinstance(messages, Exception):
            await self.system_notification(
                None,
                self.response.get("db-error-fetching-cleaning").format(exception=messages),
            )
            return

        for message in messages:
            try:
                channel_id = message[1]
                channel = await self.client.fetch_channel(channel_id)

                await channel.fetch_message(message[0])

            except discord.NotFound as e:
                # If unknown channel or unknown message
                if e.code == 10003 or e.code == 10008:
                    delete = self.db.delete(message[0])

                    if isinstance(delete, Exception):
                        await self.system_notification(
                            channel.guild.id,
                            self.response.get("db-error-fetching-cleaning").format(exception=delete),
                        )
                        return

                    await self.system_notification(
                        channel.guild.id,
                        self.response.get("db-message-delete-success").format(
                            message_id=message, channel=channel.mention
                        ),
                    )

            except discord.Forbidden:
                # If we can't fetch the channel due to the bot not being in the guild or permissions we usually cant mention it or get the guilds id using the channels object
                await self.system_notification(
                    message[3],
                    self.response.get("db-forbidden-message").format(message_id=message[0], channel_id=message[1]),
                )

        if isinstance(guilds, Exception):
            await self.system_notification(
                None, self.response.get("db-error-fetching-cleaning-guild").format(exception=guilds)
            )
            return

        for guild_id in guilds:
            try:
                await self.client.fetch_guild(guild_id)
                if guild_id in cleanup_guild_ids:
                    self.db.remove_cleanup_guild(guild_id)

            except discord.Forbidden:
                # If unknown guild
                if guild_id in cleanup_guild_ids:
                    continue
                else:
                    self.db.add_cleanup_guild(
                        guild_id, round(datetime.datetime.utcnow().timestamp())
                    )

        cleanup_guilds = self.db.fetch_cleanup_guilds()

        if isinstance(cleanup_guilds, Exception):
            await self.system_notification(
                None, self.response.get("db-error-fetching-cleanup-guild").format(exception=cleanup_guilds)
            )
            return

        current_timestamp = round(datetime.datetime.utcnow().timestamp())
        for guild in cleanup_guilds:
            if int(guild[1]) - current_timestamp <= -86400:
                # The guild has been invalid / unreachable for more than 24 hrs, try one more fetch then give up and purge the guilds database entries
                try:
                    await self.client.fetch_guild(guild[0])
                    self.db.remove_cleanup_guild(guild[0])
                    continue

                except discord.Forbidden:
                    delete = self.db.remove_guild(guild[0])
                    delete2 = self.db.remove_cleanup_guild(guild[0])
                    if isinstance(delete, Exception):
                        await self.system_notification(
                            None,
                            self.response.get("db-error-deleting-cleaning-guild").format(exception=delete),
                        )
                        return

                    elif isinstance(delete2, Exception):
                        await self.system_notification(
                            None,
                            self.response.get("db-error-deleting-cleaning-guild").format(
                                exception=delete2
                            ),
                        )
                        return

    @tasks.loop(hours=6)
    async def check_cleanup_queued_guilds(self):
        cleanup_guild_ids = self.db.fetch_cleanup_guilds(guild_ids_only=True)
        for guild_id in cleanup_guild_ids:
            try:
                await self.client.fetch_guild(guild_id)
                self.db.remove_cleanup_guild(guild_id)

            except discord.Forbidden:
                continue

    @commands.Cog.listener()
    async def on_ready(self):
        print("Reaction Light ready!")
        await self.database_updates()
        self.cleandb.start()
        self.check_cleanup_queued_guilds.start()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        self.db.remove_guild(guild.id)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        reaction = str(payload.emoji)
        msg_id = payload.message_id
        ch_id = payload.channel_id
        user_id = payload.user_id
        guild_id = payload.guild_id
        exists = self.db.exists(msg_id)

        async with (await self.lock_manager.get_lock(user_id)):
            if isinstance(exists, Exception):
                await self.system_notification(
                    guild_id, self.response.get("db-error-reaction-add").format(exception=exists)
                )

            elif exists:
                # Checks that the message that was reacted to is a reaction-role message managed by the bot
                reactions = self.db.get_reactions(msg_id)

                if isinstance(reactions, Exception):
                    await self.system_notification(
                        guild_id, self.response.get("db-error-reaction-get").format(exception=reactions)
                    )
                    return

                ch = await self.getchannel(ch_id)
                msg = await ch.fetch_message(msg_id)
                user = await self.getuser(user_id)
                if reaction not in reactions:
                    # Removes reactions added to the reaction-role message that are not connected to any role
                    await msg.remove_reaction(reaction, user)

                else:
                    # Gives role if it has permissions, else 403 error is raised
                    role_id = reactions[reaction]
                    server = await self.getguild(guild_id)
                    member = server.get_member(user_id)
                    role = discord.utils.get(server.roles, id=role_id)
                    if user_id != self.client.user.id:
                        unique = self.db.isunique(msg_id)
                        if unique:
                            for existing_reaction in msg.reactions:
                                if str(existing_reaction.emoji) == reaction:
                                    continue
                                async for reaction_user in existing_reaction.users():
                                    if reaction_user.id == user_id:
                                        await msg.remove_reaction(existing_reaction, user)
                                        # We can safely break since a user can only have one reaction at once
                                        break

                        try:
                            await member.add_roles(role)
                            notify = self.db.notify(guild_id)
                            if isinstance(notify, Exception):
                                await self.system_notification(
                                    guild_id,
                                    self.response.get("db-error-notification-check").format(
                                        exception=notify
                                    ),
                                )
                                return

                            if notify:
                                await user.send(
                                    self.response.get("new-role-dm").format(role_name=role.name)
                                )

                        except discord.Forbidden:
                            await self.system_notification(
                                guild_id, self.response.get("permission-error-add")
                            )

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        reaction = str(payload.emoji)
        msg_id = payload.message_id
        user_id = payload.user_id
        guild_id = payload.guild_id
        exists = self.db.exists(msg_id)

        if isinstance(exists, Exception):
            await self.system_notification(
                guild_id, self.response.get("db-error-reaction-remove").format(exception=exists)
            )

        elif exists:
            # Checks that the message that was unreacted to is a reaction-role message managed by the bot
            reactions = self.db.get_reactions(msg_id)

            if isinstance(reactions, Exception):
                await self.system_notification(
                    guild_id, self.response.get("db-error-reaction-get").format(exception=reactions)
                )

            elif reaction in reactions:
                role_id = reactions[reaction]
                # Removes role if it has permissions, else 403 error is raised
                server = await self.getguild(guild_id)
                member = server.get_member(user_id)

                if not member:
                    member = await server.fetch_member(user_id)

                role = discord.utils.get(server.roles, id=role_id)
                try:
                    await member.remove_roles(role)
                    notify = self.db.notify(guild_id)
                    if isinstance(notify, Exception):
                        await self.system_notification(
                            guild_id,
                            self.response.get("db-error-notification-check").format(exception=notify),
                        )
                        return

                    if notify:
                        await member.send(self.response.get("removed-role-dm").format(role_name=role.name))

                except discord.Forbidden:
                    await self.system_notification(
                        guild_id, self.response.get("permission-error-remove")
                    )

    @commands.command(name="create")
    async def new(self, ctx):
        if self.isadmin(ctx.message.author, ctx.guild.id):
            sent_initial_message = await ctx.send(self.response.get("new-reactionrole-init"))
            rl_object = {}
            cancelled = False

            def check(message):
                return message.author.id == ctx.message.author.id and message.content != ""

            if not cancelled:
                error_messages = []
                user_messages = []
                sent_reactions_message = await ctx.send(
                    self.response.get("new-reactionrole-roles-emojis")
                )
                rl_object["reactions"] = {}
                try:
                    while True:
                        reactions_message = await self.client.wait_for(
                            "message", timeout=120, check=check
                        )
                        user_messages.append(reactions_message)
                        if reactions_message.content.lower() != "done":
                            reaction = (reactions_message.content.split())[0]
                            try:
                                role = reactions_message.role_mentions[0].id
                            except IndexError:
                                error_messages.append(
                                    (await ctx.send(self.response.get("new-reactionrole-error")))
                                )
                                continue

                            if reaction in rl_object["reactions"]:
                                error_messages.append(
                                    (
                                        await ctx.send(
                                            self.response.get("new-reactionrole-already-used")
                                        )
                                    )
                                )
                                continue
                            else:
                                try:
                                    await reactions_message.add_reaction(reaction)
                                    rl_object["reactions"][reaction] = role
                                except discord.HTTPException:
                                    error_messages.append(
                                        (
                                            await ctx.send(
                                                self.response.get("new-reactionrole-emoji-403")
                                            )
                                        )
                                    )
                                    continue
                        else:
                            break
                except asyncio.TimeoutError:
                    await ctx.author.send(self.response.get("new-reactionrole-timeout"))
                    cancelled = True
                finally:
                    await sent_reactions_message.delete()
                    for message in error_messages + user_messages:
                        await message.delete()

            if not cancelled:
                sent_limited_message = await ctx.send(
                    self.response.get("new-reactionrole-limit")
                )

                def reaction_check(payload):
                    return (
                            payload.member.id == ctx.message.author.id
                            and payload.message_id == sent_limited_message.id
                            and (str(payload.emoji) == "🔒" or str(payload.emoji) == "♾️")
                    )

                try:
                    await sent_limited_message.add_reaction("🔒")
                    await sent_limited_message.add_reaction("♾️")
                    limited_message_response_payload = await self.client.wait_for(
                        "raw_reaction_add", timeout=120, check=reaction_check
                    )

                    if str(limited_message_response_payload.emoji) == "🔒":
                        rl_object["limit_to_one"] = 1
                    else:
                        rl_object["limit_to_one"] = 0
                except asyncio.TimeoutError:
                    await ctx.author.send(self.response.get("new-reactionrole-timeout"))
                    cancelled = True
                finally:
                    await sent_limited_message.delete()

            if not cancelled:
                sent_oldmessagequestion_message = await ctx.send(
                    self.response.get("new-reactionrole-old-or-new").format(bot_mention=self.client.user.mention)
                )

                def reaction_check2(payload):
                    return (
                            payload.member.id == ctx.message.author.id
                            and payload.message_id == sent_oldmessagequestion_message.id
                            and (str(payload.emoji) == "🗨️" or str(payload.emoji) == "🤖")
                    )

                try:
                    await sent_oldmessagequestion_message.add_reaction("🗨️")
                    await sent_oldmessagequestion_message.add_reaction("🤖")
                    oldmessagequestion_response_payload = await self.client.wait_for(
                        "raw_reaction_add", timeout=120, check=reaction_check2
                    )

                    if str(oldmessagequestion_response_payload.emoji) == "🗨️":
                        rl_object["old_message"] = True
                    else:
                        rl_object["old_message"] = False
                except asyncio.TimeoutError:
                    await ctx.author.send(self.response.get("new-reactionrole-timeout"))
                    cancelled = True
                finally:
                    await sent_oldmessagequestion_message.delete()

            if not cancelled:
                error_messages = []
                user_messages = []
                if rl_object["old_message"]:
                    sent_oldmessage_message = await ctx.send(
                        self.response.get("new-reactionrole-which-message").format(
                            bot_mention=self.client.user.mention
                        )
                    )

                    def reaction_check3(payload):
                        return (
                                payload.member.id == ctx.message.author.id
                                and payload.guild_id == sent_oldmessage_message.guild.id
                                and str(payload.emoji) == "🔧"
                        )

                    try:
                        while True:
                            oldmessage_response_payload = await self.client.wait_for(
                                "raw_reaction_add", timeout=120, check=reaction_check3
                            )
                            try:
                                try:
                                    channel = await self.getchannel(
                                        oldmessage_response_payload.channel_id
                                    )
                                except discord.InvalidData:
                                    channel = None
                                except discord.HTTPException:
                                    channel = None

                                if channel is None:
                                    raise discord.NotFound
                                try:
                                    message = await channel.fetch_message(
                                        oldmessage_response_payload.message_id
                                    )
                                except discord.HTTPException:
                                    raise discord.NotFound
                                try:
                                    await message.add_reaction("👌")
                                    await message.remove_reaction("👌", message.guild.me)
                                    await message.remove_reaction("🔧", ctx.author)
                                except discord.HTTPException:
                                    raise discord.NotFound
                                if self.db.exists(message.id):
                                    raise ValueError
                                rl_object["message"] = dict(
                                    message_id=message.id,
                                    channel_id=message.channel.id,
                                    guild_id=message.guild.id,
                                )
                                final_message = message
                                break
                            except discord.NotFound:
                                error_messages.append(
                                    (
                                        await ctx.send(
                                            self.response.get(
                                                "new-reactionrole-permission-error"
                                            ).format(bot_mention=self.client.user.mention)
                                        )
                                    )
                                )
                            except ValueError:
                                error_messages.append(
                                    (
                                        await ctx.send(
                                            self.response.get("new-reactionrole-already-exists")
                                        )
                                    )
                                )
                    except asyncio.TimeoutError:
                        await ctx.author.send(self.response.get("new-reactionrole-timeout"))
                        cancelled = True
                    finally:
                        await sent_oldmessage_message.delete()
                        for message in error_messages:
                            await message.delete()
                else:
                    sent_channel_message = await ctx.send(
                        self.response.get("new-reactionrole-target-channel")
                    )
                    try:
                        while True:
                            channel_message = await self.client.wait_for(
                                "message", timeout=120, check=check
                            )
                            if channel_message.channel_mentions:
                                rl_object[
                                    "target_channel"
                                ] = channel_message.channel_mentions[0]
                                break
                            else:
                                error_messages.append(
                                    (
                                        await message.channel.send(
                                            self.response.get("invalid-target-channel")
                                        )
                                    )
                                )
                    except asyncio.TimeoutError:
                        await ctx.author.send(self.response.get("new-reactionrole-timeout"))
                        cancelled = True
                    finally:
                        await sent_channel_message.delete()
                        for message in error_messages:
                            await message.delete()

            if not cancelled and "target_channel" in rl_object:
                error_messages = []
                selector_embed = discord.Embed(
                    title="Embed_title",
                    description="Embed_content",
                    colour=self.botcolour,
                )
                selector_embed.set_footer(text=f"{self.botname}", icon_url=self.logo)

                sent_message_message = await message.channel.send(
                    self.response.get("new-reactionrole-message-contents"),
                    embed=selector_embed,
                )
                try:
                    while True:
                        message_message = await self.client.wait_for(
                            "message", timeout=120, check=check
                        )
                        # I would usually end up deleting message_message in the end but users usually want to be able to access the
                        # format they once used incase they want to make any minor changes
                        msg_values = message_message.content.split(" // ")
                        # This whole system could also be re-done using wait_for to make the syntax easier for the user
                        # But it would be a breaking change that would be annoying for thoose who have saved their message commands
                        # for editing.
                        selector_msg_body = (
                            msg_values[0] if msg_values[0].lower() != "none" else None
                        )
                        selector_embed = discord.Embed(colour=self.botcolour)
                        selector_embed.set_footer(text=f"{self.botname}", icon_url=self.logo)

                        if len(msg_values) > 1:
                            if msg_values[1].lower() != "none":
                                selector_embed.title = msg_values[1]
                            if len(msg_values) > 2 and msg_values[2].lower() != "none":
                                selector_embed.description = msg_values[2]

                        # Prevent sending an empty embed instead of removing it
                        selector_embed = (
                            selector_embed
                            if selector_embed.title or selector_embed.description
                            else None
                        )

                        if selector_msg_body or selector_embed:
                            target_channel = rl_object["target_channel"]
                            sent_final_message = None
                            try:
                                sent_final_message = await target_channel.send(
                                    content=selector_msg_body, embed=selector_embed
                                )
                                rl_object["message"] = dict(
                                    message_id=sent_final_message.id,
                                    channel_id=sent_final_message.channel.id,
                                    guild_id=sent_final_message.guild.id,
                                )
                                final_message = sent_final_message
                                break
                            except discord.Forbidden:
                                error_messages.append(
                                    (
                                        await message.channel.send(
                                            self.response.get(
                                                "new-reactionrole-message-send-permission-error"
                                            ).format(channel_mention=target_channel.mention)
                                        )
                                    )
                                )
                except asyncio.TimeoutError:
                    await ctx.author.send(self.response.get("new-reactionrole-timeout"))
                    cancelled = True
                finally:
                    await sent_message_message.delete()
                    for message in error_messages:
                        await message.delete()

            if not cancelled:
                # Ait we are (almost) all done, now we just need to insert that into the database and add the reactions 💪
                try:
                    r = self.db.add_reaction_role(rl_object)
                except database.DuplicateInstance:
                    await ctx.send(self.response.get("new-reactionrole-already-exists"))
                    return

                if isinstance(r, Exception):
                    await self.system_notification(
                        ctx.message.guild.id,
                        self.response.get("db-error-new-reactionrole").format(exception=r),
                    )
                    return
                for reaction, _ in rl_object["reactions"].items():
                    await final_message.add_reaction(reaction)
                await ctx.message.add_reaction("✅")
            await sent_initial_message.delete()

            if cancelled:
                await ctx.message.add_reaction("❌")
        else:
            await ctx.send(self.response.get("new-reactionrole-noadmin"))

    @commands.command(name="edit")
    async def edit_selector(self, ctx):
        if self.isadmin(ctx.message.author, ctx.guild.id):
            # Reminds user of formatting if it is wrong
            msg_values = ctx.message.content.split()
            if len(msg_values) < 2:
                await ctx.send(self.response.get("edit-reactionrole-info"))
                return

            elif len(msg_values) == 2:
                try:
                    channel_id = ctx.message.channel_mentions[0].id

                except IndexError:
                    await ctx.send(response.get("edit-reactionrole-nochannel"))
                    return

                channel = await self.getchannel(channel_id)
                all_messages = await self.formatted_channel_list(channel)
                if len(all_messages) == 1:
                    await ctx.send(
                        self.response.get("edit-reactionrole-one").format(channel_name=channel.name)
                    )

                elif len(all_messages) > 1:
                    await ctx.send(
                        self.response.get("edit-reactionrole-instructions").format(
                            num_messages=len(all_messages), channel_name=channel.name, message_list="\n".join(all_messages)
                        )
                    )

                else:
                    await ctx.send(self.response.get("no-reactionrole-messages"))

            elif len(msg_values) > 2:
                try:
                    # Tries to edit the reaction-role message
                    # Raises errors if the channel sent was invalid or if the bot cannot edit the message
                    channel_id = ctx.message.channel_mentions[0].id
                    channel = await self.getchannel(channel_id)
                    msg_values = ctx.message.content.split(" // ")
                    selector_msg_number = msg_values[1]
                    all_messages = self.db.fetch_messages(channel_id)

                    if isinstance(all_messages, Exception):
                        await self.system_notification(
                            ctx.message.guild.id,
                            self.response.get("db-error-fetching-messages").format(message_ids=all_messages),
                        )
                        return

                    counter = 1
                    if all_messages:
                        message_to_edit_id = None
                        for msg_id in all_messages:
                            # Loop through all msg_ids and stops when the counter matches the user input
                            if str(counter) == selector_msg_number:
                                message_to_edit_id = msg_id
                                break

                            counter += 1

                    else:
                        await ctx.send(self.response.get("reactionrole-not-exists"))
                        return

                    if message_to_edit_id:
                        old_msg = await channel.fetch_message(int(message_to_edit_id))

                    else:
                        await ctx.send(self.response.get("select-valid-reactionrole"))
                        return
                    await old_msg.edit(suppress=False)
                    selector_msg_new_body = (
                        msg_values[2] if msg_values[2].lower() != "none" else None
                    )
                    selector_embed = discord.Embed()

                    if len(msg_values) > 3 and msg_values[3].lower() != "none":
                        selector_embed.title = msg_values[3]
                        selector_embed.colour = self.botcolour
                        selector_embed.set_footer(text=f"{self.botname}", icon_url=self.logo)

                    if len(msg_values) > 4 and msg_values[4].lower() != "none":
                        selector_embed.description = msg_values[4]
                        selector_embed.colour = self.botcolour
                        selector_embed.set_footer(text=f"{self.botname}", icon_url=self.logo)

                    try:
                        if selector_embed.title or selector_embed.description:
                            await old_msg.edit(
                                content=selector_msg_new_body, embed=selector_embed
                            )

                        else:
                            await old_msg.edit(content=selector_msg_new_body, embed=None)

                        await ctx.send(self.response.get("message-edited"))
                    except discord.Forbidden:
                        await ctx.send(self.response.get("other-author-error"))
                        return
                    except discord.HTTPException as e:
                        if e.code == 50006:
                            await ctx.send(self.response.get("empty-message-error"))

                        else:
                            guild_id = ctx.message.guild.id
                            await self.system_notification(guild_id, str(e))

                except IndexError:
                    await ctx.send(self.response.get("invalid-target-channel"))

                except discord.Forbidden:
                    await ctx.send(self.response.get("edit-permission-error"))

        else:
            await ctx.send(self.response.get("not-admin"))

    @commands.command(name="reaction")
    async def edit_reaction(self, ctx):
        if self.isadmin(ctx.message.author, ctx.guild.id):
            msg_values = ctx.message.content.split()
            mentioned_roles = ctx.message.role_mentions
            mentioned_channels = ctx.message.channel_mentions
            if len(msg_values) < 4:
                if not mentioned_channels:
                    await ctx.send(self.response.get("reaction-edit-info"))
                    return

                channel = ctx.message.channel_mentions[0]
                all_messages = await self.formatted_channel_list(channel)
                if len(all_messages) == 1:
                    await ctx.send(self.response.get("reaction-edit-one").format(channel_name=channel.name))
                    return

                elif len(all_messages) > 1:
                    await ctx.send(
                        self.response.get("reaction-edit-multi").format(
                            num_messages=len(all_messages), channel_name=channel.name, message_list="\n".join(all_messages)
                        )
                    )
                    return

                else:
                    await ctx.send(self.response.get("no-reactionrole-messages"))
                    return

            action = msg_values[1].lower()
            channel = ctx.message.channel_mentions[0]
            message_number = msg_values[3]
            reaction = msg_values[4]
            if action == "add":
                if mentioned_roles:
                    role = mentioned_roles[0]
                else:
                    await ctx.send(self.response.get("no-role-mentioned"))
                    return

            all_messages = self.db.fetch_messages(channel.id)
            if isinstance(all_messages, Exception):
                await self.system_notification(
                    ctx.message.guild.id,
                    self.response.get("db-error-fetching-messages").format(exception=all_messages),
                )
                return

            counter = 1
            if all_messages:
                message_to_edit_id = None
                for msg_id in all_messages:
                    # Loop through all msg_ids and stops when the counter matches the user input
                    if str(counter) == message_number:
                        message_to_edit_id = msg_id
                        break

                    counter += 1

            else:
                await ctx.send(self.response.get("reactionrole-not-exists"))
                return

            if message_to_edit_id:
                message_to_edit = await channel.fetch_message(int(message_to_edit_id))

            else:
                await ctx.send(self.response.get("select-valid-reactionrole"))
                return

            if action == "add":
                try:
                    # Check that the bot can actually use the emoji
                    await message_to_edit.add_reaction(reaction)

                except discord.HTTPException:
                    await ctx.send(self.response.get("new-reactionrole-emoji-403"))
                    return

                react = self.db.add_reaction(message_to_edit.id, role.id, reaction)
                if isinstance(react, Exception):
                    await self.system_notification(
                        ctx.message.guild.id,
                        self.response.get("db-error-add-reaction").format(
                            channel_mention=message_to_edit.channel.mention, exception=react
                        ),
                    )
                    return

                if not react:
                    await ctx.send(self.response.get("reaction-edit-already-exists"))
                    return

                await ctx.send(self.response.get("reaction-edit-add-success"))

            elif action == "remove":
                try:
                    await message_to_edit.clear_reaction(reaction)

                except discord.HTTPException:
                    await ctx.send(self.response.get("reaction-edit-invalid-reaction"))
                    return

                react = self.db.remove_reaction(message_to_edit.id, reaction)
                if isinstance(react, Exception):
                    await self.system_notification(
                        ctx.message.guild.id,
                        self.response.get("db-error-remove-reaction").format(
                            channel_mention=message_to_edit.channel.mention, exception=react
                        ),
                    )
                    return

                await ctx.send(self.response.get("reaction-edit-remove-success"))

        else:
            await ctx.send(self.response.get("not-admin"))

    @commands.command(name="systemchannel")
    async def set_systemchannel(self, ctx):
        if self.isadmin(ctx.message.author, ctx.guild.id):
            global system_channel
            msg = ctx.message.content.split()
            mentioned_channels = ctx.message.channel_mentions
            channel_type = None if len(msg) < 2 else msg[1].lower()
            if (
                    len(msg) < 3
                    or not mentioned_channels
                    or channel_type not in ["main", "server"]
            ):
                server_channel = self.db.fetch_systemchannel(ctx.guild.id)
                if isinstance(server_channel, Exception):
                    await self.system_notification(
                        None,
                        self.response.get("db-error-fetching-systemchannels").format(
                            exception=server_channel
                        ),
                    )
                    return

                if server_channel:
                    server_channel = server_channel[0][0]

                main_text = (
                    (await self.getchannel(system_channel)).mention if system_channel else "none"
                )
                server_text = (
                    (await self.getchannel(server_channel)).mention if server_channel else "none"
                )
                await ctx.send(
                    self.response.get("systemchannels-info").format(main_channel=main_text, server_channel=server_text)
                )
                return

            target_channel = mentioned_channels[0].id
            guild_id = ctx.message.guild.id

            server = await self.getguild(guild_id)
            bot_user = server.get_member(self.client.user.id)
            bot_permissions = (await self.getchannel(target_channel)).permissions_for(bot_user)
            writable = bot_permissions.read_messages
            readable = bot_permissions.view_channel
            if not writable or not readable:
                await ctx.send(self.response.get("permission-error-channel"))
                return

            if channel_type == "main":
                system_channel = target_channel

            elif channel_type == "server":
                add_channel = self.db.add_systemchannel(guild_id, target_channel)

                if isinstance(add_channel, Exception):
                    await self.system_notification(
                        guild_id,
                        self.response.get("db-error-adding-systemchannels").format(exception=add_channel),
                    )
                    return

            await ctx.send(self.response.get("systemchannels-success"))

        else:
            await ctx.send(self.response.get("not-admin"))

    @commands.command(name="notify")
    async def toggle_notify(self, ctx):
        if self.isadmin(ctx.message.author, ctx.guild.id):
            notify = self.db.toggle_notify(ctx.guild.id)
            if notify:
                await ctx.send(self.response.get("notifications-on"))
            else:
                await ctx.send(self.response.get("notifications-off"))

    @commands.is_owner()
    @commands.command(name="language")
    async def set_language(self, ctx):
        msg = ctx.message.content.split()
        args = len(msg) - 1
        available_languages = os.listdir(f"{self.directory}/files/i18n")
        available_languages = [
            i.replace(".json", "") for i in available_languages if i.endswith(".json")
        ]
        if args:
            new_language = msg[1].lower()
            if new_language in available_languages:
                global language
                global response
                language = new_language
                self.response.language = language
                await ctx.send(self.response.get("language-success"))
            else:
                await ctx.send(
                    self.response.get("language-not-exists").format(
                        available_languages=", ".join(available_languages)
                    )
                )
        else:
            await ctx.send(
                self.response.get("language-info").format(available_languages=", ".join(available_languages))
            )

    @commands.is_owner()
    @commands.command(name="colour")
    async def set_colour(self, ctx):
        msg = ctx.message.content.split()
        args = len(msg) - 1
        if args:
            global botcolour
            colour = msg[1]
            try:
                self.botcolour = discord.Colour(int(colour, 16))

                example = discord.Embed(
                    title=self.response.get("example-embed"),
                    description=self.response.get("example-embed-new-colour"),
                    colour=self.botcolour,
                )
                await ctx.send(self.response.get("colour-changed"), embed=example)

            except ValueError:
                await ctx.send(self.response.get("colour-hex-error"))

        else:
            await ctx.send(self.response.get("colour-hex-error"))

    @commands.is_owner()
    @commands.command(name="activity")
    async def add_activity(self, ctx):
        new_activity = ctx.message.content[(len(self.prefix) + len("activity")):].strip()
        if not activity:
            await ctx.send(self.response.get("activity-info"))

        elif "," in new_activity:
            await ctx.send(self.response.get("activity-no-commas"))

        else:
            self.activities.add(new_activity)
            await ctx.send(self.response.get("activity-success").format(new_activity=new_activity))

    @commands.is_owner()
    @commands.command(name="activitylist")
    async def list_activities(self, ctx):
        if self.activities.activity_list:
            formatted_list = []
            for item in self.activities.activity_list:
                formatted_list.append(f"`{item}`")

            await ctx.send(self.response.get("current-activities").format(activity_list="\n- ".join(formatted_list)))

        else:
            await ctx.send(self.response.get("no-current-activities"))

    @commands.is_owner()
    @commands.command(name="rm-activity")
    async def remove_activity(self, ctx):
        activity_to_delete = ctx.message.content[
                             (len(self.prefix) + len("rm-activity")):
                             ].strip()
        if not activity_to_delete:
            await ctx.send(self.response.get("rm-activity-info"))
            return

        removed = self.activities.remove(activity_to_delete)
        if removed:
            await ctx.send(self.response.get("rm-activity-success").format(activity_to_delete=activity_to_delete))

        else:
            await ctx.send(self.response.get("rm-activity-not-exists"))

    @commands.command(pass_context=True, name="admin")
    @commands.has_permissions(administrator=True)
    async def add_admin(self, ctx, role: discord.Role):
        # Adds an admin role ID to the database
        add = self.db.add_admin(role.id, ctx.guild.id)

        if isinstance(add, Exception):
            await self.system_notification(
                ctx.message.guild.id, self.response.get("db-error-admin-add").format(exception=add)
            )
            return

        await ctx.send(self.response.get("admin-add-success"))

    @add_admin.error
    async def add_admin_error(self, ctx, error):
        if isinstance(error, commands.RoleNotFound):
            await ctx.send(self.response.get("admin-invalid"))

    @commands.command(name="rm-admin")
    @commands.has_permissions(administrator=True)
    async def remove_admin(self, ctx, role: discord.Role):
        # Removes an admin role ID from the database
        remove = self.db.remove_admin(role.id, ctx.guild.id)

        if isinstance(remove, Exception):
            await self.system_notification(
                ctx.message.guild.id, self.response.get("db-error-admin-remove").format(exception=remove)
            )
            return

        await ctx.send(self.response.get("admin-remove-success"))

    @remove_admin.error
    async def remove_admin_error(self, ctx, error):
        if isinstance(error, commands.RoleNotFound):
            await ctx.send(self.response.get("admin-invalid"))

    @commands.command(name="adminlist")
    @commands.has_permissions(administrator=True)
    async def list_admin(self, ctx):
        # Lists all admin IDs in the database, mentioning them if possible
        admin_ids = self.db.get_admins(ctx.guild.id)

        if isinstance(admin_ids, Exception):
            await self.system_notification(
                ctx.message.guild.id,
                self.response.get("db-error-fetching-admins").format(exception=admin_ids),
            )
            return

        adminrole_objects = []
        for admin_id in admin_ids:
            adminrole_objects.append(
                discord.utils.get(ctx.guild.roles, id=admin_id).mention
            )

        if adminrole_objects:
            await ctx.send(self.response.get("adminlist-local").format(admin_list="\n- ".join(adminrole_objects)))
        else:
            await ctx.send(self.response.get("adminlist-local-empty"))

    @commands.command(name="version")
    async def print_version(self, ctx):
        if self.isadmin(ctx.message.author, ctx.guild.id):
            latest = await github.get_latest()
            changelog = await github.latest_changelog()
            em = discord.Embed(
                title=f"Reaction Light v{latest} - Changes",
                description=changelog,
                colour=self.botcolour,
            )
            em.set_footer(text=f"{self.botname}", icon_url=self.logo)
            await ctx.send(
                self.response.get("version").format(version=0.45, latest_version=latest),
                embed=em,
            )

        else:
            await ctx.send(self.response.get("not-admin"))

    @commands.is_owner()
    @commands.command(name="kill")
    async def kill(self, ctx):
        await ctx.send(self.response.get("shutdown"))
        await self.client.close()

    @commands.is_owner()
    @commands.command(name="restart")
    async def restart_cmd(self, ctx):
        if platform != "win32":
            self.restart()
            await ctx.send(self.response.get("restart"))
            await self.client.close()

        else:
            await ctx.send(self.response.get("windows-error"))

    @commands.is_owner()
    @commands.command(name="update")
    async def update(self, ctx):
        if platform != "win32":
            await ctx.send(self.response.get("attempting-update"))
            os.chdir(self.directory)
            cmd = os.popen("git fetch")
            cmd.close()
            cmd = os.popen("git pull")
            cmd.close()
            await ctx.send(self.response.get("database-backup"))
            copy(self.db_file, f"{self.db_file}.bak")
            self.restart()
            await ctx.send(self.response.get("restart"))
            await self.client.close()

        else:
            await ctx.send(self.response.get("windows-error"))


# Sets-up the cog
def setup(client):
    client.add_cog(RoleBot(client))
