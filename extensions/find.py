from datetime import datetime
from beanie import Document
from naff import (Extension, Embed, slash_command, slash_option, InteractionContext, context_menu, Permissions, CommandTypes)
from naff.models.discord.color import MaterialColors
import aiohttp
import json
from loguru import logger
import re
import orjson

# TODO: Add guild ids to a json config file instead of hardcoring them
# TODO: Make the data retrieval async in all user facing commands


class Registered(Document):
    user_id: int
    discord_full_name: str
    registered_gamer_tag: str
    pcn_url: str
    registered_date: str

    class Collection:
        name = "discord_registered"

# used to look up a discord member's gamer tag and return if they exist on pcn.
class PlayerFinder(Extension):


    def D_Embed(self, title: str) -> Embed:
        e = Embed(
            f"PCN Player Lookup: {title}",
            color=MaterialColors.BLUE_GREY,
            timestamp=datetime.now(),
        )
        e.set_footer(
            "proclubsnation.com",
            icon_url="https://proclubsnation.com/wp-content/uploads/2020/08/PCN_logo_Best.png",
        )
        return e

    @slash_command(
        "find",
        description="Look up a gamertag",
        scopes=[689119429375819951, 442081251441115136],
        default_member_permissions=Permissions.BAN_MEMBERS | Permissions.MUTE_MEMBERS
    )
    @slash_option("gamertag", "Enter Gamertag to check", 3, required=True)
    async def find(self, ctx: InteractionContext, gamertag: str):
        """Finds a player using /find [gamertag]"""
        await ctx.defer(ephemeral=True)

        try:
            
            #save id, slug, link to mongodb for faster lookup

            # make gamertag to lowercase
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.bot.config.urls.find_player.format(f"{gamertag.lower()}&_fields=title,slug,date,modified,link")) as request:
                    if request.status == 200:
                        gt_lookup = await request.text()
                        search_responsea = orjson.loads(gt_lookup)
                        for db_player in search_responsea:
                            if re.match(gamertag, db_player['title']['rendered'], flags=re.I):
                                async with session.get(self.bot.config.urls.players.format(db_player['slug'])) as gamertag_lookup:
                                    if gamertag_lookup.status == 200:
                                        lookup = await gamertag_lookup.text()
                                        player_data = orjson.loads(lookup)

                                        if len(player_data) < 1:
                                            raise ValueError
                                        else:
                                            for player in player_data:
                                                # if player["title"]['rendered'].lower() == gamertag.lower:
                                                if re.match(gamertag, player["title"]['rendered'], flags=re.I):
                                                    e = self.D_Embed("Results")
                                                    e.description = f"**{player['title']['rendered']}** :white_check_mark:"
                                                    e.add_field("Registered", player['date'], inline=True )
                                                    e.add_field("Last Updated", player['modified'], inline=True )
                                                    e.add_field("Website Slug", player['slug'], inline=False )
                                                    e.add_field("PCN Profile", player['link'], inline=True )
                                                    await ctx.send(embeds=[e])
                                    else:
                                        e = self.D_Embed("Connection Error")
                                        e.description = "Failed to connect to API.\n\n{e}\n\nTry again later."
                                        await ctx.send(embeds=[e])
        except ValueError:
            e = self.D_Embed("Results")
            e.description = f":x:\n**{gamertag}** has been not found."
            logger.error(f"ValueError in /find: {e}")
            await ctx.send(embeds=[e])
            

    # TODO Use the register command to add users to database.  Then pull the gamer tag from the database and use it to find the player.
    @context_menu(
        "Search", 
        CommandTypes.USER, 
        scopes=[689119429375819951,], 
        default_member_permissions=Permissions.BAN_MEMBERS | Permissions.MUTE_MEMBERS, dm_permission=False
    )
    async def search(self, ctx: InteractionContext):
        """
        Finds selected player when right clicking>Apps>Lookup
        """
        await ctx.defer(ephemeral=True)

        member = self.bot.get_member(ctx.target_id, ctx.guild_id)
        try:
            find_user = await Registered.find_one(Registered.user_id == member.id)
            if find_user is None:
                raise ValueError
            async with aiohttp.ClientSession() as session:
                async with session.get(self.bot.config.urls.find_player.format(f"{find_user.registered_gamer_tag}&_fields=title,link,date,modified,slug")) as resp:
                    if resp.status == 200:
                        lookup = await resp.text()
                        player_lookup = json.loads(lookup)

                        if len(player_lookup) < 1:
                            raise ValueError
                        else:
                            e = self.D_Embed("Results")
                            e.description = f"**{player_lookup[0]['title']['rendered']}** :white_check_mark:"
                            e.add_field("Registered", player_lookup[0]['date'], inline=True )
                            e.add_field("Last Updated", player_lookup[0]['modified'], inline=True )
                            e.add_field(
                                "Registered GT", find_user.registered_gamer_tag, inline=False
                            )
                            e.add_field("Discord ID", str(member))
                            e.add_field("Website Slug", player_lookup[0]['slug'], inline=False )
                            e.add_field("PCN Profile", player_lookup[0]['link'], inline=True )
                            await ctx.send(embeds=[e])
                    else:
                        e = self.D_Embed("Connection Error")
                        e.description = "Failed to connect to API.\n\n{e}\n\nTry again later."
                        await ctx.send(embeds=[e])
        except ValueError:
            e = self.D_Embed("Results")
            e.description = f"**{member.display_name}** is not registered with Bot."
            await ctx.send(embeds=[e])


def setup(bot):
    PlayerFinder(bot)
    bot.add_model(Registered)
