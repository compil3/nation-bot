import logging
from datetime import datetime
from beanie import Document
from naff import (listen, Extension, logger_name, ThreadChannel)
from naff.api.events import MemberRemove, MemberUpdate
from naff.models.naff.converters import RoleConverter


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
class AutoRoles(Extension):

    # Once member accepts screening they are assigned the role
    @listen()
    async def on_member_screening(self, event: MemberUpdate):
        if event.before.pending and event.after.pending is False:
            await event.after.add_role(await RoleConverter().convert(event, "New Member"), "Accepted Rules Screening.")
    
    # TODO:  if someone leaves check verification queue and remove if found.
    @listen()
    async def on_member_leave(self, event: MemberRemove):
        # player_in_queue = VerificationQueue.find_one(VerificationQueue.discord_id == event.member.id)
        # channel: ThreadChannel =  await self.bot.fetch_channel(player_in_queue.discord_thread)
        async for playerInDb in VerificationQueue.find(VerificationQueue.discord_id == event.member.id):
            thread_channel: ThreadChannel = await self.bot.fetch_channel(playerInDb.discord_thread)
            if playerInDb is not None:
                logger.info(f"{event.member.display_name} has left the server, removing from verification queue.")
                await playerInDb.delete()
                await thread_channel.delete()




def setup(bot):
    AutoRoles(bot)
    bot.add_model(VerificationQueue)