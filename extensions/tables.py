import asyncio
import logging
import time

import aiohttp
from aiocache import cached
from loguru import logger
from naff.ext.paginators import Paginator
from naff.models import Embed, Extension
from naff.models.discord.color import MaterialColors
from naff.models.discord.components import ActionRow, Button, ButtonStyles
from naff.models.naff.application_commands import (Permissions,
                                                   component_callback,
                                                   slash_command)
from naff.models.naff.context import ComponentContext
from naff.models.naff import (cooldown, Buckets)
from rich.table import Table
from rich.console import Console
from rich import box

logger.add("./logs/tables.log", format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}", level="INFO", rotation="50 MB", retention="5 days", compression="zip")
logo = "https://proclubsnation.com/wp-content/uploads/2021/10/PCN_logo_new.png"

# League Tabls
class Tables(Extension):

    # @check(user_has_player_role())
    @slash_command(
        "table",
        description="Display PCN League Tables",
        scopes=[689119429375819951, 442081251441115136],
        default_member_permissions=Permissions.USE_APPLICATION_COMMANDS
    )
    @cooldown(bucket=Buckets.USER, rate=1, interval=30)
    async def create_table(self, ctx: ComponentContext):
        await ctx.defer(ephemeral=True)
        try:           
            components: list[ActionRow]=[
               Button(
                   style=ButtonStyles.BLURPLE,
                   label="All Leagues",
                   custom_id="all_leagues",
               ),
               Button(
                   style=ButtonStyles.BLURPLE,
                   label="Super League",
                   custom_id="super_league",
               ),
               Button(
                   style=ButtonStyles.BLURPLE,
                   label="League One",
                   custom_id="league_one",
               ),
               Button(
                   style=ButtonStyles.BLURPLE,
                   label="League Two",
                   custom_id="league_two",
               )
           ]
        except Exception as e:
                logging.ERROR(e)
        await ctx.send("PCN Standings", components=components)

    def get_league_tables(self,session):
        competitions = ["super-league", "league-one", "league-two"]
        return [
            session.get(self.bot.config.urls.tables.format(league), ssl=False)
            for league in competitions
        ]
        

    @component_callback("all_leagues")
    async def pcn_table(self, ctx: ComponentContext):
        await ctx.defer(edit_origin=True)
        competitions = ["super-league", "league-one", "league-two"]

        e = await self.get_all_standings(competitions)
        paginator = Paginator.create_from_embeds(self.bot, *e)
        await paginator.send(ctx)

    @component_callback("super_league")
    async def super_league_table(self, ctx: ComponentContext):
        await ctx.defer(edit_origin=True)
        e = await self.get_standings("super-league")
        await ctx.edit_origin("",embeds=[e], components=[])
        
    @component_callback("league_one")
    async def league_one_table(self, ctx: ComponentContext):
        await ctx.defer(edit_origin=True)
        e = await self.get_standings("league-one")
        await ctx.send(embeds=[e], components=[])

    @component_callback("league_two")
    async def league_two_table(self, ctx: ComponentContext):
        await ctx.defer(edit_origin=True)
        e = await self.get_standings("league-two")
        await ctx.send(embeds=[e], components=[])

    @logger.catch
    @cached(ttl=300)
    async def get_standings(self, league):
        competitions = ["super-league", "league-one", "league-two"]

        league_table = []
        async with aiohttp.ClientSession() as session:
            async with session.get(self.bot.config.urls.tables.format(league), ssl=False) as resp:
                standing_data = await resp.json()
                league_name, season_number = standing_data[0]['title']['rendered'].split("&#8211;")
                e = Embed(f"**{season_number}**", color=MaterialColors.RED)
                e.set_author("PCN Tables", url=f"https://proclubsnation.com/table/{league}", icon_url=logo)
                table = Table(title=f"{league_name}", box=box.ROUNDED)
                table.add_column("Rank", style="cyan", justify="right", no_wrap=True)
                table.add_column("Team", style="magenta", justify="full", no_wrap=True)
                table.add_column("Points", style="green", justify="left", no_wrap=True)
                for tablePosition in standing_data[0]['data']:
                    if tablePosition != '0':
                        rank = str(standing_data[0]['data'][tablePosition]['pos'])
                        if " - 🏆" in str(standing_data[0]['data'][tablePosition]['name']):
                            team = str(standing_data[0]['data'][tablePosition]['name']).replace(" - 🏆", "") 
                        else:
                            team = str(standing_data[0]['data'][tablePosition]['name'])
                        pts = str(standing_data[0]['data'][tablePosition]['pts'])
                        table.add_row(rank, team, pts)
                console = Console()
                with console.capture() as cap:
                    console.print(table)
                # table_out = cap.get()
                e.description = f"```ansi\n{cap.get()}\n```"
                e.set_footer(
                    text="proclubsnation.com",
                    icon_url="https://proclubsnation.com/wp-content/uploads/2021/10/PCN_logo_new.png",
                )

        return e  

    @logger.catch
    @cached(ttl=300)
    async def get_all_standings(self, competition: list):
        start_time = time.time()
        async with aiohttp.ClientSession() as client:
            tasks = []
            embeds = []
            league_table= []
            standings = []
            for league in competition:
                url = self.bot.config.urls.tables.format(league)
                tasks.append(asyncio.ensure_future(get_data(client, url)))

            tables = await asyncio.gather(*tasks)
            for standings in tables:
                league_name, season = standings[0]['title']['rendered'].split("&#8211;")
                e = Embed(f"**{season}**", color=MaterialColors.RED)
                e.set_author("PCN Tables", url=f"https://proclubsnation.com/table/{league}", icon_url=logo)
                table =  Table(title=f"{league_name}", box=box.ROUNDED)
                table.add_column("Rank", justify="right", style="cyan", no_wrap=True)
                table.add_column("Team", justify="center", style="magenta", no_wrap=True)
                table.add_column("Points", justify="right", style="green", no_wrap=True)
                league_table = []
                for table_position in standings[0]['data']:
                    if table_position != '0':
                        rank = str(standings[0]['data'][table_position]['pos'])
                        if " - 🏆" in str(standings[0]['data'][table_position]['name']):
                            team = str(standings[0]['data'][table_position]['name']).replace(" - 🏆", "")
                        else:
                            team = str(standings[0]['data'][table_position]['name'])
                        pts = str(standings[0]['data'][table_position]['pts'])
                        table.add_row(rank, team, pts)
                        league_table.append(table)
                console = Console()
                with console.capture() as cap:
                    console.print(table)
                e.description = f"```ansi\n{cap.get()}\n```"
                e.set_footer(
                    text="proclubsnation.com",
                    icon_url="https://proclubsnation.com/wp-content/uploads/2021/10/PCN_logo_new.png",
                )

                embeds.append(e)

        return embeds                
        

async def get_data(session, url):
    async with session.get(url, ssl=True) as resp:

        resp = await resp.json()
        return resp

def setup(bot):
    Tables(bot)
