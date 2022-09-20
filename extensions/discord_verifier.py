# from loguru import logger
import logging
import re
from datetime import datetime

import aiohttp
import orjson
from beanie import Document
from naff import (ActionRow, AutoArchiveDuration, BrandColors, Button,
                  ButtonStyles, ComponentContext, Embed, Extension,
                  InteractionContext, Member, Missing, Modal, ModalContext,
                  ParagraphText, PartialEmoji, Permissions, PrefixedContext,
                  ShortText, Snowflake_Type, component_callback, logger_name,
                  prefixed_command, slash_command, to_snowflake)
from naff.client.utils import misc_utils, optional
from naff.models.naff.application_commands import modal_callback
from naff.models.naff.converters import ChannelConverter, RoleConverter

logo = "https://proclubsnation.com/wp-content/uploads/2021/10/PCN_logo_new.png"
# logger = logging.getLogger()
class VerificationQueue(Document):
    discord_id: int
    discord_name: str
    gamertag: str
    status: str
    reason: str
    updated: datetime
    discord_thread: int

    class Collection:
        name = "verification_queue"

#Discord auto-verification
class DiscordVerification(Extension):
    logger = logging.getLogger(logger_name)
    @prefixed_command()
    async def verify_init(self, ctx: PrefixedContext):
        if ctx.author.id not in [111252573054312448, 421064675267051531]:
            return
        await ctx.message.delete()
        threads = await ChannelConverter().convert(ctx, "verification-threads")
        general = await ChannelConverter().convert(ctx, "general-discussion")
        embed = Embed(title="Welcome to PCN Discord", description=f"""1.    Discord is provided as a courtesy by the owners of PCN, meaning that it is a privilege, not a right
                2.    Show respect to all Staff members, Managers, and Players at all times
                3.    <#{general.id}> is the only chat that can be used for cutting up or friendly banter
                4.    All special chat channels are to be used ONLY for their intended purposes. Repeated abuse of this rule may lead to disciplinary action and possible stripping of roles on Discord
                5.    No spamming or flooding the chat with messages, and do not type in ALL CAPS
                6.    No large paragraphs of text or text walls
                7.    No personal attacks or harassment of anyone
                8.    No racist, homophobic, or sexist content or language
                9.    No excessive use of profanity
                10.    No advertising other leagues or discord servers (Permission must be requested from a member of staff)
                11.     No referral links
                12.    Players must have their Discord name match their gamertag
                13.    Do not use the @everyone / @here / @Admin  in chat without permission
                14.    Do not argue with any member of the staff as all decisions are final
                15.    No pornography or inappropriate profile pictures
                16.    No discussion of politics or religion will be allowed
                17.    Repeated violations will result in suspensions, temporary or permanent at the discretion of the Admins
                
                To gain access to PCN Discord, press "Start Verification".\nOnce you have, check the <#{threads.id}> channel for your thread.\n
                If you are looking to join our UFC League, please press the PCN UFC button below.\n
                """, color=BrandColors.BLURPLE)

        icon = PartialEmoji.from_str("<:rotating_light:1006193707197935626>")
        try:
            components: list[ActionRow] = [ActionRow(Button(style=ButtonStyles.BLURPLE, label="Start Verification", custom_id="create_verification_thread"), Button(style=ButtonStyles.BLURPLE, label="PCN UFC", custom_id="pcn_ufc"))]

        except Exception as e:
            self.logger.error(e)
        embed.set_footer("PCN Staff", icon_url=logo)
        await ctx.send(embeds=embed, components=components)

    @modal_callback("verification_thread_modal")
    async def create_thread(self, ctx: ModalContext):
        await ctx.defer(ephemeral=True)
        threads = await ChannelConverter().convert(ctx, "verification-threads")
        channel = await self.bot.fetch_channel(threads.id)
        current_tag = ctx.responses.get("gamertag")
        if "https://proclubsnation.com/members" in current_tag:
            current_tag = current_tag.replace("https://proclubsnation.com/members/", "")
        elif "https://proclubsnation.com/player/" in current_tag:
            current_tag = current_tag.replace("https://proclubsnation.com/player/", "")
        previous_tag = ctx.responses.get("previous_gamertag")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.bot.config.urls.find_player.format(f"{current_tag}&_fields=title,link,date,modified,slug"), ssl=False) as resp:
                    if resp.status == 200:
                        gt_lookup = await resp.text()
                        search_response = orjson.loads(gt_lookup)
                        if len(search_response) < 1:
                                await ctx.author.add_role(await RoleConverter().convert(ctx, "Waiting Verification"), "Waiting for verification.")
                                await ctx.author.remove_role(await RoleConverter().convert(ctx, "New Member"), "Verification started")

                                thread = await channel.create_private_thread(
                                    name=f"{ctx.author.display_name}'s Verification",
                                    auto_archive_duration=AutoArchiveDuration.ONE_WEEK,
                                    reason="Verification Thread",
                                    invitable=False,
                                )
                                await thread.add_member(ctx.author.id)

                                if not previous_tag:
                                    previous_tag = "--"

                                await thread.send(
                                    f"Welcome to your verification thread, {ctx.author.mention}."
                                    "\nThis thread was created automatically by the bot due to your Gamer Tag not being found.\n\n"
                                    "**Provided Information:**\n\n"
                                    f"Gamertag: **{current_tag}**\n"
                                    f"Previous Gamertags: **{previous_tag}**\n"
                                    "Verified Onsite: **False**"         
                                    "\n\n**Please make sure you have Direct Messages enabled for this server."
                                    "\nYou will be notified via DM when access is granted.**"
                                    "\nTo enble DMs for this server only on mobile, click server name > Allow Direct Messages."
                                    "\nTo enable DMs for this server only on desktop, click server name > Privacy Settings > Allow Direct Messages."
                                    "\n\n**Discord verifications are automatically checked every 48 hours.**"
                                )

                
                                await ctx.send(f"{ctx.author.mention} Your verification thread has been created here: {thread.mention}", ephemeral=True)

                                existing_verification = await VerificationQueue.find_one({"discord_id": ctx.author.id})
                                if existing_verification is None:    
                                    waiting_verification = VerificationQueue(
                                        discord_id=ctx.author.id,
                                        discord_name=ctx.author.display_name,
                                        gamertag=current_tag,
                                        status="New",
                                        reason="Waiting for website verification",
                                        updated=datetime.now(),
                                        discord_thread=thread.id,
                                    )
                                    await waiting_verification.save()
                        else:
                            for db_player in search_response:
                                if re.match(current_tag, db_player['title']['rendered'], flags=re.I):
                                    async with session.get(self.bot.config.urls.players.format(db_player['slug'])) as gamertag_lookup:
                                        if gamertag_lookup.status == 200:
                                            lookup = await gamertag_lookup.text()
                                            player_found = orjson.loads(lookup)

                                            if len(player_found) < 1:                                            
                                                await ctx.author.add_role(await RoleConverter().convert(ctx, "Waiting Verification"), "Waiting for verification.")
                                                await ctx.author.remove_role(await RoleConverter().convert(ctx, "New Member"), "Verification started")
                                                thread = await channel.create_public_thread(
                                                    name=f"{ctx.author.display_name}'s Verification",
                                                    auto_archive_duration=AutoArchiveDuration.ONE_WEEK,
                                                    reason="Verification Thread",
                                                    # invitable=True,
                                                )
                                                await thread.add_member(ctx.author.id)

                                                if not previous_tag:
                                                    previous_tag = "--"

                                                await thread.send(
                                                    f"Welcome to your verification thread, {ctx.author.mention}."
                                                    "\nThis thread was created automatically by the bot due to your Gamer Tag not being found.\n\n"
                                                    "**Provided Information:**\n\n"
                                                    f"Gamertag: **{current_tag}**\n"
                                                    f"Previous Gamertags: **{previous_tag}**\n"
                                                    "Verified Onsite: **False**"         
                                                    "\n\n**Please make sure you have Direct Messages enabled for this server."
                                                    "\nYou will be notified via DM when access is granted.**"
                                                    "\nTo enble DMs for this server only on mobile, click server name > Allow Direct Messages."
                                                    "\nTo enable DMs for this server only on desktop, click server name > Privacy Settings > Allow Direct Messages."
                                                    "\n\n**Discord verifications are automatically checked every 24 hours.**"
                                                )

                                
                                                await ctx.send(f"{ctx.author.mention} Your verification thread has been created here: {thread.mention}", ephemeral=True)

                                                existing_verification = await VerificationQueue.find_one({"discord_id": ctx.author.id})
                                                if existing_verification is None:    
                                                    waiting_verification = VerificationQueue(
                                                        discord_id=ctx.author.id,
                                                        discord_name=ctx.author.display_name,
                                                        gamertag=current_tag,
                                                        status="New",
                                                        reason="Waiting for website verification",
                                                        updated=datetime.now(),
                                                        discord_thread=thread.id,
                                                    )
                                                    await waiting_verification.save()
                                                else:
                                                    pass
                                            else:
                                                try:
                                                    await ctx.author.add_role(await RoleConverter().convert(ctx, "Player"), "Granted Access")
                                                    await ctx.author.remove_role(await RoleConverter().convert(ctx, "New Member"), "Removed from New member role.")
                                                    await ctx.send(f"{ctx.author.mention} have been automatically verified and have been granted access to the PCN Discord.", ephemeral=True)
                                                    await ctx.author.edit_nickname(f"{current_tag}", "Verified User")                   
                                                except Exception as e:
                                                    self.logger.error(e)
        except Exception as e:
            self.logger.error(e)

    @component_callback("create_verification_thread", "pcn_ufc")
    async def verification_thread_button(self, ctx: ComponentContext):
        try:
            match ctx.custom_id:
                case "create_verification_thread":
                    try:
                        verification_modal = Modal(
                                title="Verification Wizard",
                                components=[
                                    ShortText(
                                        label="Gamer Tag",
                                        custom_id="gamertag",
                                        placeholder="Found in profile url: proclubsnation.com/player/GAMERTAG",
                                        required=True,
                                    ),
                                    ShortText(
                                        label="Previously Registered Gamer Tag",
                                        custom_id="previous_gamertag",
                                        placeholder="Please enter any previous gamertags you have used on PCN.",
                                        required=False,
                                    ),
                                ],
                                custom_id="verification_thread_modal",
                            )
                        await ctx.send_modal(modal=verification_modal)
                    except Exception as e:
                        print(e)
                case "pcn_ufc":
                    await ctx.author.add_role(await RoleConverter().convert(ctx, "UFC Fighter"))
                    await ctx.send("You now have access to PCN UFC Channels.\nIf you wish to participate in our FIFA league please come back to this channel and click 'Start Verification'.", ephemeral=True)
        except Exception as e:
            print(e.search_for_message())
            # logger.error(e.search_for_message())

        

    @slash_command(
        name="verification",
        description="Starts the verificaiton threading for the bot",
        scopes=[689119429375819951,442081251441115136],
        default_member_permissions=Permissions.USE_APPLICATION_COMMANDS
    )
    async def verification_threader(self, ctx: InteractionContext):
        await self.verification_thread_button(ctx)

def setup(bot):
    DiscordVerification(bot)
    bot.add_model(VerificationQueue)


    