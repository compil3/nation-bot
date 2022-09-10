# from loguru import logger
import logging
from functools import cache

from beanie import Document
from naff import (CommandTypes, Embed, Extension, InteractionContext, Member,
                  OptionTypes, Permissions, check, context_menu, logger_name,
                  slash_command, slash_option)
from naff.ext.paginators import Paginator
from naff.models.naff import Buckets, cooldown
from utils.player_builder import PlayerBuilder
from utils.stat_builder import PlayerStatsBuilder


class UserRegistration(Document):
    user_id: int
    discord_full_name: str
    registered_gamer_tag: str
    pcn_url: str
    registered_date: str

    class Collection:
        name = "discord_registered"

# 442081251441115136
# Player stats
class PlayerStats(Extension):
    logger = logging.getLogger(logger_name)
    @slash_command(
        "stats",
        description="PCN gamertag stats lookup. (Only Super League, League One/Two, Royal/PCN/Super Cups are available)",
        scopes=[689119429375819951, 442081251441115136],
        default_member_permissions=Permissions.USE_APPLICATION_COMMANDS,
    )
    @slash_option(
        "gamertag", "(Optional) Enter a Gamertag", OptionTypes.STRING, required=False
    )
    @cooldown(bucket=Buckets.USER, rate=1, interval=15)
    async def player_stats(self, ctx: InteractionContext, gamertag: str = None):
        """
        Look up PCN Stats for yourself or someone else.
        """
        await ctx.defer(ephemeral=True)
        if gamertag is None:
            gamertag = ctx.author.display_name
            try:
                display = await PlayerBuilder.builder(self, gamertag)
                if display is not None:
                    try:
                        paginator = Paginator.create_from_embeds(self.bot, display)
                        self.logger.error(ctx, f"{gamertag} found")
                        paginator.show_callback_button = False
                        await paginator.send(ctx)
                    except Exception as e: 
                        self.logger.error(e)
                        await ctx.send(embeds=display) 
                else:
                    self.logger.error(f"No player found for {gamertag}")
                    await ctx.send("Unable to retreive your stats.  If you discord name does not match your gamertag, you will need to use /stats [gamertag] or no stats could be found.")
                    return
            except Exception as e:
                self.logger.error(e)
        else:
            try:
                display = await PlayerStatsBuilder.builder(self, gamertag.lower())
                if display is not None:
                    try:
                        paginator = Paginator.create_from_embeds(self.bot, *display)
                        paginator.show_callback_button = False
                        await paginator.send(ctx)
                    except Exception:
                        await ctx.send(ctx)
                else:
                    self.logger.info(f"No player found for {gamertag} or no stats found.")
                    await ctx.send(
                        f"Unable to retreive stats for `{gamertag}`. Stats may not exist, please verify the gamer tag is correct or verifiy the user exists on the website."
                    )
                    return
            except Exception as e:
                self.logger.error(e)

    # TODO Complete the player stats context menu
    @context_menu(
        "Stats",
        CommandTypes.USER,
        scopes=[689119429375819951],
        default_member_permissions=Permissions.USE_APPLICATION_COMMANDS,

    )
    @cooldown(bucket=Buckets.USER, rate=1, interval=60)
    async def stats_context(self, ctx: InteractionContext):
        """
        Look up PCN Stats for selected user
        """
        await ctx.defer(ephemeral=True)

        post = []
        try:
            member: Member = ctx.target
            registered_user = await UserRegistration.find_one(UserRegistration.user_id == member.id)
            if registered_user is not None:
                post = await PlayerBuilder.builder(self,registered_user.registered_gamer_tag)
                if post is not None:
                    paging = Paginator.create_from_embeds(self.bot, *post)
                    paging.show_select_menu = False
                    await paging.send(ctx)
                else:
                    await ctx.send(
                        f"Unable to retreive stats for {member.display_name} stats.  If you know the players gamertag, you will need "
                        "to use /stats [gamertag]."
                    )
                    return
            else:
                await ctx.send(f"`Command unavailable.\n\n{member.display_name}` has not registered with the bot yet.\nIf you know their gamertag, try using `/stats <gamertag>`, and get them to register using `/register <gamertag>`.")
                return
        except Exception as e:
            logging.ERROR(e)

def setup(bot):
    PlayerStats(bot)
    bot.add_model(UserRegistration)
