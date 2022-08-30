from ast import Delete
import asyncio
import aiohttp
import json
from datetime import datetime
from pkgutil import get_data
from typing import TYPE_CHECKING


import requests
from beanie import Document
from loguru import logger
from naff import (ActionRow, Button, ButtonStyles, ComponentContext, Embed,
                  Extension, Guild, InteractionContext, Member, Modal,
                  ModalContext, ParagraphText, Permissions, ShortText,
                  component_callback, slash_command, Timestamp)
from naff.ext.paginators import Paginator
from naff.models.naff.converters import RoleConverter, SnowflakeConverter

if TYPE_CHECKING:
    from main import Bot


format = "%b %d %Y %I:%M%p"


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

# PCN Roles
# Admin - 552702041395298324
# Roster Admin - 543563725630865417
# player admin - 442082962826199041
# Moderator - 608012366197686286
# Owner - 442082486022045697
# Discord Management - 545392640884211712


class Queue(Extension):
    bot: "Bot"

    # TODO: Add task to check gamer tags in verification_queue every 5 hours, if the gamer tag is found, add 'Player' role to user, remove from queue, send a "register" msg to user.
    # TODO: Change look up method to one found in stat_builder.py
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
        db_search = await VerificationQueue.find(VerificationQueue.status == "New").to_list()

        async for playerInDb in VerificationQueue.find(VerificationQueue.status == "New"):
            async with aiohttp.ClientSession() as session:
                async with session.get(self.bot.config.urls.find_player.format(f"{playerInDb.gamertag}&_fields=title,link,date,modified,slug")) as resp:
                    try:
                        if resp.status == 200:
                            lookup = await resp.json()
                            if not lookup:
                                raise IndexError                           
                            else:
                                # lookupData = json.loads(lookup)
                                try:
                                    member = await Guild.fetch_member(ctx.guild, playerInDb.discord_id)
                                    await member.add_role(await RoleConverter().convert(ctx, "Player"))
                                    await member.edit_nickname(f"{playerInDb.gamertag}", "Verified user name change.")
                                    if await RoleConverter().convert(ctx, "Waiting Verification") in member.roles:
                                        await member.remove_role(await RoleConverter().convert(ctx, "Waiting Verification"), "Removed from Waiting Verification role.")
                                    await playerInDb.delete()
                                except Exception as e:
                                    logger.error(e)
                    except IndexError:
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
        paginator.callback_button_emoji = "✅"
        paginator.show_callback_button = True
        await paginator.send(ctx)

    async def approval(self, ctx):
        try:
            _discord_id = ctx.message.embeds[0].fields[1].value
            db_user = await VerificationQueue.find_one(VerificationQueue.discord_id == int(_discord_id))
            member = await Guild.fetch_member(ctx.guild, int(_discord_id))
    
            await member.add_role(await RoleConverter().convert(ctx, "Player"), "Player has been verified")
            if await RoleConverter().convert(ctx, "Waiting Verification") in member.roles:
                await member.remove_role(await RoleConverter().convert(ctx, "Waiting Verification"), "Removed from Waiting Verification role.")
            await member.edit_nickname(f"{ctx.message.embeds[0].fields[0].value}", "Verified user name change.")
            await db_user.delete()
        except Exception as e:
            logger.error(e)

async def get_data(session, url):
    async with session.get(url, ssl=True) as resp:
        resp = await resp.json()
        return resp

def setup(bot):
    Queue(bot)
    bot.add_model(VerificationQueue)
