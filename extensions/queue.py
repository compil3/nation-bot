import logging
import re
import time
from datetime import datetime
from typing import TYPE_CHECKING
from xmlrpc.client import Boolean

import aiohttp
import orjson
from beanie import Document
from naff import (ActionRow, Button, ButtonStyles, ComponentContext, Embed,
                  Extension, Guild, InteractionContext, IntervalTrigger,
                  Member, Modal, ModalContext, ParagraphText, Permissions,
                  ShortText, Task, Timestamp, component_callback, listen,
                  logger_name, slash_command, ThreadChannel, Context)
from naff.ext.paginators import Paginator
from naff.models.naff.converters import MemberConverter, RoleConverter

if TYPE_CHECKING:
    from main import Bot


logger = logging.getLogger(logger_name)


class VerificationQueue(Document):
    discord_id: int
    discord_name: str
    gamertag: str
    status: str
    reason: str
    updated: datetime
    discord_thread: int

    class Collection:
        name = "verification_queue"

#Verification queue system
class Queue(Extension):
    def __init__(self, *args, **kwargs):
        self.check_queue.start()

    # TODO: Add task to check gamer tags in verification_queue every 5 hours, if the gamer tag is found, add 'Player' role to user, remove from queue, send a "register" msg to user.
    @slash_command(
        "queue",
        description="Discord Verification Queue",
        scopes=[689119429375819951, 442081251441115136],
        default_member_permissions=Permissions.MANAGE_ROLES
    )
    async def waiting_queue(self, ctx: InteractionContext):
        await ctx.defer(ephemeral=True)

        embeds = []
        # Grab the users gamertag from queue, search website for it, if found automatically add 'Player' role.
        startTime = time.time()
        async for playerInDb in VerificationQueue.find(VerificationQueue.status == "New"):
            channel: ThreadChannel =  await self.bot.fetch_channel(playerInDb.discord_thread)
            async with aiohttp.ClientSession() as session:
                if await fetch_api(self,playerInDb, session):
                    logger.info(f"Player in db found.\n{playerInDb.discord_name} - {playerInDb.gamertag}")
                    member = await Guild.fetch_member(ctx.guild, playerInDb.discord_id)
                    if await RoleConverter().convert(ctx, "Waiting Verification") in member.roles:
                        await member.remove_role(await RoleConverter().convert(ctx, "Waiting Verification"), "Removed from role.")
                    await member.add_role(await RoleConverter().convert(ctx, "Player"), "User has been verified")
                    await member.edit_nickname(f"{playerInDb.gamertag}", "Verified user name change.")
                    await channel.delete("User has been verified.")
                    await playerInDb.delete()
                    try:
                        await member.send(f"{member.mention} you have been verified and have been granted access to the PCN Discord.", ephermal=True)
                    except Exception as e:
                        logger.error(f"Error sending message to user: {e}") 
                else:
                    embed = Embed("Verification Queue", description=f"User: `{playerInDb.discord_name}`")
                    embed.add_field("Gamertag", playerInDb.gamertag, inline=False)
                    embed.add_field("Discord Id", playerInDb.discord_id, inline=False)
                    embed.add_field("Status", playerInDb.status, inline=False)
                    embed.add_field("Reason", playerInDb.reason, inline=True)
                    embed.add_field("Updated", Timestamp.fromdatetime(playerInDb.updated), inline=False)
                    embed.add_field("Discord Thread", f"<#{playerInDb.discord_thread}>", inline=False)
                    embeds.append(embed)
        paginator = Paginator.create_from_embeds(self.bot, *embeds)
        paginator.callback = self.approval
        paginator.show_callback_button = "✅"
        logger.info(f"Queue took {time.time() - startTime} seconds to run.")
        await paginator.send(ctx)

    async def approval(self, ctx):
        try:
            _discord_id = ctx.message.embeds[0].fields[1].value
            db_user = await VerificationQueue.find_one(VerificationQueue.discord_id == int(_discord_id))
            channel: ThreadChannel = await self.bot.fetch_channel(db_user.discord_thread)
            member = await Guild.fetch_member(ctx.guild, int(_discord_id))
    
            await member.add_role(await RoleConverter().convert(ctx, "Player"), "Player has been verified")
            if await RoleConverter().convert(ctx, "Waiting Verification") in member.roles:
                await member.remove_role(await RoleConverter().convert(ctx, "Waiting Verification"), "Removed from Waiting Verification role.")
            await member.edit_nickname(f"{ctx.message.embeds[0].fields[0].value}", "Verified user name change.")
            await channel.delete("User has been verified.")
            await db_user.delete()
            try:
                await member.send(f"{member.mention} you have been verified and have been granted access to the PCN Discord.", ephermal=True)
            except Exception as e:
                logger.error(f"Error sending message to user: {e}")
        except Exception as e:
            logger.error(e)

    @Task.create(IntervalTrigger(hours=24))
    async def check_queue(self):
        print("Task started at: ", datetime.now())
        async for playerWaiting in VerificationQueue.find(VerificationQueue.status == "New"):
            channel: ThreadChannel =  await self.bot.fetch_channel(playerWaiting.discord_thread)
            guild: Guild = await self.bot.fetch_guild(442081251441115136)
            member = await self.bot.fetch_member(playerWaiting.discord_id, guild.id)
            player_role: Guild = await guild.fetch_role(449043802829750272)
            waiting_role: Guild = await guild.fetch_role(1001999651429425233)
            ufc_role: Guild = await guild.fetch_role(1005163999215755347)

            async with aiohttp.ClientSession() as session:
                if await fetch_api(self, playerWaiting, session):
                    print("Player found in API")
                    try:
                        logger.info(f"A player has been verified:\nDiscord | id: {playerWaiting.discord_name} : {playerWaiting.discord_id}\nGamertag: {playerWaiting.gamertag}")
                        if waiting_role in member.roles and ufc_role in member.roles:
                            await member.remove_roles([waiting_role, ufc_role], "Use removed from roles.")
                        elif ufc_role not in member.roles:
                            await member.remove_role(waiting_role, "Removed from Waiting Verification role.")
                        await member.add_role(player_role, "Player has been verified")
                        await member.edit_nickname(f"{playerWaiting.gamertag}", "Verified user name change.")
                        await channel.delete("User has been verified.")
                        await playerWaiting.delete()
                        try:
                            await member.send(f"{member.mention} you have been verified and have been granted access to the PCN Discord.", ephermal=True)
                        except Exception as e:
                            logger.error(f"Error sending message to user: {e}")
                    except Exception as e:
                        logger.error(e)
                else:
                    await channel.send(f"Hey {member.mention},\nPlease bear with us as we are working through our verification queue and we will get to your application as soon as we can.\nThanks for your patience.")
                    logger.info(f"User: {playerWaiting.discord_name} is still waiting for verification.")


async def fetch_api(self, doc: Document, session) -> Boolean:
    try:
        async with session.get(self.bot.config.urls.find_player.format(f"{doc.gamertag}&_fields=title,link,date,modified,slug")) as resp:
            if resp.status == 200:
                search_response = await resp.text()
                if not (db_response := orjson.loads(search_response)):
                    return False
                for db_player in db_response:
                    if len(db_response) <= 1:
                        async with session.get(self.bot.config.urls.players.format(db_player['slug'])) as gamertag_lookup:
                            if gamertag_lookup.status == 200:
                                lookup_player = await gamertag_lookup.text()
                                player_found = orjson.loads(lookup_player)
                                return len(player_found) >= 1
                    elif re.match(doc.gamertag, db_player["title"]['rendered'], flags=re.I):
                        async with session.get(self.bot.config.urls.players.format(db_player['slug'])) as gamertag_lookup:
                            if gamertag_lookup.status == 200:
                                lookup_player = await gamertag_lookup.text()
                                player_found = orjson.loads(lookup_player)
                                return len(player_found) >= 1
    except Exception as e:
        logger.error(e)


def setup(bot):
    Queue(bot)
    bot.add_model(VerificationQueue)