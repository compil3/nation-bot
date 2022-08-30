import asyncio
import datetime
import platform
import subprocess
import git
import psutil
import httpx

from io import BytesIO
from pathlib import Path
from aiofile import AIOFile, LineReader
from helpers.updates import update
from loguru import logger
from naff import BrandColors, Guild, GuildCategory, GuildText, GuildVoice
from naff.client.const import __py_version__, __version__
from naff.ext.debug_extension import utils as _d_utils
from naff.models import Embed, Extension, MaterialColors, Timestamp
from naff.models.discord.enums import Intents
from naff.models.discord.file import File
from naff.models.naff.application_commands import (Permissions, slash_command)
from naff.models.naff.command import cooldown
from naff.models.naff.context import InteractionContext
from naff.models.naff.cooldowns import Buckets
from rich.console import Console
from pydactyl import PterodactylClient


def strf_delta(time_delta: datetime.timedelta, show_seconds=True) -> str:
    """Formats timedelta into a human readable format"""

    years, days = divmod(time_delta.days, 365)
    hours, rem = divmod(time_delta.seconds, 3600)
    minutes, seconds = divmod(rem, 60)

    years_fmt = f"{years}, year{'s' if years >1 or years == 0 else ''}"
    days_fmt = f"{days} day{'s' if days > 1 or days == 0 else ''}"
    hours_fmt = f"{hours} hour{'s' if hours > 1 or hours == 0 else ''}"
    minutes_fmt = f"{minutes} minute{'s' if minutes > 1 or minutes == 0 else ''}"
    seconds_fmt = f"{seconds} second{'s' if seconds > 1 or seconds == 0 else ''}"

    if years >= 1:
        return f"{years_fmt} and {days_fmt}"
    if days >= 1:
        return f"{days_fmt} and {hours_fmt}"
    if hours >= 1:
        return f"{hours_fmt} and {minutes_fmt}"
    if show_seconds:
        return f"{minutes_fmt} and {seconds_fmt}"
    return f"{minutes_fmt}"


def get_size(bytes, suffix="B"):
    """
    Scale bytes to its proper format
    e.g:
        1253656 => '1.20MB'
        1253656678 => '1.17GB'
    """
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor


class BotInfo (Extension):
    def UpdateEmbed(self, title: str) -> Embed:
        e = Embed(
            title="Update Status",
            description=f"{title}",
            color=MaterialColors.BLUE_GREY,
            timestamp=datetime.datetime.now(),
        )
        e.set_footer(
            "proclubsnation.com",
            icon_url="https://proclubsnation.com/wp-content/uploads/2020/08/PCN_logo_Best.png",
        )
        return e

    def D_Embed(self, title: str) -> Embed:
        e = Embed(
            f"PCN Bot Debug: {title}",
            color=MaterialColors.BLUE_GREY,
        )
        e.set_footer(
            "PCN Debug Scale",
            icon_url="https://proclubsnation.com/wp-content/uploads/2020/08/PCN_logo_Best.png",
        )
        return e

    async def get_async(url):
        async with httpx.AsyncClient(timeout=None) as client:
            return await client.get(url)

    def get_repo_hash(self) -> str:
        repo = git.Repo(".")
        return repo.head.object.hexsha

    @slash_command(
        "bot",
        sub_cmd_description="Basic information regarding the bot.",
        sub_cmd_name="info",
        scopes=[689119429375819951, 442081251441115136],
        default_member_permissions=Permissions.MANAGE_ROLES | Permissions.KICK_MEMBERS | Permissions.BAN_MEMBERS,
    )
    async def debug_info(self, ctx):
        await ctx.defer(ephemeral=True)
        urls = []
        for sites, value in self.bot.config.urls.items():
            match sites:
                case "find_player":
                    value.format("Spillshot")
                case "teams":
                    value = value.replace("/v2/teams", "/v2/teams?slug=ac-milan")
                case "schedules":
                    value = value
            urls.append(value)
        try:
            # Todo: Fix error Exception during command execution: AttributeError("'NoneType' object has no attribute 'total'")
            resps = await asyncio.gather(*map(BotInfo.get_async, urls))
            for data in resps:
                if "teams" in str(data.request.url):
                    team_delay = round(data.elapsed.total_seconds(), 2)
                elif "players" in str(data.request.url):
                    player_delay = round(data.elapsed.total_seconds(), 2)
                elif "tables" in str(data.request.url):
                    table_delay = round(data.elapsed.total_seconds(), 2)
                elif "calendars" in str(data.request.url):  # local variable 'schedule_delay' referenced before assignment
                    schedule_delay = round(data.elapsed.total_seconds(), 2)
        except httpx.ConnectError:
            return await ctx.send("Could not connect to the API. Please try again later.")

        startTime = self.bot.start_time
        print(startTime)
        uptime = datetime.datetime.now() - self.bot.start_time
        e = self.D_Embed("Information")
        e.add_field("Bot Version", f"{self.bot.config.version}", inline=False)
        e.add_field("Language Info", f"NAFF@{__version__}  |  Py@{__py_version__}", inline=True)
        e.add_field("Current Git Hash", self.get_repo_hash()[:7], inline=True)
        e.add_field("Start Time", f"{Timestamp.fromdatetime(self.bot.start_time)}\n({strf_delta(uptime)}) ago")
        e.add_field("Operating System", platform.system(), inline=True)
        e.add_field(name="CPU | Usage", value=f"**{psutil.cpu_count(logical=False)} | {psutil.cpu_percent()}%**", inline=True)
        e.add_field(name="RAM Usage", value=f"**{psutil.virtual_memory().percent}**%", inline=True)
        
        e.add_field("Loaded Extensions", ", ".join(self.bot.ext))
        guild_names = []
        for guild in self.bot.guilds:
            guild_names.append(guild.name)
        e.add_field(f"Connected to **{len(self.bot.guilds)}** Guilds", guild_names)
        privileged_intents = [i.name for i in self.bot.intents if i in Intents.PRIVILEGED]
        if privileged_intents:
            e.add_field("Intents", " | ".join(privileged_intents), inline=True)

        e.add_field(name="\u200b", value="**API Status**", inline=False)
        e.add_field(name="Bot", value=f"```{round(self.bot.latency * 100, 2)}s ```", inline=True)
        e.add_field(name="Player API", value=f"```{player_delay}```", inline=True)
        e.add_field(name="\u200b", value="\u200b", inline=True)

        e.add_field(name="Table API", value=f"```{table_delay}```", inline=True)
        e.add_field(name="Teams API", value=f"```{team_delay}```", inline=True)
        e.add_field("Calendar API", f"```{schedule_delay}```", inline=True)
        await ctx.send(embeds=[e])

    @debug_info.subcommand(
        "cache",
        sub_cmd_description="Get information about the cache.",
    )
    async def debug_cache(self, ctx: InteractionContext) -> None:
        await ctx.defer(ephemeral=True)

        e = self.D_Embed("Cache")
        e.description = f"```prolog\n{_d_utils.get_cache_state(self.bot)}\n```"

        await ctx.send(embeds=[e])

    @debug_info.subcommand("lines", sub_cmd_description="Get PCN Bot lines of code")
    async def _lines(self, ctx: InteractionContext) -> None:
        await ctx.defer(ephemeral=True)
        output = subprocess.check_output(["tokei", "-C", "--sort", "code"]).decode("utf-8")
        await ctx.send(f"```haskell\n{output}\n```")

    # TODO: fix error [Errno 2] No such file or directory: '/home/logs/bot.log'
    @debug_info.subcommand("log", sub_cmd_description="Get's the bots last few log messages.")
    async def _tail(self, ctx: InteractionContext, count: int = 10) -> None:
        await ctx.defer(ephemeral=True)
        lines = []
        current_dir = Path(__file__).parent.parent.parent
        log_loc = current_dir / "container" / "logs" / "main.log"
        async with AIOFile(log_loc, "r") as af:
            async for line in LineReader(af):
                lines.append(line)
                if len(lines) == count + 1:
                    lines.pop(0)
        log = "".join(lines)
        if len(log) > 1500:
            with BytesIO() as file_bytes:
                file_bytes.write(log.encode("utf-8"))
                file_bytes.seek(0)
                log = File(file_bytes, file_name=f"tail_{count}.log")
                await ctx.send(content="Here's the latest log.", file=log)
        else:
            await ctx.send(content=f"```\n{log}\n```")

    @debug_info.subcommand(
        "guilds", 
        sub_cmd_description="Lists the names of the guilds the bot is in.",
    )
    async def _guild_names(self, ctx:InteractionContext) -> None:
        await ctx.defer(ephemeral=True)
        guild_list = []

        for guild in self.bot.guilds:
            guild_list.append(f"[ {guild.name} ]")
        embed = Embed(
            title="Guilds",
            description="\n".join(guild_list),
            color=BrandColors.BLURPLE
        )
        await ctx.send(embeds=embed, ephemeral=True)

    @slash_command(
        name="update",
        description="Updates the bot to the latest version.",
        default_member_permissions=Permissions.ADMINISTRATOR,
        scopes=[689119429375819951, 442081251441115136]
    )
    async def update_bot(self, ctx: InteractionContext) -> None:
        await ctx.defer(ephemeral=True)
        status = await update(self.bot)
        if status:
            console = Console()
            with console.capture() as capture:
                console.print(status.table)
            logger.debug(capture.get())
            logger.debug(len(capture.get()))
            added = "\n".join(status.added)
            removed = "\n".join(status.removed)
            changed = "\n".join(status.changed)
            embed = self.UpdateEmbed("Updates have been applied.")
            embed.add_field("Old Commit", value=status.old_hash)
            embed.add_field("New Commit", value=status.new_hash)

            if added:
                embed.add_field(name="New Modules", value=f"```\n{added}\n```")
            if removed:
                embed.add_field(name="Removed Modules", value=f"```\n{removed}\n```")
            if changed:
                embed.add_field(name="Changed Modules", value=f"```\n{changed}\n```")
            embed.set_footer(text="Bot Updater", icon_url="https://proclubsnation.com/wp-content/uploads/2020/08/PCN_logo_Best.png")
            logger.debug("Updates Applied.")
            content = f"```ansi\n{capture.get()}\n```"
            if len(content) < 3000:
                await ctx.send(content, embeds=embed, ephemeral=True)
            else:
                await ctx.send(f"Total Changes: {status.lines['total_lines']}", embeds=embed, ephemeral=True)
        else:
            embed = self.UpdateEmbed("No updates have been applied.")
            await ctx.send(embeds=embed, ephemeral=True)

    @debug_info.subcommand(
        sub_cmd_name="server_info",
        sub_cmd_description="Gets information about the server.",
    )
    async def _server_info(self, ctx: InteractionContext) -> None:
        await ctx.defer(ephemeral=True)
        guild: Guild = ctx.guild
        owner = await guild.fetch_owner()
        owner = f"{owner.username}#{owner.discriminator}" if owner else "||`[redacted]`||"
        categories = len([x for x in guild.channels if isinstance(x, GuildCategory)])
        text_channels = len([x for x in guild.channels if isinstance(x, GuildText)])
        voice_channels = len([x for x in guild.channels if isinstance(x, GuildVoice)])
        threads = len(guild.threads)
        members = guild.member_count
        roles = len(guild.roles)
        role_list = sorted(guild.roles, key=lambda x: x.position, reverse=True)
        role_list = ", ".join(role.mention for role in role_list)

        embed = Embed(
            title="",
            description=""
        )
        embed.add_field("Owner", value=owner, inline=True)
        embed.add_field("Channel Categories", value=str(categories), inline=True)
        embed.add_field("Text Channels", value=str(text_channels), inline=True)
        embed.add_field("Voice Channels", value=str(voice_channels), inline=True)
        embed.add_field("Threads", value=str(threads), inline=True)
        embed.add_field("Members", value=str(members), inline=True)
        embed.add_field("Roles", value=str(roles), inline=True)
        embed.add_field("Created At", value=f"<t:{int(guild.created_at.timestamp())}:F>"),
        if len(role_list) < 1024:
            embed.add_field("Role List", value=role_list, inline=False)
        embed.set_author(name=guild.name, icon_url=guild.icon.url)
        embed.set_thumbnail(url=guild.icon.url)
        embed.set_footer(text=f"ID: {guild.id} | Server Created")
        
        await ctx.send(embeds=embed, ephemeral=True)

    @debug_info.subcommand(sub_cmd_name="restart", sub_cmd_description="Restarts the bot.")
    async def restart(self, ctx: InteractionContext):
        await ctx.defer(ephemeral=True)

        api = PterodactylClient('https://control.sparkedhost.us/', self.bot.config.sparkedhost.token)
        servers = api.client.servers.list_servers()
        srv_id = servers[0]['attributes']['identifier']
        
        await ctx.send("Restarting bot...please wait for it to return to the discord server.")
        api.client.servers.send_power_action(srv_id, 'restart')
    
    @debug_info.subcommand(sub_cmd_name="server", sub_cmd_description="Gets information about the bot server.")
    async def bot_server(self, ctx: InteractionContext):
        await ctx.defer(ephemeral=True)

        api = PterodactylClient('https://control.sparkedhost.us/', self.bot.config.sparkedhost.token)
        bot_servers = api.client.servers.list_servers()
        srv_id = bot_servers[0]['attributes']['identifier']

        srv_utilization = api.client.servers.get_server_utilization(srv_id)
        embed = Embed(
            title="Host Information",
            description=f"{srv_id}",
            color=BrandColors.YELLOW
        )

        embed.add_field("CPU Usage", value=f"{(srv_utilization['resources']['cpu_absolute'])}%")
        embed.add_field("Mem Usage", value=f"{round(srv_utilization['resources']['memory_bytes'] / 1024 / 1024,2)}MB")
        await ctx.send(embeds=embed, ephemeral=True)
def setup(bot):
    BotInfo(bot)

# https://git.zevaryx.com/stark-industries/jarvis/jarvis-bot/-/blob/dev/jarvis/cogs/botutil.py
