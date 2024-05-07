"""Main module for the Narga Chef discord bot"""

# Imports
import os
import logging
import time
from dotenv import load_dotenv
from interactions import (
    Client,
    Intents,
    listen,
    SlashCommand,
    SlashCommandOption,
    SlashCommandChoice,
    slash_command,
    slash_option,
    OptionType,
    SlashContext,
    Permissions,
    Member,
    Role,
    ChannelType,
    BaseChannel,
)
from interactions.api.events import MessageCreate, Component
from interactions.ext.paginators import Paginator
import dao
import business
import tools
import update

# Inititialization
logging.basicConfig()
logging.root.setLevel(logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()
TOKEN = os.environ.get("token")
intents = Intents.MESSAGE_CONTENT | Intents.GUILD_MESSAGES | Intents.GUILDS

IS_UPDATED = update.run_updates()
bot = Client(intents=intents, delete_unused_application_cmds=IS_UPDATED)


# Per guild requests, registered manually see guild_commands
def generate_request_list_cmd(guild_id, types_choices):
    """request_list command depending on the available request types"""
    request_list_cmd = SlashCommand(
        name="request_list",
        description="List all the requests",
        scopes=[str(guild_id)],
        default_member_permissions=Permissions.USE_APPLICATION_COMMANDS,
        options=[
            SlashCommandOption(
                name="request_type",
                description="Type of the request",
                type=OptionType.STRING,
                required=True,
                choices=types_choices,
            )
        ],
        callback=request_list,
    )
    return request_list_cmd


async def request_list(ctx: SlashContext, request_type: str):
    """Request list command have been received"""
    # Check input and fetch from database
    guild_error = tools.check_in_guild(ctx)
    if guild_error is not None:
        return await ctx.send(guild_error)
    is_setup, error = tools.check_guild_setup(ctx.guild.id)
    if not is_setup:
        return await ctx.send(error)
    # Business
    request_embeds = tools.requests_content(ctx.guild.id, request_type)
    paginator = Paginator.create_from_embeds(bot, *request_embeds)
    return await paginator.send(ctx)


def generate_request_delete_cmd(guild_id, types_choices):
    """request_delete command depending on the available request types"""
    request_delete_cmd = SlashCommand(
        name="request_delete",
        description="Delete a request",
        scopes=[str(guild_id)],
        default_member_permissions=Permissions.MANAGE_GUILD,
        options=[
            SlashCommandOption(
                name="request_type",
                description="Type of the request",
                type=OptionType.STRING,
                required=True,
                choices=types_choices,
            ),
            SlashCommandOption(
                name="name",
                description="Name of the request",
                type=OptionType.STRING,
                required=True,
            ),
            SlashCommandOption(
                name="effect",
                description="Effect of the request",
                type=OptionType.STRING,
                required=True,
            ),
        ],
        callback=request_delete,
    )
    return request_delete_cmd


async def request_delete(ctx: SlashContext, request_type: str, name: str, effect: str):
    """Request delete command have been received"""
    # Check input and fetch from database
    guild_error = tools.check_in_guild(ctx)
    if guild_error is not None:
        return await ctx.send(guild_error)
    is_setup, error = tools.check_guild_setup(ctx.guild.id)
    if not is_setup:
        return await ctx.send(error)
    # Business
    dao.dao.request_delete(ctx.guild.id, request_type, name, effect)
    # Respond
    return await ctx.send(f"{request_type} {name} with effect {effect} removed")


def get_guild_commands(guilds):
    """Get all the guild commands to be registered in the guild scope"""
    scopes = []
    commands = []
    for guild in guilds:
        db_types = [
            req[dao.requests.REQUEST_TYPE] for req in dao.dao.get_requests(guild)
        ]
        db_types = list(dict.fromkeys(db_types))
        types_choices = list(
            SlashCommandChoice(name=element, value=element) for element in db_types
        )
        if len(types_choices) > 0:
            scope = guild
            commands.append(generate_request_list_cmd(scope, types_choices))
            commands.append(generate_request_delete_cmd(scope, types_choices))
            scopes.append(scope)
    return [scopes, commands]


async def register_guild_commands(guilds):
    """Register all the guild commands to discord"""
    scopes, commands = get_guild_commands(guilds)
    for command in commands:
        bot.add_interaction(command)
    await bot.synchronise_interactions(scopes=scopes)


@listen()  # this decorator tells snek that it needs to listen for the corresponding event
async def on_ready():
    """This event is called when the bot is ready to respond to commands"""
    # pylint:disable=W0603
    logger.info("This bot is owned by %s", bot.owner)
    if IS_UPDATED:
        # Register all the guild specific commands
        guild_ids = [guild.id for guild in bot.guilds]
        await register_guild_commands(guild_ids)
        logger.info("Update finished")
    else:
        logger.info("Bot up to date")


@listen()
async def on_message_create(ctx: MessageCreate):
    """When the discord bot sees a message"""
    images = tools.get_image_attachements(ctx.message)
    if len(images) > 0:
        return await business.image_received(ctx, images)


@listen(Component)
async def on_component(event: Component):
    """When a component is interacted with"""
    ctx = event.ctx
    try:
        event_type, req_member, unique, data1 = ctx.custom_id.split(",")
    except ValueError:  # Ignore this interaction
        return
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
            value = int(data1)
            return await business.accept_component(ctx, req_member, unique, value)
        case ["deny", *_]:
            value = int(data1)
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
    dao.dao.setup(
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
    db_member = dao.dao.fetch_member(ctx.guild.id, member.id, member.display_name)
    # Business
    rank = dao.dao.get_rank(ctx.guild.id, member.id)
    return await ctx.send(
        embed=tools.generate_guild_card_embed(db_member, db_guild, rank)
    )


@slash_command(
    name="cooldown_reset",
    description="Reset a member's cooldown",
    default_member_permissions=Permissions.MANAGE_GUILD,
)
@slash_option(
    name="member",
    description="Member to reset the cooldown of",
    opt_type=OptionType.USER,
    required=True,
)
async def cooldown_reset(ctx: SlashContext, member: Member = None):
    """Cooldown_reset command have been received"""
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
    dao.dao.cooldown_reset(ctx.guild.id, member.id)
    return await ctx.send(f"Request cooldown for <@{member.id}> have been reset.")


@slash_command(
    name="request_add",
    description="Register a request and set its value",
    default_member_permissions=Permissions.MANAGE_GUILD,
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
async def request_add(
    ctx: SlashContext, request_type: str, name: str, effect: str, value: str
):
    """Request register command have been received"""
    # Check input and fetch from database
    guild_error = tools.check_in_guild(ctx)
    if guild_error is not None:
        return await ctx.send(guild_error)
    is_setup, error = tools.check_guild_setup(ctx.guild.id)
    if not is_setup:
        return await ctx.send(error)
    # Update DB
    res = business.add_request(ctx, request_type, name, effect, value)
    # Respond
    return await ctx.send(res)


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
async def points_add(ctx: SlashContext, member: Member, points: int):
    """Command to add point to the member"""
    guild_error = tools.check_in_guild(ctx)
    if guild_error is not None:
        return await ctx.send(guild_error)
    is_setup, error = tools.check_guild_setup(ctx.guild.id)
    if not is_setup:
        return await ctx.send(error)
    await business.add_points_listener(ctx.guild, member.id, points, member=member)
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
async def points_sub(ctx: SlashContext, member: Member, points: int):
    """Command to subtract point to the member"""
    guild_error = tools.check_in_guild(ctx)
    if guild_error is not None:
        return await ctx.send(guild_error)
    is_setup, error = tools.check_guild_setup(ctx.guild.id)
    if not is_setup:
        return await ctx.send(error)
    await business.add_points_listener(ctx.guild, member.id, -points, member=member)
    return await ctx.send(f"Points subtracted for {member.display_name}")


@slash_command(
    name="reward_add",
    description="Add a reward that users can get when gaining points",
    default_member_permissions=Permissions.MANAGE_GUILD,
)
# @slash_option(
#    name="reward_type",
#    description="Type of the reward to award users",
#    required=True,
# )
# @slash_option(
#    name="condition",
#    description="Condition for awarding reward",
#    required=True,
#    opt_type=OptionType.STRING,
# )
@slash_option(
    name="reward",
    description="A role to award",
    required=True,
    opt_type=OptionType.ROLE,
)
@slash_option(
    name="points_required",
    description="Amount of points required",
    required=True,
    opt_type=OptionType.INTEGER,
)
async def reward_add(ctx: SlashContext, reward: Role, points_required: int):
    """Add a reward that users can get when gaining points"""
    # Planned to add rewards that are other than roles, as well as rewards that are "buyable" instead of milestones
    guild_error = tools.check_in_guild(ctx)
    if guild_error is not None:
        return await ctx.send(guild_error)
    is_setup, error = tools.check_guild_setup(ctx.guild.id)
    if not is_setup:
        return await ctx.send(error)
    return await business.add_reward(ctx, reward, points_required)


@slash_command(
    name="reward_delete",
    description="Remove a reward",
    default_member_permissions=Permissions.MANAGE_GUILD,
)
@slash_option(
    name="reward",
    description="A role to award",
    required=True,
    opt_type=OptionType.ROLE,
)
async def reward_delete(ctx: SlashContext, reward: Role):
    """Add a reward that users can get when gaining points"""
    # Planned to add rewards that are other than roles, as well as rewards that are "buyable" instead of milestones
    guild_error = tools.check_in_guild(ctx)
    if guild_error is not None:
        return await ctx.send(guild_error)
    is_setup, error = tools.check_guild_setup(ctx.guild.id)
    if not is_setup:
        return await ctx.send(error)
    return await business.remove_reward(ctx, reward)


bot.start(TOKEN)
