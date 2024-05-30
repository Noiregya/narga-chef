"""Main module for the Narga Chef discord bot"""

# Imports
import os
import logging
from dotenv import load_dotenv
from interactions import (
    Client,
    Intents,
    listen,
    SlashCommandChoice,
    slash_command,
    slash_option,
    OptionType,
    SlashContext,
    Permissions,
    Member,
    Role,
    Attachment,
    ChannelType,
    BaseChannel,
    AutocompleteContext,
    global_autocomplete,
)
from interactions.api.events import MessageCreate, Component
from interactions.ext.paginators import Paginator
import dao
import business
import tools
import update
import auto_complete
import render.render as render


# Inititialization
logging.basicConfig()
logging.root.setLevel(logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()
TOKEN = os.environ.get("token")
intents = Intents.MESSAGE_CONTENT | Intents.GUILD_MESSAGES | Intents.GUILDS

IS_UPDATED = update.run_updates()
bot = Client(intents=intents, delete_unused_application_cmds=IS_UPDATED)


@slash_command(
    name="request_list",
    description="List all the requests",
    default_member_permissions=Permissions.USE_APPLICATION_COMMANDS,
)
@slash_option(
    name="request_type",
    description="Type of the request",
    opt_type=OptionType.STRING,
    autocomplete=True,
    required=True,
)
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
    request_str = business.list_requests(ctx.guild.id, request_type)
    paginator = Paginator.create_from_string(bot, request_str, page_size=1000)
    return await paginator.send(ctx)


@slash_command(
    name="complete_request",
    description="Complete a request for a user",
    default_member_permissions=Permissions.MANAGE_GUILD,
)
@slash_option(
    name="member",
    description="Member you want to complete the request for",
    opt_type=OptionType.USER,
    autocomplete=True,
    required=True,
)
@slash_option(
    name="request_type",
    description="Type of the request",
    opt_type=OptionType.STRING,
    autocomplete=True,
    required=True,
)
@slash_option(
    name="request_name",
    description="Name of the request",
    opt_type=OptionType.STRING,
    autocomplete=True,
    required=True,
)
@slash_option(
    name="request_effect",
    description="Effect of the request",
    opt_type=OptionType.STRING,
    autocomplete=True,
    required=True,
)
async def complete_request(
    ctx: SlashContext,
    member: Member,
    request_type: str,
    request_name: str,
    request_effect: str,
):
    """Complete request command have been received"""
    # Check input and fetch from database
    guild_error = tools.check_in_guild(ctx)
    if guild_error is not None:
        return await ctx.send(guild_error)
    is_setup, error = tools.check_guild_setup(ctx.guild.id)
    if not is_setup:
        return await ctx.send(error)
    return await ctx.send(
        business.award_request(
            ctx.guild.id,
            member.id,
            request_type=request_type,
            request_name=request_name,
            request_effect=request_effect,
        )
    )


@slash_command(
    name="request_completed",
    description="See what requests a user have completed",
    default_member_permissions=Permissions.MANAGE_GUILD,
)
@slash_option(
    name="member",
    description="Member you want to look at",
    opt_type=OptionType.USER,
    autocomplete=True,
    required=True,
)
async def request_completed(
    ctx: SlashContext,
    member: Member,
):
    """Request completed command have been received"""
    # Check input and fetch from database
    guild_error = tools.check_in_guild(ctx)
    if guild_error is not None:
        return await ctx.send(guild_error)
    is_setup, error = tools.check_guild_setup(ctx.guild.id)
    if not is_setup:
        return await ctx.send(error)
    # Business
    request_attr_str = business.list_request_completed(ctx.guild.id, member.id)
    paginator = Paginator.create_from_string(bot, request_attr_str, page_size=1000)
    return await paginator.send(ctx)


@slash_command(
    name="request_delete",
    description="Delete a request",
    default_member_permissions=Permissions.MANAGE_GUILD,
)
@slash_option(
    name="request_type",
    description="Type of the request",
    opt_type=OptionType.STRING,
    autocomplete=True,
    required=True,
)
@slash_option(
    name="request_name",
    description="Name of the request",
    opt_type=OptionType.STRING,
    autocomplete=True,
    required=True,
)
@slash_option(
    name="request_effect",
    description="Effect of the request",
    opt_type=OptionType.STRING,
    autocomplete=True,
    required=True,
)
async def request_delete(
    ctx: SlashContext, request_type: str, request_name: str, request_effect: str
):
    """Request delete command have been received"""
    # Check input and fetch from database
    guild_error = tools.check_in_guild(ctx)
    if guild_error is not None:
        return await ctx.send(guild_error)
    is_setup, error = tools.check_guild_setup(ctx.guild.id)
    if not is_setup:
        return await ctx.send(error)
    # Business
    dao.dao.request_delete(ctx.guild.id, request_type, request_name, request_effect)
    # Respond
    return await ctx.send(
        f"{request_type} {request_name} with effect {request_effect} removed"
    )


@listen()  # this decorator tells snek that it needs to listen for the corresponding event
async def on_ready():
    """This event is called when the bot is ready to respond to commands"""
    # pylint:disable=W0603
    logger.info("This bot is owned by %s", bot.owner)
    if IS_UPDATED:
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
        event_type, p1, p2, p3 = ctx.custom_id.split(",")
    except ValueError:  # Ignore this interaction
        return
    match [event_type, p1, p2, p3]:  # Read component event id
        # Name field has been set
        case ["type", *_]:
            req_member, unique = [p1, p2]
            request_type = ctx.values[0]
            return await business.type_component(
                ctx, request_type, event_type, req_member, unique
            )
        case ["name", *_]:
            req_member, unique = [p1, p2]
            name = ctx.values[0]
            return await business.name_component(
                ctx, name, event_type, req_member, unique
            )
        # Effect field has been set
        case ["effect", *_]:
            req_member, unique = [p1, p2]
            effect = ctx.values[0]
            return await business.effect_component(
                ctx, effect, event_type, req_member, unique
            )
        case ["accept", *_]:
            req_member, unique, value = [p1, p2, int(p3)]
            return await business.accept_component(ctx, req_member, unique, value)
        case ["deny", *_]:
            req_member, unique, value = [p1, p2, int(p3)]
            return await business.deny_component(ctx, req_member, unique, value)
        case ["buy", *_]:
            nature, ident, cost = [p1, p2, int(p3)]
            res = await business.buy_component(ctx, nature, ident, cost)
            return await ctx.send(content=res, ephemeral=True)
        case ["toggle", *_]:
            nature, reward_content = [p1, p2]
            res = await business.toggle_component(ctx, nature, reward_content)
            return await ctx.send(content=res, ephemeral=True)
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
    await ctx.defer()
    image = await business.get_card_image(
        db_member, db_guild, rank, pfp=member.display_avatar
    )
    res = await ctx.send(file=image)
    render.clear_cache(image)
    return res


@slash_command(
    name="leaderboard",
    description="Show the guild card for the specified member",
    default_member_permissions=Permissions.USE_APPLICATION_COMMANDS,
)
async def leaderboard(ctx: SlashContext):
    """Card command have been received"""
    # Check input
    guild_error = tools.check_in_guild(ctx)
    if guild_error is not None:
        return await ctx.send(guild_error)
    is_setup, db_guild = tools.check_guild_setup(ctx.guild.id)
    if not is_setup:
        return await ctx.send(db_guild)
    # Business
    db_leaderboard = dao.dao.get_leaderboard(ctx.guild.id)
    request_embeds = tools.generate_leaderboard(
        db_leaderboard, db_guild[dao.guilds.CURRENCY]
    )
    paginator = Paginator.create_from_embeds(bot, *request_embeds)
    return await paginator.send(ctx)


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
    autocomplete=True,
)
@slash_option(
    name="request_name",
    description="Name of the request",
    opt_type=OptionType.STRING,
    required=True,
    autocomplete=True,
)
@slash_option(
    name="request_effect",
    description="Effect of the request",
    opt_type=OptionType.STRING,
    required=True,
    autocomplete=True,
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
    await business.add_points_listener(ctx.guild, member.id, points)
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
    await business.add_points_listener(ctx.guild, member.id, -points)
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
@slash_option(
    name="condition",
    description="Condition for awarding reward",
    required=True,
    opt_type=OptionType.STRING,
    choices=[
        SlashCommandChoice(name="Bought", value="bought"),
        SlashCommandChoice(name="Milestone", value="milestone"),
    ],
)
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
async def reward_add(
    ctx: SlashContext, condition: str, reward: Role, points_required: int
):
    """Add a reward that users can get when gaining points"""
    # Planned to add rewards that are other than roles, as well as rewards that are "buyable" instead of milestones
    guild_error = tools.check_in_guild(ctx)
    if guild_error is not None:
        return await ctx.send(guild_error)
    is_setup, db_guild = tools.check_guild_setup(ctx.guild.id)
    if not is_setup:
        return await ctx.send(db_guild)
    return await business.add_reward(
        ctx,
        reward,
        points_required,
        condition=condition,
        currency=db_guild[dao.guilds.CURRENCY],
    )


@slash_command(
    name="reward_delete",
    description="Remove a reward",
    default_member_permissions=Permissions.MANAGE_GUILD,
)
@slash_option(
    name="condition",
    description="Condition for awarding reward",
    required=True,
    opt_type=OptionType.STRING,
    choices=[
        SlashCommandChoice(name="Bought", value="bought"),
        SlashCommandChoice(name="Milestone", value="milestone"),
    ],
)
@slash_option(
    name="reward",
    description="A role to award",
    required=True,
    opt_type=OptionType.ROLE,
)
async def reward_delete(ctx: SlashContext, condition: str, reward: Role):
    """Add a reward that users can get when gaining points"""
    # Planned to add rewards that are other than roles, as well as rewards that are "buyable" instead of milestones
    guild_error = tools.check_in_guild(ctx)
    if guild_error is not None:
        return await ctx.send(guild_error)
    is_setup, error = tools.check_guild_setup(ctx.guild.id)
    if not is_setup:
        return await ctx.send(error)
    return await business.remove_reward(
        ctx, reward, condition=condition
    )  # TODO: Respond here instead of in business


@slash_command(
    name="reward_list",
    description="View all the rewards in the guild",
    default_member_permissions=Permissions.USE_APPLICATION_COMMANDS,
)
async def reward_list(ctx: SlashContext):
    """Respond with a list of all the rewards currently in the guild"""
    guild_error = tools.check_in_guild(ctx)
    if guild_error is not None:
        return await ctx.send(guild_error)
    is_setup, error = tools.check_guild_setup(ctx.guild.id)
    if not is_setup:
        return await ctx.send(error)
    rewards_str = business.list_rewards(ctx.guild.id)
    paginator = Paginator.create_from_string(bot, rewards_str, page_size=1000)
    return await paginator.send(ctx)

@slash_command(
    name="achievement_add",
    description="Add an achievement",
    default_member_permissions=Permissions.MANAGE_GUILD,
)
@slash_option(
    name="name",
    description="Name for the achievement",
    required=True,
    opt_type=OptionType.STRING,
)
@slash_option(
    name="image",
    description="Icon for the achievement (48x48px)",
    required=True,
    opt_type=OptionType.ATTACHMENT,
)
@slash_option(
    name="condition",
    description="JSON condition for awarding achievement",
    required=True,
    opt_type=OptionType.STRING,
)
async def achievement_add(
    ctx: SlashContext, name: str, image: Attachment, condition: str
):
    """Add an achievement"""
    guild_error = tools.check_in_guild(ctx)
    if guild_error is not None:
        return await ctx.send(guild_error)
    is_setup, db_guild = tools.check_guild_setup(ctx.guild.id)
    if not is_setup:
        return await ctx.send(db_guild)
    return await ctx.send(business.add_achievement(ctx.guild.id, name, image, condition),
        ephemeral=True)


@slash_command(
    name="achievement_list",
    description="View all the achievements in the guild",
    default_member_permissions=Permissions.USE_APPLICATION_COMMANDS,
)
async def achievement_list(ctx: SlashContext):
    """Respond with a list of all the achievements currently in the guild"""
    guild_error = tools.check_in_guild(ctx)
    if guild_error is not None:
        return await ctx.send(guild_error)
    is_setup, error = tools.check_guild_setup(ctx.guild.id)
    if not is_setup:
        return await ctx.send(error)
    achievements_str = business.list_achievements(ctx.guild.id)
    paginator = Paginator.create_from_string(bot, achievements_str, page_size=1000)
    return await paginator.send(ctx)


@slash_command(
    name="shop",
    description="Generates a shop in the current channel with all the rewards",
    default_member_permissions=Permissions.MANAGE_GUILD,
)
async def generate_shop(ctx: SlashContext):
    """Generates a shop in the current channel with all the rewards"""
    guild_error = tools.check_in_guild(ctx)
    if guild_error is not None:
        return await ctx.send(guild_error)
    is_setup, db_guild = tools.check_guild_setup(ctx.guild.id)
    if not is_setup:
        return await ctx.send(db_guild)

    roles = ctx.guild.roles
    res = business.generate_shop(db_guild, roles)
    channel = ctx.channel
    await ctx.defer(ephemeral=True)
    for kvp in res.items():
        messages = kvp[1]
        for message in messages:
            await channel.send(
                content=message["content"], components=message["components"]
            )
    return await ctx.send(content="Shop have been generated")


@global_autocomplete("request_type")
async def autocomplete_request_type(ctx: AutocompleteContext):
    """Autocompletes for all the types in the guild"""
    if ctx.guild is None:
        return await ctx.send([])
    string_option_input = ctx.input_text  # can be empty/None
    options = auto_complete.get_cache_request_options(ctx.guild.id)
    return await ctx.send(
        choices=auto_complete.autocomplete_from_options(options, string_option_input)
    )


@global_autocomplete("request_name")
async def autocomplete_request_name(ctx: AutocompleteContext):
    """Autocompletes for all the names in the guild"""
    if ctx.guild is None:
        return await ctx.send([])
    string_option_input = ctx.input_text  # can be empty/None
    request_type = ctx.kwargs.get("request_type")
    options = auto_complete.get_cache_request_options(
        ctx.guild.id, request_type=request_type
    )
    return await ctx.send(
        choices=auto_complete.autocomplete_from_options(options, string_option_input)
    )


@global_autocomplete("request_effect")
async def autocomplete_request_effect(ctx: AutocompleteContext):
    """Autocompletes for all the effects in the guild"""
    if ctx.guild is None:
        return await ctx.send([])
    string_option_input = ctx.input_text  # can be empty/None
    request_type = ctx.kwargs.get("request_type")
    request_name = ctx.kwargs.get("request_name")
    options = auto_complete.get_cache_request_options(
        ctx.guild.id, request_type=request_type, name=request_name
    )
    return await ctx.send(
        choices=auto_complete.autocomplete_from_options(options, string_option_input)
    )


bot.start(TOKEN)
