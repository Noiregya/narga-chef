"""Main module for the Narga Chef discord bot"""

# Imports
import os
from dotenv import load_dotenv
from interactions import (
    Client,
    Intents,
    listen,
    slash_command,
    slash_option,
    OptionType,
    SlashContext,
    Permissions,
    Member,
    ChannelType,
    BaseChannel,
)
from interactions.api.events import MessageCreate, Component
import dao.dao as dao
import business
import tools

# Inititialization
load_dotenv()
TOKEN = os.environ.get("token")
intents = Intents.MESSAGE_CONTENT | Intents.GUILD_MESSAGES | Intents.GUILDS
bot = Client(intents=intents)


# Listeners
@listen()
async def on_message_create(ctx: MessageCreate):
    """When the discord bot sees a message"""
    image = tools.get_first_image_attachement(ctx.message)
    if image is not None:
        return await business.image_received(ctx, image)


@listen(Component)
async def on_component(event: Component):
    """When a component is interacted with"""
    ctx = event.ctx
    event_type, req_member, unique, data1 = ctx.custom_id.split(",")
    match [event_type, req_member, unique, data1]:  # Read component event id
        # Name field has been set
        case ["type", *_]:
            request_type = ctx.values[0]
            return await business.type_component(
                ctx, request_type, event_type, req_member, unique
            )
        case ["name", *_]:
            name = ctx.values[0]
            return await business.name_component(
                ctx, name, event_type, req_member, unique
            )
        # Effect field has been set
        case ["effect", *_]:
            effect = ctx.values[0]
            return await business.effect_component(ctx, effect, req_member, unique)
        case ["accept", *_]:
            value = data1
            return await business.accept_component(ctx, req_member, unique, value)
        case ["deny", *_]:
            value = data1
            return await business.deny_component(ctx, req_member, unique, value)
        case _:
            response = f"Something went wrong, unknown interaction {ctx.custom_id}"
    return await ctx.edit_origin(content=response, components=[])


@slash_command(
    name="setup",
    description="Set up the bot for this server",
    default_member_permissions=Permissions.MANAGE_GUILD,
)
@slash_option(
    name="currency",
    description="Name of the points to be collected",
    opt_type=OptionType.STRING,
    required=True,
)
@slash_option(
    name="cooldown",
    description="Delay before the member is allowed to submit again (in hours)",
    opt_type=OptionType.INTEGER,
    required=True,
)
@slash_option(
    name="submission_channel",
    description="Channel you want members to submit to",
    opt_type=OptionType.CHANNEL,
    channel_types=[ChannelType.GUILD_TEXT],
    required=True,
)
@slash_option(
    name="review_channel",
    description="Channel you want moderators to review submissions in",
    opt_type=OptionType.CHANNEL,
    channel_types=[ChannelType.GUILD_TEXT],
    required=True,
)
@slash_option(
    name="info_channel",
    description="Channel you want the leaderboard to be displayed in",
    opt_type=OptionType.CHANNEL,
    channel_types=[ChannelType.GUILD_TEXT],
    required=True,
)
async def setup(
    ctx: SlashContext,
    currency: str,
    cooldown: int,
    submission_channel: BaseChannel,
    review_channel: BaseChannel,
    info_channel: BaseChannel,
):
    """Setup command setup have been received"""
    # Check input
    guild_error = tools.check_in_guild(ctx)
    if guild_error is not None:
        return await ctx.send(guild_error)
    if submission_channel.type != ChannelType.GUILD_TEXT:
        return await ctx.send(
            "submission_channel is not a text channel", ephemeral=True
        )
    if review_channel.type != ChannelType.GUILD_TEXT:
        return await ctx.send("review_channel is not a text channel", ephemeral=True)
    if info_channel.type != ChannelType.GUILD_TEXT:
        return await ctx.send("info_channel is not a text channel", ephemeral=True)
    # Setup in database
    dao.setup(
        ctx.guild.id,
        ctx.guild.name,
        currency,
        submission_channel.id,
        review_channel.id,
        info_channel.id,
        cooldown,
    )
    return await ctx.send("Setup complete. Enjoy!")


@slash_command(
    name="card",
    description="Show the guild card for the specified member",
    default_member_permissions=Permissions.USE_APPLICATION_COMMANDS,
)
@slash_option(
    name="member",
    description="Member to show the card of",
    opt_type=OptionType.USER,
    required=False,
)
async def card(ctx: SlashContext, member: Member = None):
    """Card command have been received"""
    # Check input
    guild_error = tools.check_in_guild(ctx)
    if guild_error is not None:
        return await ctx.send(guild_error)
    is_setup, db_guild = tools.check_guild_setup(ctx.guild.id)
    if not is_setup:
        return await ctx.send(
            db_guild
        )  # db_guild is a polymorph, either guild or error message
    if member is None:
        member = ctx.member
    db_member = dao.get_member(ctx.guild.id, member.id, member.display_name)
    # Business
    rank = dao.get_rank(ctx.guild.id, member.id)
    return await ctx.send(
        embed=tools.generate_guild_card_embed(db_member, db_guild, rank)
    )


@slash_command(
    name="request_register",
    description="Register a request and set its value",
    default_member_permissions=Permissions.ADMINISTRATOR,
)
@slash_option(
    name="request_type",
    description="Type of the request",
    opt_type=OptionType.STRING,
    required=True,
)
@slash_option(
    name="name",
    description="Name of the request",
    opt_type=OptionType.STRING,
    required=True,
)
@slash_option(
    name="effect",
    description="Effect of the request",
    opt_type=OptionType.STRING,
    required=True,
)
@slash_option(
    name="value",
    description="Reward for making the request",
    opt_type=OptionType.INTEGER,
    required=True,
)
async def request_register(
    ctx: SlashContext, request_type: str, name: str, effect: str, value: str
):
    """Request register command have been received"""
    request_type = request_type.lower()
    # Check input and fetch from database
    guild_error = tools.check_in_guild(ctx)
    if guild_error is not None:
        return await ctx.send(guild_error)
    is_setup, error = tools.check_guild_setup(ctx.guild.id)
    if not is_setup:
        return await ctx.send(error)

    try:
        dao.request_register(
            ctx.guild.id, request_type, name, effect, value
        )
    except Exception:
        return await ctx.send(f"Could not add {request_type} {name} with effect {effect}"
            " please check that it doesn't already exists") 
    return await ctx.send(
        f"{request_type.capitalize()} {name} with effect {effect} and value {value} added"
    )


@slash_command(
    name="request_delete",
    description="Delete a request",
    default_member_permissions=Permissions.ADMINISTRATOR,
)
@slash_option(
    name="request_type",
    description="Type of the request",
    opt_type=OptionType.STRING,
    required=True,
)
@slash_option(
    name="name",
    description="Name of the request",
    opt_type=OptionType.STRING,
    required=True,
)
@slash_option(
    name="effect",
    description="Effect of the request",
    opt_type=OptionType.STRING,
    required=True,
)
async def request_delete(ctx: SlashContext, request_type: str, name: str, effect: str):
    """Request delete command have been received"""
    request_type = request_type.lower()
    # Check input and fetch from database
    guild_error = tools.check_in_guild(ctx)
    if guild_error is not None:
        return await ctx.send(guild_error)
    is_setup, error = tools.check_guild_setup(ctx.guild.id)
    if not is_setup:
        return await ctx.send(error)
    # Business
    dao.request_delete(ctx.guild.id, request_type, name, effect)
    return await ctx.send(
        f"{request_type.capitalize()} {name} with effect {effect} removed"
    )


@slash_command(
    name="request_list",
    description="List all the requests",
    default_member_permissions=Permissions.USE_APPLICATION_COMMANDS,
)
@slash_option(
    name="request_type",
    description="Type of the request",
    opt_type=OptionType.STRING,
    required=True,
)
async def request_list(ctx: SlashContext, request_type: str):
    """Request list command have been received"""
    request_type = request_type.lower()
    # Check input and fetch from database
    guild_error = tools.check_in_guild(ctx)
    if guild_error is not None:
        return await ctx.send(guild_error)
    is_setup, error = tools.check_guild_setup(ctx.guild.id)
    if not is_setup:
        return await ctx.send(error)
    # Business
    db_requests = dao.get_requests(ctx.guild.id, request_type=request_type)
    return await ctx.send(content=tools.requests_content(db_requests))

@slash_command(
    name="points_add",
    description="Add points to a certain user",
    default_member_permissions=Permissions.MANAGE_GUILD,
)
@slash_option(
    name="member",
    description="Member whose point are going to be changed",
    opt_type=OptionType.USER,
    required=True,
)
@slash_option(
    name="points",
    description="Amount of points to award",
    opt_type=OptionType.INTEGER,
    required=True,
)
async def points_add(ctx:SlashContext, member: Member, points:int):
    """Command to add point to the member"""
    guild_error = tools.check_in_guild(ctx)
    if guild_error is not None:
        return await ctx.send(guild_error)
    is_setup, error = tools.check_guild_setup(ctx.guild.id)
    if not is_setup:
        return await ctx.send(error)
    dao.get_member(member.guild.id, member.id, member.display_name)
    dao.add_points(member.guild.id, member.id, points)
    return await ctx.send(f"Points added for {member.display_name}")

@slash_command(
    name="points_sub",
    description="Add points to a certain user",
    default_member_permissions=Permissions.MANAGE_GUILD,
)
@slash_option(
    name="member",
    description="Member whose point are going to be changed",
    opt_type=OptionType.USER,
    required=True,
)
@slash_option(
    name="points",
    description="Amount of points to take away",
    opt_type=OptionType.INTEGER,
    required=True,
)
async def points_sub(ctx:SlashContext, member: Member, points:int):
    """Command to subtract point to the member"""
    guild_error = tools.check_in_guild(ctx)
    if guild_error is not None:
        return await ctx.send(guild_error)
    is_setup, error = tools.check_guild_setup(ctx.guild.id)
    if not is_setup:
        return await ctx.send(error)
    dao.get_member(member.guild.id, member.id, member.display_name)
    dao.add_points(member.guild.id, member.id, -points)
    return await ctx.send(f"Points subtracted for {member.display_name}")

bot.start(TOKEN)
