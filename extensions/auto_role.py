from loguru import logger
from naff import (listen, Extension, slash_command, InteractionContext)
from naff.api.events import MemberAdd, MemberUpdate
from naff.models.naff.converters import RoleConverter

class AutoRoles(Extension):

    # Once member accepts screening they are assigned the role
    @listen()
    async def on_member_screening(self, event: MemberUpdate):
        if event.before.pending:
            if event.after.pending is False:
                await event.after.add_role(await RoleConverter().convert(event, "New Member"), "Accepted Rules Screening.")
        else:
            pass


def setup(bot):
    AutoRoles(bot)