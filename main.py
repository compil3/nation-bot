import asyncio
import os
import logging
from http.client import HTTPException
from pathlib import Path
from sys import platform
from typing import Optional

import jurigged
from beanie import init_beanie
# from loguru import logger
from motor import motor_asyncio
from naff import (AllowedMentions, Client, Intents, InteractionContext, errors,
                  listen, logger_name)
from naff.models.naff.context import Context

from utils.init_logging import init_logging

from config import ConfigLoader


# logger.add("./logs/main.log", format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}", level="INFO", rotation="5MB", retention="5 days", compression="zip")
dev = False
logger = logging.getLogger(logger_name)
#The start of the bot.
class Bot(Client):
    logger = logging.getLogger(logger_name)
    def __init__(self, current_dir, config):
        self.current_dir: Path = current_dir
        self.config = config

        super().__init__(
            intents=Intents.DEFAULT | Intents.GUILD_MEMBERS,
            sync_interactions=True,
            asyncio_debug=False,
            delete_unused_application_cmds=True,
            activity="with your emotions",
            fetch_members=True,
        )

        self.db: Optional[motor_asyncio.AsyncIOMotorClient] = None
        self.models = list()

    def get_extension(self):
        self.logger.info("Loading Extensions...")

        # go through all folders in the directory and load the extensions from all files
        # Note: files must end in .py
        for root, dirs, files in os.walk("extensions"):
            for file in files:
                if file.endswith(".pyc"):
                    pass
                if file.endswith(".py") and not file.startswith("__init__") and not file.startswith("!"):
                    file = file.removesuffix(".py")
                    path = os.path.join(root, file)
                    python_import_path = path.replace("/", ".").replace("\\", ".")
                    self.load_extension(python_import_path)


    async def startup(self):
        self.load_extension('sentry', token=self.config.sentry_token)
        self.get_extension()
        if dev:
            self.grow_scale("dis_snek.ext.debug_scale")

        self.db = motor_asyncio.AsyncIOMotorClient(self.config.database_address)
        await init_beanie(database=self.db.Nation, document_models=self.models)
        if self.config.debug.debug_set is True:
            await self.astart(self.config._dev_token)
        else:
            await self.astart(self.config.discord_token)

        # jurigged.watch(pattern="*.py")

             
    @listen()
    async def on_ready(self):
        msg = f"Logged in as {self.user}.\nCurrent scales: {', '.join(self.ext)}"

        if platform == "linux" or platform == "linux2" or platform == "darwin":
            # os.system("clear")
            jurigged.watch(pattern="./extensions/*.py")

            self.logger.info(f"--Pro Clubs Nation Bot {self.config.version}")
            self.logger.info("Connected to {} guild(s)".format(len(self.guilds)))
            self.logger.info(f"Logged in as {self.user}.")
            self.logger.info(f"Extensions: {', '.join(self.ext)}")


        elif platform == "win32":
            # os.system('cls')
            jurigged.watch(pattern="./extensions/*.py")

            self.logger.info(f"--Pro Clubs Nation Bot {self.config.version}")
            self.logger.info("Connected to {} guild(s)".format(len(self.guilds)))
            self.logger.info(f"Logged in as {self.user}.")
            self.logger.info(f"Extensions: {', '.join(self.ext)}")

    async def on_command_error(self, ctx: InteractionContext, error: Exception, *args, **kwargs):
        unexpected = True
        if isinstance(error, errors.CommandCheckFailure):
            unexpected = False
            await send_error(ctx, "Command check failed!\nSorry, but it looks like you don't have permission to use this commands.")
        else:
            await send_error(ctx, str(error)[:2000] or "<No exception text available>")

        if unexpected:
            self.logger.error(f"Exception during command execution: {repr(error)}", exc_info=error)

    async def on_command(self, ctx: Context):
        _command_name = ctx.invoke_target
        self.logger.info(f"{ctx.author.display_name} used Command: '{ctx.invoke_target} {ctx.args}'")

    async def on_error(self, source: str, error: Exception, *args, **kwargs) -> None:
        """Bot on_error override"""
        if isinstance(error, HTTPException):
            errors = error.search_for_message(error.errors)
            out = f"HTTPException: {error.status}|{error.response.reason}: " + "\n".join(errors)
            self.logger.error(out, exc_info=error)
        else:
            self.logger.error(f"Ignoring exception in {source}", exc_info=error)

    def add_model(self, model):
        self.models.append(model)


async def send_error(ctx, msg):
    if ctx is not None:
        await ctx.send(msg, allowed_mentions=AllowedMentions.none(), ephemeral=True)
    else:
        logger.warning(f"Already responded to message, error message: {msg}")

def main():
    current_dir = Path(__file__).parent
    config = ConfigLoader.load_settings()
    init_logging()

    bot = Bot(current_dir, config)
    asyncio.run(bot.startup())


if __name__ == "__main__":
    main()
