"""JARVIS update handler."""
import asyncio
import logging
from dataclasses import dataclass
from importlib import import_module
from inspect import getmembers, isclass
from pkgutil import iter_modules
from types import FunctionType, ModuleType
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

import git
from naff.client.errors import ExtensionNotFound
from naff.client.utils.misc_utils import find, find_all
from naff.models.naff.application_commands import SlashCommand
from naff.models.naff.extension import Extension
from rich.table import Table

import extensions

if TYPE_CHECKING:
    from naff.client.client import Client

_logger = logging.getLogger(__name__)


@dataclass
class UpdateResult:
    """JARVIS update result."""

    old_hash: str
    new_hash: str
    table: Table
    added: List[str]
    removed: List[str]
    changed: List[str]
    lines: Dict[str, int]


def get_all_commands(module: ModuleType = extensions) -> Dict[str, Callable]:
    """Get all SlashCommands from a specified module."""
    commands = {}

    def validate_ires(entry: Any) -> bool:
        return isclass(entry) and issubclass(entry, Extension) and entry is not Extension

    def validate_cog(cog: FunctionType) -> bool:
        return isinstance(cog, SlashCommand)

    for item in iter_modules(module.__path__):
        new_module = import_module(f"{module.__name__}.{item.name}")
        if item.ispkg:
            if cmds := get_all_commands(new_module):
                commands.update(cmds)
        else:
            inspect_result = getmembers(new_module)
            cogs = []
            for _, val in inspect_result:
                if validate_ires(val):
                    cogs.append(val)
            for cog in cogs:
                values = cog.__dict__.values()
                commands[cog.__module__] = find_all(lambda x: isinstance(x, SlashCommand), values)
    return {k: v for k, v in commands.items() if v}


def get_git_changes(repo: git.Repo) -> dict:
    """Get all Git changes"""
    logger = _logger
    logger.debug("Getting all git changes")
    current_hash = repo.head.ref.object.hexsha
    tracking = repo.head.ref.tracking_branch()

    file_changes = {}
    for commit in tracking.commit.iter_items(repo, f"{repo.head.ref.path}..{tracking.path}"):
        if commit.hexsha == current_hash:
            break
        files = commit.stats.files
        file_changes |= {
            key: {"insertions": 0, "deletions": 0, "lines": 0}
            for key in files.keys()
        }

        for file, stats in files.items():
            if file not in file_changes:
                file_changes[file] = {"insertions": 0, "deletions": 0, "lines": 0}
            for key, val in stats.items():
                file_changes[file][key] += val
    logger.debug("Found %i changed files", len(file_changes))

    table = Table(title="File Changes")

    table.add_column("File", justify="left", style="white", no_wrap=True)
    table.add_column("Insertions", justify="center", style="green")
    table.add_column("Deletions", justify="center", style="red")
    table.add_column("Lines", justify="center", style="magenta")

    i_total = 0
    d_total = 0
    l_total = 0
    for file, stats in file_changes.items():
        i_total += stats["insertions"]
        d_total += stats["deletions"]
        l_total += stats["lines"]
        table.add_row(
            file,
            str(stats["insertions"]),
            str(stats["deletions"]),
            str(stats["lines"]),
        )
    logger.debug("%i insertions, %i deletions, %i total", i_total, d_total, l_total)

    table.add_row("Total", str(i_total), str(d_total), str(l_total))
    return {
        "table": table,
        "lines": {"inserted_lines": i_total, "deleted_lines": d_total, "total_lines": l_total},
    }


async def update(bot: "Client") -> Optional[UpdateResult]:
    """
    Update JARVIS and return an UpdateResult.

    Args:
        bot: Bot instance

    Returns:
        UpdateResult object
    """
    logger = _logger
    repo = git.Repo(".")
    current_hash = repo.head.object.hexsha
    origin = repo.remotes.origin
    origin.fetch()
    remote_hash = origin.refs[repo.active_branch.name].object.hexsha

    if current_hash != remote_hash:
        logger.info("Updating from %s to %s", current_hash, remote_hash)
        current_commands = get_all_commands()
        changes = get_git_changes(repo)

        origin.pull()
        await asyncio.sleep(3)

        new_commands = get_all_commands()

        logger.info("Checking if any modules need reloaded...")

        reloaded = []
        loaded = []
        unloaded = []

        logger.debug("Checking for removed cogs")
        for module in current_commands.keys():
            if module not in new_commands:
                logger.debug("Module %s removed after update", module)
                bot.unload_extension(module)
                unloaded.append(module)

        logger.debug("Checking for new/modified commands")
        for module, commands in new_commands.items():
            logger.debug("Processing %s", module)
            if module not in current_commands:
                bot.load_extension(module)
                loaded.append(module)
            elif len(current_commands[module]) != len(commands):
                try:
                    bot.reload_extension(module)
                except ExtensionNotFound:
                    bot.load_extension(module)
                reloaded.append(module)
            else:
                for command in commands:
                    old_command = find(
                        lambda x: x.resolved_name == command.resolved_name, current_commands[module]
                    )

                    # Extract useful info
                    old_args = old_command.options
                    if old_args:
                        old_arg_names = [x.name for x in old_args]
                    new_args = command.options
                    if new_args:
                        new_arg_names = [x.name for x in new_args]

                    # No changes
                    if not old_args and not new_args:
                        continue

                    # Check if number arguments have changed
                    if len(old_args) != len(new_args):
                        try:
                            bot.reload_extension(module)
                        except ExtensionNotFound:
                            bot.load_extension(module)
                        reloaded.append(module)
                    elif any(x not in old_arg_names for x in new_arg_names) or any(
                        x not in new_arg_names for x in old_arg_names
                    ):
                        try:
                            bot.reload_extension(module)
                        except ExtensionNotFound:
                            bot.load_extension(module)
                        reloaded.append(module)
                    elif any(new_args[idx].type != x.type for idx, x in enumerate(old_args)):
                        try:
                            bot.reload_extension(module)
                        except ExtensionNotFound:
                            bot.load_extension(module)
                        reloaded.append(module)

        return UpdateResult(
            old_hash=current_hash,
            new_hash=remote_hash,
            added=loaded,
            removed=unloaded,
            changed=reloaded,
            **changes,
        )
    return None
