from loguru import logger
from naff import (listen, Extension, slash_command, InteractionContext)
from naff.api.events import MemberAdd, MemberUpdate
from naff.models.naff.converters import RoleConverter

class AutoRoles(Extension):
    @listen()
    async def on_member_screening(self, event: MemberUpdate):
        if event.before.pending:
            if event.after.pending is False:
                await event.after.add_role(await RoleConverter().convert(event, "New Member"), "Accepted Rules Screening.")
        else:
            pass


def setup(bot):
    AutoRoles(bot)