import copy
import logging
import re
from distutils.command import check

import aiohttp
import orjson
from aiocache import Cache, cached
# from loguru import logger
from naff import BrandColors, Embed, logger_name


class PlayerStatsBuilder:
    logger = logging.getLogger(logger_name)
    @cached(ttl=300)
    async def builder(self, gamertag: str):
        
        embeds = []
        league_name = ""
        try:
            # if " " in gamertag.lower():
            #     gamertag = gamertag.lower().replace(" ", "-")               

            async with aiohttp.ClientSession() as session:
                async with session.get(self.bot.config.urls.find_player.format(f"{gamertag.lower()}&_fields=title,slug")) as player_search:
                    if player_search.status == 200:
                        player_search_response = await player_search.text()
                        sdata = orjson.loads(player_search_response)
                        league_fields = ['21', '26','27', '110', '111', '112']
                        leagues = []
                        total_only_league = ['110','111','112']
                        stats_data = {}
                        
                        totals = 0
                        p_apps = 0
                        t_win_record = 0
                        t_draw_record = 0
                        t_loss_record = 0
                        t_record = ''
                        t_win_percent = 0.0
                        t_save_percentage = 0.0
                        t_win_ratio = 0.0
                        t_gaa = 0.0
                        t_shots_against = 0 
                        t_goals_against = 0
                        t_saves = 0
                        t_clean_sheets = 0
                        t_passes_comp = 0
                        t_passes_att = 0
                        t_pass_percent = 0.0
                        t_goals = 0
                        t_gpg = 0.0
                        t_sog = 0
                        t_shots = 0
                        t_shots_per_game = 0.0
                        t_shots_per_goal = 0.0
                        t_assists = 0
                        t_assist_per_game = 0.0
                        t_passes = 0
                        t_pass_att = 0
                        t_pass_percentage = 0.0
                        t_crosses = 0
                        t_cross_att = 0
                        t_keypass = 0                        
                        t_beaten = 0
                        t_interceptions = 0
                        t_tackles = 0
                        t_tackle_game = 0
                        t_int_game = 0.0
                        t_possession_won = 0
                        t_possession_lost = 0
                        t_blocks = 0
                        t_airduels = 0
                        t_clearances = 0
                        t_cleansheets = 0
                        t_fouls = 0
                        t_redcards = 0

                        if len(sdata) < 1:
                            embeds = None
                            return embeds
                        else:
                            for player in sdata:
                                if re.match(gamertag, player["title"]['rendered'], flags=re.I):
                                    async with session.get(self.bot.config.urls.players.format(player['slug'])) as player_data:
                                        if player_data.status == 200:
                                            player_data_response = await player_data.text()
                                            pdata = orjson.loads(player_data_response)
                                        
                                            if len(pdata) < 1:
                                                embeds = None
                                                return embeds
                                            else:
                                                api_data = pdata[0]['statistics']
                                                stats = api_data.copy()
                                                embed_wrote = False
                                                last_comp = False
                                                print(type(stats))

                                                # check indexes/fields for valid stats and write new list of valid stats
                                                for check_index in api_data:
                                                    if check_index not in league_fields:
                                                        continue
                                                    for check_field in api_data[check_index]:
                                                        if check_field == '0':
                                                            pass
                                                        if 'appearances' not in api_data[check_index][check_field] or api_data[check_index][check_field]['appearances'] == 0 or api_data[check_index][check_field]['appearances'] == '0':
                                                            del stats[check_index][check_field]
                                                        else:
                                                            pass
                                                            # holding_data = {
                                                            #     'field': check_field,
                                                            # }
                                                            

                                                            
                                                # check if field    
                                                for index in league_fields:
                                                    if embed_wrote:
                                                        embed_wrote = False
                                                    if index not in stats:
                                                        continue
                                                    else:
                                                        pass
                                                    for field in stats[index]:
                                                        # check all league_fields if 
                                                        if embed_wrote:
                                                            continue
                                                        if field == '0':
                                                            pass
                                                        elif 'appearances' not in stats[index][field]: 
                                                            pass

                                                        # when it's 112 and no stats are found it skips everything else.
                                                        elif stats[index][field]['appearances'] == '0' or stats[index][field]['appearances'] == 0:
                                                            pass
                                                        else:
                                                            match index:
                                                                case '21':
                                                                    league_name = 'Super League'
                                                                case '27':
                                                                    league_name = 'League One'
                                                                case '26':
                                                                    league_name = 'League Two'
                                                                case '105':
                                                                    league_name = 'Regions Cup'
                                                                case '106':
                                                                    league_name = 'World Cup'
                                                                case '110':
                                                                    league_name = 'Royal Cup'
                                                                case '111':
                                                                    league_name = 'PCN Cup'
                                                                case '112':
                                                                    league_name = 'Super Cup'
                                                                # default case
                                                                case _:
                                                                    league_name = stats[index][field]['name']
                                                            


                                                            if index in total_only_league:                                                                
                                                                field = '-1'
                                                            if index == '112':
                                                                last_comp = True

                                                            if "&#8211;" in pdata[0]['title']['rendered']:
                                                                player_name, status = pdata[0]['title']['rendered'].split("&#8211;")
                                                            else:
                                                                player_name = pdata[0]['title']['rendered']

                                                            win_record = round(int(stats[index][field]['appearances']) * float(stats[index][field]['winratio']) / 100, 2) 
                                                            draw_record =round(int(stats[index][field]['appearances']) * float(stats[index][field]['drawratio']) / 100, 2)
                                                            loss_record = round(int(stats[index][field]['appearances']) * float(stats[index][field]['lossratio']) / 100, 2)
                                                            record = str(win_record).replace(".0","") + "-" + str(draw_record).replace(".0","") + "-" + str(loss_record).replace(".0","")
                                                            if field == '-1':
                                                                t_win_record +=  int(win_record)
                                                                t_draw_record +=  int(draw_record)
                                                                t_loss_record += int(loss_record)
                                
                                                            apps = float(stats[index][field]['appearances'])

                                                            # check if goalie & goalie stats
                                                            #TODO: fix goalie stats to work correctly

                                                            if int(stats[index][field]['saves']) > 1:
                                                                # goalie stats function
                                                                gaa = (float(stats[index][field]['goalsconceded']) / (apps * 90)) * 90

                                                                if stats[index][field]['name'] == 'Total':
                                                                    embed = Embed(
                                                                        title = f"**{league_name} - Career Totals**",
                                                                        color = BrandColors.WHITE
                                                                    )
                                                                    embed.set_author(
                                                                        name = f"{player_name} - GK",
                                                                        url = f"{pdata[0]['link']}stats"
                                                                    )
                                                                    if "&#8211;" in pdata[0]['title']['rendered']:
                                                                        embed.set_footer(text=f"Status: {status}")
                                                                else:
                                                                    team_name_strip = re.compile("<.*?>")
                                                                    team = re.sub(team_name_strip, "", stats[index][field]['team'])
                                                                    t_link = re.search(r'href=[\'"]?([^\'" >]+)', stats[index][field]['team'])
                                                                    team_link = t_link.group(0).replace('href="', "")

                                                                    embed = Embed(
                                                                        title=f"**{team} - {stats[index][field]['name']}**",
                                                                        url = team_link,
                                                                        color=BrandColors.WHITE
                                                                    )
                                                                    embed.set_author(
                                                                        name=f"{player_name} - {league_name}",
                                                                        url = f"{pdata[0]['link']}stats"
                                                                    )
                                                                    if "&#8211;" in pdata[0]['title']['rendered']:
                                                                        embed.set_footer(text=f"Status: {status}")

                                                                embed.add_field("Appearances", stats[index][field]['appearances'], inline=True)
                                                                embed.add_field("W-D-L", record, inline=True)
                                                                embed.add_field("Win %", f"{round(float(stats[index][field]['winratio']), 2)}%", inline=True)
                                                                embed.add_field("\u200b", "```Stats```", inline=False)
                                                                embed.add_field("Shots Against", stats[index][field]['shotsontargetgk'], inline=True)
                                                                embed.add_field("Goals Against", stats[index][field]['goalsconceded'], inline=True)
                                                                embed.add_field("Goals Against Average", gaa, inline=True)                                                            
                                                                embed.add_field("Saves", stats[index][field]['saves'], inline=True)
                                                                # if stats[index][field]['shotsontargetgk'] == 0:
                                                                #     embed.add_field("Save %", "Stat not found", inline=True)
                                                                # else:
                                                                #     save_percentage = round(float(stats[index][field]['saves'] / float(stats[index][field]['shotsontargetgk']) * 100), 2)  
                                                                #     embed.add_field("Save %", save_percentage, inline=True)
                                                                embed.add_field("Clean Sheets", stats[index][field]['cleansheets'], inline=True)
                                                                embed.add_field("\u200b", "```Other```", inline=False)
                                                                embed.add_field("Passes Completed", stats[index][field]['passescompleted'], inline=True)
                                                                embed.add_field("Pass Attempts", stats[index][field]['passingattempts'], inline=True)
                                                                embed.add_field("Pass %", stats[index][field]['passpercent'], inline=True)
                                                                embeds.append(embed)


                                                                # t_pass_percent += round(float(stats[index][field]['passpercent']),2) / p_apps
                                                                if field == '-1':
                                                                    p_apps += int(stats[index][field]['appearances'])
                                                                    t_record = str(t_win_record) + "-" + str(t_draw_record) + "-" + str(t_loss_record)
                                                                    t_win_percent = round(float(t_win_record / p_apps) * 100,2)
                                                                    t_shots_against += stats[index][field]['shotsontargetgk']
                                                                    t_goals_against += stats[index][field]['goalsconceded']
                                                                    t_gaa = round(float(t_goals_against / p_apps), 2)
                                                                    t_saves += stats[index][field]['saves'] 
                                                                    t_clean_sheets += stats[index][field]['cleansheets']
                                                                    t_passes_comp += stats[index][field]['passescompleted']
                                                                    t_passes_att += stats[index][field]['passingattempts']
                                                                    embed_wrote = True
            
                                                                if last_comp:
                                                                    embed = Embed(
                                                                        title=f"**PCN Career Totals**",
                                                                        url = team_link,
                                                                        color=BrandColors.WHITE
                                                                    )
                                                                    embed.set_author(
                                                                        name=f"{player_name}",
                                                                        url = f"{pdata[0]['link']}stats"
                                                                    )
                                                                    if "&#8211;" in pdata[0]['title']['rendered']:
                                                                        embed.set_footer(text=f"Status: {status}") 
                                                                    embed.add_field("Appearances", p_apps, inline=True)
                                                                    embed.add_field("W-D-L", t_record, inline=True)
                                                                    embed.add_field("Win %", str(t_win_percent) + "%", inline=True)
                                                                    embed.add_field("\u200b", "```Stats```", inline=False)
                                                                    embed.add_field("Shots Against", t_shots_against, inline=True)
                                                                    embed.add_field("Goals Against", t_goals_against, inline=True)
                                                                    embed.add_field("Goals Against Average", t_gaa, inline=True)
                                                                    embed.add_field("Saves", t_saves, inline=True)
                                                                    # embed.add_field("Save %", t_save_percentage, inline=True)
                                                                    embed.add_field("Clean Sheets", t_clean_sheets, inline=True)
                                                                    embed.add_field("\u200b", "```Other```", inline=False)
                                                                    embed.add_field("Passes Completed", t_passes_comp, inline=True)
                                                                    embed.add_field("Pass Attempts", t_passes_att, inline=True)
                                                                    embed.add_field("Pass %", str(round(t_passes / t_pass_att * 100,0)).replace(".0","") + "%", inline=True)
                                                                    embeds.append(embed)
                                                                    
                                                                
                                                            
                                                            # check if player isn't a goalie
                                                            elif int(stats[index][field]['saves']) < 1:
                                                                # player stats function
                                                                avg_pass_game = str(round(float(stats[index][field]['passescompleted']) / float(stats[index][field]['appearances']), 2))

                                                                #Need this
                                                                tackle_per_game = str(round(float(stats[index][field]['tackles']) / float(stats[index][field]['appearances']), 2))
                                                                int_per_game = str(round(float(stats[index][field]['interceptions']) / float(stats[index][field]['appearances']), 2))
                                                                tacklesInt_game = str(tackle_per_game) + " - " + str(int_per_game)
                                                                #
                                                                possessions = str(stats[index][field]['possessionswon']) + " - " + str(stats[index][field]['possessionslost'])
                                                                tackle_beaten = str(stats[index][field]['tackles']) + " - " + str(stats[index][field]['beatenbyopponnent'])

                                                                    

                                                                if int(stats[index][field]['goals']) >= 1:
                                                                    shotsPerGoal = round(float(stats[index][field]['shots']) / float(stats[index][field]['goals']), 2)
                                                                    shotsPerGoal = str(shotsPerGoal) + " - " + str(stats[index][field]['shpercent']) + "%"
                                                                    shooting_accuracy = str(round(float(stats[index][field]['goals']) / float(stats[index][field]['sog']), 2) * 100) + "%"
                                                                else:
                                                                    shotsPerGoal = ('0.0' + " - " + str(stats[index][field]['shpercent']) + "%")

                                                                
                                                                sog_shot = str(stats[index][field]['sog']) + " - " + str(stats[index][field]['shots'])
                                                                shots_per_game = str(round(float(stats[index][field]['shots']) / float(stats[index][field]['appearances']),2))
                                                                passes = str(stats[index][field]['passescompleted']) + " - " + str(stats[index][field]['passingattempts'])
                                                                assists = str(stats[index][field]['assists']) + " - " + str(stats[index][field]['apg'])
                                                                pass_game_percentage = str(avg_pass_game) + ' - ' + str(stats[index][field]['passpercent']) + '%'

                                                                if stats[index][field]['airduelswon'] == 0 and stats[index][field]['headerswon'] > 0:
                                                                    airduels = stats[index][field]['headerswon']
                                                                elif stats[index][field]['headerswon'] == 0 and stats[index][field]['airduelswon'] > 0:
                                                                    airduels = stats[index][field]['airduelswon']
                                                                elif stats[index][field]['airduelswon'] == 0 and stats[index][field]['headerswon'] == 0:
                                                                    airduels = 0
                                                                
                                                                crossing = str(stats[index][field]['crossescompleted']) + " - " + str(stats[index][field]['crossesattempted'])

                                                                # pcn career totals

                                                                if stats[index][field]['name'] == 'Total':
                                                                    embed = Embed(
                                                                        title=f"**{league_name} - Career Totals**",
                                                                        color=BrandColors.WHITE
                                                                    )
                                                                    embed.set_author(
                                                                        name=f"{player_name} - {league_name}",
                                                                        url = f"{pdata[0]['link']}stats"                                                                        
                                                                    )

                                                                    if "&#8211;" in pdata[0]['title']['rendered']:
                                                                        embed.set_footer(text=f"Status: {status}")
                                                                    pass
                                                                else:
                                                                    team_name_strip = re.compile("<.*?>")
                                                                    team = re.sub(team_name_strip, "", stats[index][field]['team'])
                                                                    t_link = re.search(r'href=[\'"]?([^\'" >]+)', stats[index][field]['team'])
                                                                    team_link = t_link.group(0).replace('href="', "")

                                                                    embed = Embed(
                                                                        title=f"**{team} - {stats[index][field]['name']}**",
                                                                        url = team_link,
                                                                        color=BrandColors.WHITE
                                                                    )
                                                                    embed.set_author(
                                                                        name=f"{player_name} - {league_name}",
                                                                        url = f"{pdata[0]['link']}stats"
                                                                    )
                                                                    if "&#8211;" in pdata[0]['title']['rendered']:
                                                                        embed.set_footer(text=f"Status: {status}")     
                                                                embed.add_field("Appearances", stats[index][field]['appearances'], inline=True)
                                                                embed.add_field("W-D-L", record, inline=True)
                                                                embed.add_field("Win %", f"{round(float(stats[index][field]['winratio']), 2)}%", inline=True)
                                                                embed.add_field("\u200b", "```Stats```", inline=False)
                                                                embed.add_field("Goals", stats[index][field]['goals'], inline=True)
                                                                embed.add_field("G/Game", stats[index][field]['gpg'], inline=True)
                                                                embed.add_field("SOG - Shots", sog_shot, inline=True)
                                                                embed.add_field("S/Game", shots_per_game, inline=True)
                                                                embed.add_field("S/G", shotsPerGoal, inline=True)
                                                                embed.add_field("Assists - A/G", assists, inline=True)
                                                                embed.add_field("Passes - Pass Atempts", passes, inline=True)
                                                                embed.add_field("Crosses - Cross Atempts", crossing, inline=True)
                                                                embed.add_field("Key Passes", stats[index][field]['keypasses'], inline=True)
                                                                embed.add_field("P/Game - Pass %", pass_game_percentage, inline=True)
                                                                embed.add_field("\u200b", "```Defensive & Disciplinary Stats```", inline=False)
                                                                embed.add_field("Tackles - Times Beaten", tackle_beaten, inline=True)
                                                                embed.add_field("Interceptions", stats[index][field]['interceptions'], inline=True)
                                                                embed.add_field("TKL - Int/Game", tacklesInt_game, inline=True)
                                                                embed.add_field("PossW - PossL", possessions, inline=True)
                                                                embed.add_field("Blocks", stats[index][field]['blocks'], inline=True)
                                                                embed.add_field("Air Duels Won", airduels, inline=True)
                                                                embed.add_field("Clearances", stats[index][field]['clearances'], inline=True)
                                                                embed.add_field("Clean Sheets", stats[index][field]['cleansheets'], inline=True)
                                                                embed.add_field("Fouls", stats[index][field]['foulscommitted'], inline=True)
                                                                embed.add_field("Red Cards", stats[index][field]['redcards'], inline=True)
                                                                embeds.append(embed)

                                                             
                                                                if field == '-1':

                                                                    if stats[index][field]['headerswon'] > 0:
                                                                        t_airduels += stats[index][field]['headerswon']
                                                                    if stats[index][field]['airduelswon'] > 0:
                                                                        t_airduels += stats[index][field]['airduelswon']
                                                                    if stats[index][field]['airduelswon'] == 0 and stats[index][field]['headerswon'] == 0:
                                                                        t_airduels += 0
                                                                    totals += 1
                                                                    p_apps += int(stats[index][field]['appearances'])
                                                                    t_record = str(t_win_record) + "-" + str(t_draw_record) + "-" + str(t_loss_record)
                                                                    t_win_percent = round(float(t_win_record / p_apps) * 100, 2)
                                                                    t_goals += stats[index][field]['goals']
                                                                    t_gpg = round(float(t_goals / p_apps), 0)
                                                                    t_sog += stats[index][field]['sog']
                                                                    t_shots += stats[index][field]['shots']
                                                                    t_shots_per_game = round(t_shots / p_apps, 2)
                                                                    t_shots_per_goal = round(t_shots / t_goals, 2)
                                                                    t_assists += stats[index][field]['assists']
                                                                    t_assist_per_game = round(t_assists / p_apps,2)
                                                                    t_passes += stats[index][field]['passescompleted']
                                                                    t_pass_att += stats[index][field]['passingattempts']
                                                                    t_pass_percentage += round(float(stats[index][field]['passpercent']), 2)
                                                                    t_crosses += stats[index][field]['crossescompleted']
                                                                    t_cross_att += stats[index][field]['crossesattempted']
                                                                    t_keypass += stats[index][field]['keypasses']
                                                                    t_tackles += stats[index][field]['tackles']                                            
                                                                    t_tackle_game = round(t_tackles / p_apps,2)
                                                                    t_beaten += stats[index][field]['beatenbyopponnent']
                                                                    t_interceptions += stats[index][field]['interceptions']
                                                                    t_int_game = round(t_interceptions / p_apps, 2)
                                                                    t_possession_won += stats[index][field]['possessionswon']
                                                                    t_possession_lost += stats[index][field]['possessionslost']
                                                                    t_blocks += stats[index][field]['blocks']

                                                                    # TODO: fix airduels not having correct amount
                                                                    # t_airduels += airduels
                                                                    t_clearances += stats[index][field]['clearances']
                                                                    t_cleansheets += stats[index][field]['cleansheets']
                                                                    t_fouls += stats[index][field]['foulscommitted']
                                                                    t_redcards += stats[index][field]['redcards']
                                                                    embed_wrote = True
                                                                if last_comp:
                                                                    embed = Embed(
                                                                        title=f"**PCN Career Totals**",
                                                                        url = team_link,
                                                                        color=BrandColors.WHITE
                                                                    )
                                                                    embed.set_author(
                                                                        name=f"{player_name}",
                                                                        url = f"{pdata[0]['link']}stats"
                                                                    )
                                                                    if "&#8211;" in pdata[0]['title']['rendered']:
                                                                        embed.set_footer(text=f"Status: {status}")                                                            
                                                                    embed.add_field("Appearances", p_apps, inline=True)
                                                                    embed.add_field("W-D-L", str(t_record), inline=True)
                                                                    embed.add_field("Win %", str(t_win_percent) + "%", inline=True)
                                                                    embed.add_field("\u200b", "```Stats```", inline=False)
                                                                    embed.add_field("Goals", t_goals, inline=True)
                                                                    embed.add_field("G/Game", t_gpg, inline=True)
                                                                    embed.add_field("SOG - Shots", str(t_sog) + " - " + str(t_shots), inline=True)
                                                                    embed.add_field("S/Game",t_shots_per_game, inline=True)
                                                                    embed.add_field("S/G", t_shots_per_goal, inline=True)
                                                                    embed.add_field("Assists - A/G", str(t_assists) + " - " + str(t_assist_per_game), inline=True)
                                                                    embed.add_field("Passes - Pass Atempts", str(t_passes) + " - " + str(t_pass_att), inline=True)
                                                                    embed.add_field("Crosses - Cross Atempts", str(t_crosses) + " - " + str(t_cross_att), inline=True)
                                                                    embed.add_field("Key Passes", t_keypass, inline=True)
                                                                    embed.add_field("P/Game - Pass %",  str(round(t_passes / p_apps,2)) + " - " +  str(round(t_passes / t_pass_att * 100,0)).replace(".0","") + "%", inline=True)
                                                                    embed.add_field("\u200b", "```Defensive & Disciplinary Stats```", inline=False)
                                                                    embed.add_field("Tackles - Times Beaten", str(t_tackles) + ' - ' + str(t_beaten), inline=True)
                                                                    embed.add_field("Interceptions", t_interceptions, inline=True)
                                                                    embed.add_field("TKL - Int/Game", str(round(t_tackle_game,2)) + ' - ' + str(t_int_game), inline=True)
                                                                    embed.add_field("PossW - PossL", str(t_possession_won) + " - " + str(t_possession_lost), inline=True)
                                                                    embed.add_field("Blocks", t_blocks, inline=True)
                                                                    embed.add_field("Air Duels Won", t_airduels, inline=True)
                                                                    embed.add_field("Clearances",t_clearances, inline=True)
                                                                    embed.add_field("Clean Sheets", t_cleansheets, inline=True)
                                                                    embed.add_field("Fouls", t_fouls, inline=True)
                                                                    embed.add_field("Red Cards", t_redcards, inline=True)
                                                                    embeds.append(embed)                                                                

        except Exception as e:
            self.logger.error(e.search_for_message())
        return embeds
