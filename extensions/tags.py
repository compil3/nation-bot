import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from beanie import Document, Indexed
from naff import (BrandColors, Embed, Guild, Modal, ModalContext,
                  ParagraphText, ShortText, Timestamp, logger_name)
from naff.api.http.http_requests.members import MemberRequests
from naff.client.utils import misc_utils, optional
from naff.models import (AutocompleteContext, Extension, InteractionContext,
                         OptionTypes, Snowflake_Type, slash_command,
                         slash_option, to_snowflake)
from naff.models.naff.application_commands import Permissions, modal_callback
from naff.models.naff.command import cooldown
from naff.models.naff.converters import (ChannelConverter, MemberConverter,
                                         UserConverter)
from naff.models.naff.cooldowns import Buckets
from pydantic import Field
from thefuzz import fuzz, process


def deserialize_datetime(date):
    if isinstance(date, str):
        return datetime.datetime.strptime(date, "%YYYY-%MM-%DDT%HH:%MM:%SS.%f")
    return date


class TagStorage(Document):
    name: str
    content: str
    guild: int
    author_id: int
    user_mention: Optional[list] = None 
    channel_mention: Optional[list] = None
    creation: datetime #= Field(default_factory=datetime.datetime.now)
    modified: Optional[datetime] = None
    modifier_id: Optional[int] = None
    class Collection:
        name = "tags"



class Tags(Extension):
    logger = logging.getLogger(logger_name)
    def __init__(self, bot):
        self.tags = {}
        self.bot = bot
    
    # Gets all tags from db
    async def async_start(self):
        await self.cache()

    async def cache(self):
        try:
            async for tag in TagStorage.find({}):
                await self.get_tag(tag.name)
            self.logger.info(f"Cached {len(self.tags)} tags")
        except Exception as e:
           self.logger.error(e)
    
    async def get_tag(self, tag_name: str) -> TagStorage:
        try:
            if tag_name in self.tags:
                return self.tags[tag_name]
            tag = await TagStorage.find_one(TagStorage.name == tag_name)
            self.tags[tag_name] = tag
            return tag
        except Exception as e:
            self.logger.error(e)

    @slash_command(
        name="tag",
        description="Get a tag",
        default_member_permissions=Permissions.USE_APPLICATION_COMMANDS,
        scopes=[689119429375819951,442081251441115136],
    )
    @slash_option(
        name="tag_name",
        description="The name of the tag to use.",
        opt_type=OptionTypes.STRING,
        required=True,
    )
    async def tag(self, ctx: InteractionContext, tag_name: str):
        await ctx.defer()
        tag = await TagStorage.find_one(TagStorage.name == tag_name.lower().replace("_", " "))
        try:
            if not tag:
                await ctx.send(f"No tag found with the name ``{tag_name}``")
                return
            else:
                if '@' in tag.content or '#' in tag.content:
                        mention = tag.content.split('\n')
                        try:
                            for i in range(len(mention)):
                                if '@' in mention[i] and 'everyone' not in mention[i]:
                                    user_mention = mention[i].split('@')[1].split(' ')[0]
                                    try:
                                        if await UserConverter().convert(ctx, user_mention):                                            
                                            user = await UserConverter().convert(ctx, user_mention)
                                            userId = user.id
                                            mention[i] = mention[i].replace('@', '').replace(user_mention, f'<@{userId}>', 1)
                                    except:
                                        mention[i] = mention[i]
                                if '#' in mention[i]:
                                    channel_mention = mention[i].split('#')[1].split(' ')[0]
                                    if '.' in channel_mention or ',' in channel_mention:                                       
                                        channel_mention = channel_mention.replace('.', '').replace(',', '')
                                    try:
                                        if await ChannelConverter().convert(ctx, channel_mention):
                                            channel = await ChannelConverter().convert(ctx, channel_mention)
                                            channelId = channel.id
                                            mention[i] = mention[i].replace('#', '').replace(channel_mention, f'<#{channelId}>', 1)
                                    except Exception as e:
                                        self.logger.error(e)
                                        mention[i] = mention[i]
                        except:
                            content = content
                        else:
                            content = '\n'.join(mention)
                else:
                    content = tag.content
            await ctx.send(content)
        except Exception as e:
            self.logger.error(e)
    
    @slash_command(
        name="tag-create", 
        description="Create a tag", 
        default_member_permissions=Permissions.MANAGE_ROLES
    )
    @cooldown(bucket=Buckets.USER, rate=1, interval=30)
    async def create_tag(self, ctx: InteractionContext) -> None:
        modal = Modal(
            title="Tag Creation Wizard",
            components= [
                ShortText(
                    label="Tag Name",
                    placeholder="Eg: SL Table",
                    custom_id="name",
                    max_length=40,
                ),
                ParagraphText(
                    label="Tag Contents",
                    placeholder="Maxiumum of 4000 characters.",
                    custom_id="contents",
                    max_length=4000,
                ),
            ],
            custom_id="create_tag",
        )
        await ctx.send_modal(modal)

    @slash_command(
        name="tag-delete", 
        description="Delete a tag",
        default_member_permissions=Permissions.MANAGE_ROLES
    )
    @slash_option("name", "The name of the tag to delete.", OptionTypes.STRING, required=True)
    async def delete_tag(self, ctx: InteractionContext, name: str):
        await ctx.defer(ephemeral=True)
        tag = await TagStorage.find_one(TagStorage.name == name.lower().replace("_", " "))
        if not tag:
            await ctx.send(f"No tag found with the name `{name}`", ephemeral=True)
            return
        try:
            self.tags.pop(name.lower().replace("_", " "))
        except Exception as e:
            self.logger.error(e)
        await tag.delete()
        await ctx.send(f"Deleted tag `{name}`", ephemeral=True)
    
    @slash_command(
        name="tag-details", 
        description="Get details of a tag",
        default_member_permissions=Permissions.USE_APPLICATION_COMMANDS
    )
    @slash_option("name", "The name of the tag to get details of.", OptionTypes.STRING, required=True)
    async def tag_details(self, ctx: InteractionContext, name: str):
        await ctx.defer(ephemeral=True)
        tag = await TagStorage.find_one(TagStorage.name == name.lower().replace("_", " "))
        if tag:          
            author = await ctx.guild.fetch_member(tag.author_id)
            embed = Embed(
                title="Tag Information",
                description=f"{tag.content}",
                color=BrandColors.YELLOW
            )
            embed.add_field("Tag", tag.name)
            embed.add_field("Created At", Timestamp.fromdatetime(tag.creation))
            if tag.modifier_id is not None:
                mod_user = await ctx.guild.fetch_member(tag.modifier_id)
                embed.add_field("Last Modified", Timestamp.fromdatetime(tag.modified))
                embed.add_field("Last Modified By", mod_user.tag)
            embed.set_author(author.tag, icon_url=author.display_avatar.url)

            return await ctx.send(embeds=embed, ephemeral=True)
        return await ctx.send(f"No tag found with the name `{name}`")

    @slash_command(
        name="tag-edit", 
        description="Edit an existing tag",
        default_member_permissions=Permissions.MANAGE_ROLES
    )
    @slash_option("name","The name of the tag to edit.",OptionTypes.STRING,required=True)
    async def edit_tag(self, ctx: InteractionContext, name: str):
        tag = await TagStorage.find_one(TagStorage.name == name.lower().replace("_", " "))
        if tag:
            modal = Modal(
                title="Tag Edit Wizard",
                components= [
                    ShortText(
                        label="Tag Name",
                        value=tag.name,
                        custom_id="name",
                    ),
                    ParagraphText(
                        label="Tag Contents",
                        placeholder="What should this tag say?",
                        value=tag.content,
                        custom_id="contents",
                    ),
                ],
                custom_id="edit_tag",
            )
            return await ctx.send_modal(modal)
        return await ctx.send(f"No tag found with the name `{name}`", ephemeral=True)

    @modal_callback("create_tag", "edit_tag")
    async def tag_modal_rcv(self, ctx: ModalContext):
        name = ctx.responses.get("name")
        content = ctx.responses.get("contents")
        edit_mode = ctx.custom_id == "edit_tag"
        tag = None
        try:
            tag_lookup = await TagStorage.find_one(TagStorage.name == name.lower().replace("_", " "))
            if not edit_mode and tag_lookup:
                return await ctx.send(f"A tag with the name `{name}` already exists")
            if edit_mode:
                tag = tag_lookup
                tag.name = name.lower()
                tag.modifier_id = ctx.author.id
                tag.modified = datetime.now()
                tag.content = content
            if not tag:
                tag = TagStorage(
                    name=name.lower(),
                    content=content,
                    author_id=ctx.author.id,
                    creation=datetime.now(),
                    guild=ctx.guild.id,
                )
            await tag.save()
            if edit_mode:
                self.tags.pop(name.lower().replace("_", " "))
            self.tags[name] = tag
            await ctx.send(f"{'Edited' if edit_mode else 'Created'} `{name}`", ephemeral=True)
        except Exception as e:
            self.logger.error(e)
            await ctx.send("An error occurred", ephemeral=True)

    @slash_command(
        name="tag-cache", 
        description="Update tag cache",
        default_member_permissions=Permissions.MANAGE_ROLES
    )
    async def update_cache(self, ctx: InteractionContext):
        await ctx.defer(ephemeral=True)
        try:
            async for tag in TagStorage.find({}):
               await self.get_tag(tag.name)
            await ctx.send(f"Updated tag cache\nCached {len(self.tags)}", ephemeral=True)
        except Exception as e:
            self.logger.error(e)
            await ctx.send(f"An error occurred while caching tags.\n{e}", ephemeral=True)


    
    @tag.autocomplete("tag_name")
    @delete_tag.autocomplete("name")
    @tag_details.autocomplete("name")
    @edit_tag.autocomplete("name")
    async def tag_autocomplete(self, ctx: AutocompleteContext, **kwargs):
        tags = self.tags.keys()
        output = []
        if tags:
            if ctx.input_text:
                print(ctx.input_text)
                result = process.extract(ctx.input_text, tags, scorer=fuzz.partial_token_sort_ratio)
                output = [t[0] for t in result if t[1] > 50]
            else:
                output = list(tags)[:25]
            return await ctx.send(output)

def setup(bot):
    Tags(bot)
    bot.add_model(TagStorage)
