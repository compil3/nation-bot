import functools
import json
import logging
import re

import aiohttp
from naff import Embed, logger_name

from aiocache import Cache, cached
import logging

class PlayerBuilder:
    logger = logging.getLogger(logger_name)
    @cached(ttl=300)
    async def builder(self, gamertag):
        league_ids = ["21", "26", "27"]
        embeds = []
        try:
            if " " in gamertag:
                gamertag = gamertag.replace(" ", "-")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.bot.config.urls.players.format(gamertag)) as response:                   
                    if response.status == 200:
                        player_text = await response.text()
                        player_data = json.loads(player_text)

                        if len(player_data) < 1:
                            embeds = None
                            return embeds
                        else:
                            player_record = player_data[0]['statistics']
                            for key in league_ids:
                                index = key
                                for field in player_record[index]:
                                    if field != "0":
                                        league_name = None
                                        if index == "21":
                                            league_name = "Super League"
                                        elif index == "27":
                                            league_name = "League One"
                                        elif index == "26":
                                            league_name = "League Two"
                                        if (field == "-1" and "appearances" not in player_record[index][field]):
                                            continue

                                        if "&#8211;" in player_data[0]['title']['rendered']:
                                            player_name = player_data[0]['title']['rendered']
                                            playername, status = player_name.split("&#8211;")
                                        else:
                                            playername = player_data[0]['title']['rendered']

                                        win_record = str(
                                            int(
                                                int(player_record[index][field]['appearances']) 
                                                * float(player_record[index][field]['winratio']) 
                                                / 100
                                            )
                                        )

                                        draw_record = str(int(int(player_record[index][field]['appearances']) * float(player_record[index][field]['drawratio']) / 100))
                                        loss_record = str(int(int(player_record[index][field]['appearances']) * float(player_record[index][field]['lossratio']) / 100))
                                        windrawlost = win_record + "-" + draw_record + "-" + loss_record
                                        #TODO: change to display win% only
                                        ratio = (
                                            str(player_record[index][field]['winratio']) 
                                            + "% - " + str(player_record[index][field]['drawratio'])
                                            + "% - " + str(player_record[index][field]['lossratio'])
                                            + "%"
                                        )

                                        # Check if the data exists or not
                                        if (int(player_record[index][field]['appearances']) < 1 and int(player_record[index][field]['shotsfaced']) <= 0):
                                            continue
                                        
                                        # goalie stats & calculations
                                        #TODO: fix goalie stats
                                        #TODO: change to check for player_record[index][field]['saves'] or player_record[index][field]['shotsontargetgk']
                                        elif (int(player_record[index][field]['goalsconceded']) > 0 and float(player_record[index][field]['saves']) > 0.0):
                                            saveperc = float(int(player_record[index][field]['saves']) / int(player_record[index][field]['shotsontargetgk'])) * 100
                                            # saveperc = float(player_record[index][field]['saveperc']) * 100
                                            ga = float(player_record[index][field]['goalsconceded'])
                                            mins = (float(player_record[index][field]['appearances'] * 90))
                                            gaa = float(ga / mins) * 90

                                            if player_record[index][field]['name'] == 'Total':
                                                embed = Embed (
                                                    title = f"**{league_name} - Career Totals**",
                                                    color = 0x1815C6
                                                )
                                                embed.set_author(
                                                    name=f"{playername}",
                                                    url=f"{player_data[0]['link']}stats"
                                                )
                                                if "&#8211;" in player_data[0]['title']['rendered']:
                                                    embed.set_footer(text=f"Status: {status}")
                                                pass
                                            else:
                                                team_name_clean = re.compile("<.*?>")
                                                team = re.sub(team_name_clean, "", player_record[index][field]['team'])
                                                team_link = re.search(r'href=[\"]?([^\'" >]+)', player_record[index][field]['team'])
                                                team_link_cleaned = team_link.group(0).replace('href="', "")
                                                embed= Embed (
                                                    title=f"**{team}** - {player_record[index][field]['name']}",
                                                    url = team_link_cleaned,
                                                    color=0x1815C6
                                                )
                                                embed.set_author(
                                                    name = f"{playername} - {league_name}",
                                                    url = f"{player_data[0]['link']}stats"
                                                )
                                                if "&#8211;" in player_data[0]['title']['rendered']:
                                                    embed.set_footer(text=f"Status: {status}")
                                            embed.add_field(
                                                name="Appearances", 
                                                value=player_record[index][field]['appearances'],
                                                inline=True
                                            )
                                            embed.add_field(name="W-D-L",value=windrawlost, inline=True)
                                            embed.add_field(name="Win - Draw - Loass %", value=ratio, inline=True)
                                            embed.add_field(name="\u200b", value="```Stats```", inline=False)
                                            embed.add_field(name="Save %", value=saveperc, inline=True)
                                            embed.add_field(name="Shots Faced", value=player_record[index][field]['shotsfaced'], inline=True)
                                            embed.add_field(name="Saves", value=player_record[index][field]['saves'], inline=True)
                                            embed.add_field(name="GA", value=player_record[index][field]['goalsconceded'], inline=True)
                                            embed.add_field(name="GAA", value=round(gaa,2), inline=True)
                                            embed.add_field(name="CS", value=player_record[index][field]['cleansheets'], inline=True)
                                            embed.add_field(name="\u200b", value="```Other```", inline=False)
                                            embed.add_field(name="Passes Completed", value=player_record[index][field]['passescompleted'], inline=True)
                                            embed.add_field(name="Pass Attempts", value=player_record[index][field]['passingattempts'], inline=True)
                                            embed.add_field(name="Pass %", value=f"{player_record[index][field]['passpercent']}%", inline=True)
                                            embeds.append(embed)
                                        # check if player isn't a goalie
                                        elif int(player_record[index][field]['appearances']) > 0 and float(player_record[index][field]['saveperc']) == 0.00:
                                            avgPassPerGame = str(round(float(player_record[index][field]['passescompleted']) / float(player_record[index][field]['appearances']),2))
                                            tacklesPerGame = str(round(float(player_record[index][field]['tackles']) / float(player_record[index][field]['appearances']),2))
                                            interceptionsPerGame = str(round(float(player_record[index][field]['interceptions']) / float(player_record[index][field]['appearances']),2))
                                            tckIntPerGame = str(tacklesPerGame + " - " + str(interceptionsPerGame))
                                            possW = str(round(float(player_record[index][field]['possessionswon'])))
                                            possL = str(round(float(player_record[index][field]['possessionslost'])))
                                            possessions = possW + " - " + possL

                                            if int(player_record[index][field]['goals']) > 0:
                                                shotsPerGoal = str(round(float(player_record[index][field]['shots']) / float(player_record[index][field]['goals']), 2)) + " - " + str(player_record[index][field]['shpercent']) + "%" 
                                            else:
                                                shotsPerGoal = ("0.0" + " - " + str(player_record[index][field]['shpercent']) + "%")
                                            
                                            if player_record[index][field]['name'] == "Total":
                                                embed = Embed(
                                                    title=f"**{league_name} - Career Totals**",
                                                    color=0x1815C6
                                                )
                                                embed.set_author(
                                                    name=f"{playername} - {league_name}",
                                                    url = f"{player_data[0]['link']}stats"
                                                )
                                                if "&#8211;" in player_data[0]['title']['rendered']:
                                                    embed.set_footer(text=f"Status: {status}")
                                                pass
                                            else:
                                                team_name_clean = re.compile("<.*?>")
                                                team = re.sub(team_name_clean, "", player_record[index][field]['team'])
                                                team_link = re.search(r'href=[\'"]?([^\'" >]+)', player_record[index][field]['team'])
                                                team_link_cleaned = team_link.group(0).replace('href="', "")

                                                embed = Embed(
                                                    title=f"**{team} - {player_record[index][field]['name']}**",
                                                    url = team_link_cleaned,
                                                    color = 0x1815C6
                                                )
                                                embed.set_author(
                                                    name=f"{playername} - {league_name}",
                                                    url = f"{player_data[0]['link']}stats"
                                                )
                                                if "&#8211;" in player_data[0]['title']['rendered']:
                                                    embed.set_footer(text=f"Status: {status}")                                            
                                            embed.add_field(
                                                name = "Appearances",
                                                value = player_record[index][field]['appearances'],
                                                inline = True
                                            )
                                            embed.add_field(
                                                name = "W-D-L", value = windrawlost, inline = True
                                            )
                                            embed.add_field(name = "Win - Draw - Loass %", value = ratio, inline = True)
                                            embed.add_field(name = "\u200b", value = "```Offensive Stats```", inline = False)
                                            embed.add_field(name="Goals", value=player_record[index][field]['goals'], inline=True)
                                            embed.add_field(name="G/Game", value=player_record[index][field]['gpg'], inline=True)
                                            embed.add_field(name="SOG - Shots", value=str(player_record[index][field]['sog'])+ " - " + str(player_record[index][field]['shots']), inline=True)
                                            embed.add_field(name="S/Game", value=(str(round(float(player_record[index][field]['shots']) / float(player_record[index][field]['appearances']),2))), inline=True)
                                            embed.add_field(name="Shots/Goal - SH%", value= shotsPerGoal, inline=True)
                                            embed.add_field(name="Assists", value=player_record[index][field]['assists'], inline=True)
                                            embed.add_field(name="Passes - Pass Attempts", value=(str(player_record[index][field]['passescompleted']) + " - " + str(player_record[index][field]['passingattempts'])), inline=True)
                                            embed.add_field(name="Key Passes", value=player_record[index][field]['keypasses'], inline=True)
                                            embed.add_field(name="Assists/Game", value = player_record[index][field]['apg'], inline = True)
                                            embed.add_field(name="P/Game - Pass%", value=(str(avgPassPerGame) + ' - ' + str(player_record[index][field]['passpercent']) + '%'), inline=True)
                                            embed.add_field(name="\u200b", value="```Defensive & Discplinary Stats```", inline=False)
                                            embed.add_field("Tackles", value=player_record[index][field]['tackles'], inline=True)
                                            embed.add_field("Interceptions", value=player_record[index][field]['interceptions'], inline=True)
                                            embed.add_field("TKL-INT/Game", value=tckIntPerGame, inline=True)
                                            embed.add_field("PossW - PossL", value=possessions, inline=True)
                                            embed.add_field("Blocks", value=player_record[index][field]['blocks'], inline=True)
                                            embed.add_field("Headers Won", value=player_record[index][field]['headerswon'], inline=True)
                                            embed.add_field("Clearances", value=player_record[index][field]['clearances'], inline=True)
                                            embed.add_field("Clean Sheets", value=player_record[index][field]['cleansheets'], inline=True)
                                            embed.add_field("Red Cards", value=player_record[index][field]['redcards'], inline=True)
                                            embeds.append(embed)                                    
        except Exception as e:
            self.logger.error(e)
        return embeds

