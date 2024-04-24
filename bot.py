"""Main module for the Narga Chef discord bot"""

# Imports
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from interactions import (
    Client,
    Intents,
    listen,
    slash_command,
    slash_option,
    OptionType,
    SlashContext,
    Modal,
    ParagraphText,
    spread_to_rows,
    Embed,
    EmbedField,
    StringSelectMenu,
    Button,
    ButtonStyle,
    ActionRow,
    Permissions,
    Member,
    ChannelType,
    BaseChannel,
)
from interactions.api.events import MessageCreate, Component
import dao.dao

# Inititialization
load_dotenv()
TOKEN = os.environ.get("token")
PURPLE = "#7f03fc"
AQUAMARINE = "#00edd9"
ONE_HOUR = 3600
intents = Intents.MESSAGE_CONTENT | Intents.GUILD_MESSAGES | Intents.GUILDS
bot = Client(intents=intents)
eventDictionnary = {}


# Listeners
@listen()
async def on_message_create(ctx: MessageCreate):
    """When the discord bot sees a message"""
    image = get_first_image_attachement(ctx.message)
    if image is not None:
        return await image_received(ctx, image)


@listen(Component)
async def on_component(event: Component):
    """When a component is interacted with"""
    ctx = event.ctx
    event_type, req_member, unique, data1 = ctx.custom_id.split(",")
    match [event_type, req_member, unique, data1]:  # Read component event id
        # Name field has been set
        case ["type", *_]:
            request_type = ctx.values[0]
            return await type_component(
                ctx, request_type, event_type, req_member, unique
            )
        case ["name", *_]:
            name = ctx.values[0]
            return await name_component(ctx, name, event_type, req_member, unique)
        # Effect field has been set
        case ["effect", *_]:
            effect = ctx.values[0]
            return await effect_component(ctx, effect, req_member, unique)
        case ["accept", *_]:
            value = data1
            return await accept_component(ctx, req_member, unique, value)
        case ["deny", *_]:
            value = data1
            return await deny_component(ctx, req_member, unique, value)
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
    required=True,
)
@slash_option(
    name="review_channel",
    description="Channel you want moderators to review submissions in",
    opt_type=OptionType.CHANNEL,
    required=True,
)
@slash_option(
    name="info_channel",
    description="Channel you want the leaderboard to be displayed in",
    opt_type=OptionType.CHANNEL,
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
    guild_error = check_in_guild(ctx)
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
    guild_error = check_in_guild(ctx)
    if guild_error is not None:
        return await ctx.send(guild_error)
    is_setup, db_guild = check_guild_setup(ctx.guild.id)
    if not is_setup:
        return await ctx.send(
            db_guild
        )  # db_guild is a polymorph, either guild or error message
    if member is None:
        member = ctx.member
    db_member = dao.dao.get_member(ctx.guild.id, member.id, member.display_name)
    # Business
    rank = dao.dao.get_rank(ctx.guild.id, member.id)
    return await ctx.send(embed=generate_guild_card_embed(db_member, db_guild, rank))


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
    guild_error = check_in_guild(ctx)
    if guild_error is not None:
        return await ctx.send(guild_error)
    is_setup, error = check_guild_setup(ctx.guild.id)
    if not is_setup:
        return await ctx.send(error)
    dao.dao.request_register(
        ctx.guild.id, request_type.lower(), name.lower(), effect.lower(), value
    )
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
    guild_error = check_in_guild(ctx)
    if guild_error is not None:
        return await ctx.send(guild_error)
    is_setup, error = check_guild_setup(ctx.guild.id)
    if not is_setup:
        return await ctx.send(error)
    # Business
    dao.dao.request_delete(ctx.guild.id, request_type, name, effect)
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
    guild_error = check_in_guild(ctx)
    if guild_error is not None:
        return await ctx.send(guild_error)
    is_setup, error = check_guild_setup(ctx.guild.id)
    if not is_setup:
        return await ctx.send(error)
    # Business
    db_requests = dao.dao.requests(ctx.guild.id, request_type=request_type)
    return await ctx.send(content=requests_content(db_requests))


# Business
async def image_received(ctx, image):
    """A message with an image has been received"""
    guild = ctx.message.guild
    author = ctx.message.author
    is_setup, db_guild = check_guild_setup(guild.id)
    is_right_channel = ctx.message.channel.id == db_guild[dao.guilds.SUBMISSION_CHANNEL]
    # Check input and fetch from database
    guild_error = check_in_guild(ctx.message)
    if guild_error is not None or is_setup is False or is_right_channel is False:
        return  # Nothing to do
    # Make sure that the member exists and update its nickname in the database
    db_member = dao.dao.get_member(guild.id, author.id, author.display_name)
    if (
        db_member[dao.members.LAST_SUBMISION_TIME] != datetime.min
    ):  # The user submitted before
        timestamp_next_request = (
            db_member[dao.members.LAST_SUBMISION_TIME].timestamp()
            + float(db_guild[7]) * ONE_HOUR
        )
        if datetime.utcnow().timestamp() < timestamp_next_request:
            return await ctx.message.reply(
                f"""You will be able to submit your next request on:
 <t:{int(timestamp_next_request)}>"""
            )
    eventDictionnary[f"image,{author.id},{ctx.message.id}"] = image.url
    type_list = dao.dao.request_per_column(guild.id)["type"]
    if len(type_list) == 0:
        return await ctx.send("Please start by registering requests for this guild")
    return await ctx.message.reply(
        "Please tell us about your request",
        components=generate_request_component(
            type_list, author.id, ctx.message.id, name="Request Type", variation="type"
        ),
    )


async def type_component(ctx, request_type, event_type, req_member, unique):
    """A component indicating the type of request that have been received"""
    eventDictionnary[f"{event_type},{req_member},{unique}"] = request_type
    name_list = dao.dao.request_per_column(
        ctx.guild.id, request_type=request_type)["name"]
    if len(name_list) == 0:
        return await ctx.send(f"Could not find any {request_type}")
    return await ctx.edit_origin(
        content=f"Please tell us about your {request_type}",
        components=generate_request_component(
            name_list, req_member, unique, name="Request Name", variation="name"
        ),
    )


async def name_component(ctx, name, event_type, req_member, unique):
    """A component indicating the name of request that have been received"""
    request_type = eventDictionnary.get(f"type,{req_member},{unique}")
    eventDictionnary[f"{event_type},{req_member},{unique}"] = name
    effect_list = dao.dao.request_per_column(
        ctx.guild.id, request_type=request_type, name=name
    )["effect"]
    if len(effect_list) == 0:
        return await ctx.send(f"Could not find an effect for this {request_type}")
    return await ctx.edit_origin(
        content=f"Please tell us about your {request_type}",
        components=generate_request_component(
            effect_list, req_member, unique, name="Request Effect", variation="effect"
        ),
    )


async def effect_component(ctx, effect, req_member, unique):
    """A component indicating the effect of request that have been received"""
    image = eventDictionnary.get(f"image,{req_member},{unique}")
    request_type = eventDictionnary.get(f"type,{req_member},{unique}")
    if image is not None and request_type is not None:
        effect = ctx.values[0]
        name = eventDictionnary.get(f"name,{req_member},{unique}")
        return await send_to_review(ctx, image, request_type, name, effect, unique)
    else:
        return "Sorry, we lost track of your request... Please submit again"


async def accept_component(ctx, req_member, unique, value):
    """A component received when a user clicks the accept button"""
    image = eventDictionnary.get(f"image,{req_member},{unique}")
    request_type = eventDictionnary.get(f"type,{req_member},{unique}")
    name = eventDictionnary.get(f"name,{req_member},{unique}")
    effect = eventDictionnary.get(f"effect,{req_member},{unique}")
    # Update member
    dao.dao.add_points(ctx.guild.id, req_member, value)
    last_request = "I forgor 💀"
    if request_type is not None:
        last_request = f"{request_type.capitalize()} {name} {effect}"
    dao.dao.update_member_submission(ctx.guild.id, req_member, last_request)
    clear_events(unique, req_member)
    # Send messages
    await notify_member(ctx, req_member, unique, value, fulfilled=True)
    return await ctx.edit_origin(
        content=(f"{image}\nRequest accepted by <@{ctx.member.id}> and"
                 f" {value} points awarded to <@{req_member}>"),
        components=[],
    )


async def deny_component(ctx, req_member, unique, value):
    """A component received when a user clicks the deny button"""
    modal = get_denial_reason_modal()
    image = eventDictionnary.get(f"image,{req_member},{unique}")
    await ctx.send_modal(modal=modal)
    # Response received
    modal_ctx = await ctx.bot.wait_for_modal(modal)
    paragraph = modal_ctx.responses["reason"]
    dao.dao.add_points(ctx.guild.id, req_member, value)
    clear_events(unique, req_member)
    await notify_member(
        ctx, req_member, unique, value, reason=paragraph, fulfilled=False
    )
    await modal_ctx.send(content="Processing", ephemeral=True, delete_after=1.0)
    return await ctx.message.edit(
        content=(f"{image}\nRequest from <@{req_member}> denied by <@{ctx.member.id}>"
                f" for reason:\n{paragraph}"),
        components=[],
    )


async def send_to_review(ctx, image, request_type, name, effect, unique):
    """Send a request to be reviewed"""
    guild = ctx.guild.id
    db_request = dao.dao.get_request(guild, request_type, name, effect)
    db_guild = dao.dao.get_guild(guild)
    if len(db_guild) == 0:
        return "Please setup the guild again"
    if db_request is None or len(db_request) == 0:
        return (f"{request_type.capitalize()} {name} with effect {effect} doesn't exist."
                " Available requests might have changed")
    await send_review_message(ctx, image, db_guild, db_request, unique)
    return (f"You have submitted a {request_type}: {name} with effect {effect},"
             " review is in progress")


async def send_review_message(ctx, image, db_guild, db_request, unique):
    """Send the message in the review channel"""
    member = ctx.user.id
    channel = await ctx.guild.fetch_channel(db_guild[dao.guilds.REVIEW_CHANNEL])
    if channel is None:
        return await ctx.channel.send((f"Error, I cannot see channel"
            f"<#{db_guild[dao.guilds.REVIEW_CHANNEL]}>, check the setup and bot rights")
        )
    components = generate_review_component(
        member, unique, db_request[dao.requests.VALUE]
    )
    return await channel.send(
        f"{image}\n<@{member}> submitted"
        f" {db_request[dao.requests.REQUEST_TYPE]}"
        f" {db_request[dao.requests.REQUEST_NAME]} with effect"
        f" {db_request[dao.requests.EFFECT]} and value"
        f" {db_request[dao.requests.VALUE]}",
        components=components,
        attachements=image,
    )


async def notify_member(ctx, member, message, points, reason=None, fulfilled=False):
    """Notify a member of the result of their request"""
    db_guild = dao.dao.get_guild(ctx.guild.id)
    channel = await ctx.guild.fetch_channel(db_guild[dao.guilds.SUBMISSION_CHANNEL])
    message = await channel.fetch_message(message)
    if fulfilled:
        content = (f"Congratulations, your request have been accepted by <@{ctx.user.id}>"
            f" and you have been awarded {points} points")
    else:
        content = f"<@{ctx.user.id}> denied your request"
    if reason is not None:
        content = f"{content} here's why:\n{reason}"
    if message is None:  # The request message can't be fetched
        await channel.send(f"<@{member}> {content}")
    else:
        await message.reply(content)


# Utility
def clear_events(unique, member):
    """Delete the event from the event dictionnary"""
    try:
        del eventDictionnary[f"name,{unique},{member}"]
        del eventDictionnary[f"effect,{unique},{member}"]
        del eventDictionnary[f"image,{unique},{member}"]
    except KeyError:
        logging.info("Unable to delete event from the dictionnary")


def get_denial_reason_modal():
    """Returns a modal for reviewer to type a reason after a denial"""
    return Modal(
        ParagraphText(
            label="Reason for denial",
            custom_id="reason",
            placeholder="Help the member understand the reason of the denial",
            max_length=255,
        ),
        title="Bounty denial",
    )


def check_in_guild(context):
    """Check if we are in a guild"""
    if context.guild is None:
        return "This command isn't available outside of a guild"


def check_guild_setup(guild_id):
    """Check if the setup have been performed for this guild"""
    db_guild = dao.dao.get_guild(guild_id)
    if db_guild is None:
        return [False, "Please register this guild by using the /setup command"]
    return [True, db_guild]


def generate_guild_card_embed(db_member, db_guild, rank):
    """Generates the embed for a guild card"""
    points = EmbedField(
        name=db_guild[dao.guilds.CURRENCY],
        value=str(db_member[dao.members.POINTS]),
        inline=True,
    )
    rank = EmbedField(name="Rank", value=str(rank[2]), inline=True)
    if db_member[dao.members.LAST_SUBMISION_TIME] is datetime.min:
        timestamp_string = "No submission yet"
    else:
        timestamp_next_request = (
            db_member[dao.members.LAST_SUBMISION_TIME].timestamp()
            + float(db_guild[dao.guilds.COOLDOWN]) * ONE_HOUR
        )
        timestamp_string = f"<t:{int(timestamp_next_request)}>"
    cooldown = EmbedField(name="Cooldown", value=timestamp_string, inline=True)
    embed = Embed(
        color=PURPLE,
        title=f"Guild card for {db_member[dao.members.NICKNAME]}",
        fields=[points, rank, cooldown],
    )
    return embed


def requests_content(db_requests):
    """Format the requests in a string"""
    res = "```csv\nType; Name; Effect; Value\n"
    for request in db_requests:
        res = (f"{res}"
            f"{request[dao.requests.REQUEST_TYPE]};"
            f"{request[dao.requests.REQUEST_NAME]};"
            f"{request[dao.requests.EFFECT]};"
            f"{request[dao.requests.VALUE]}\n")
    return f"{res}```"


def get_first_image_attachement(message):
    """Gets the first image attached to a message"""
    for attachement in message.attachments:
        if attachement.content_type.startswith("image"):
            return attachement
    return None


def generate_request_component(
    options, member_id, message_id, name="Request name", variation="name"
):
    """Generates a selector for users to pick an option"""
    res: list[ActionRow] = spread_to_rows(  #TODO: check size limit
        StringSelectMenu(
            options,
            placeholder=name,
            min_values=1,
            max_values=1,
            custom_id=f"{variation},{member_id},{message_id},none",
        ),
    )
    logging.info(res)
    return res


def generate_review_component(member, unique, value):
    """Generate a component for the review message"""
    return [
        ActionRow(
            Button(
                style=ButtonStyle.RED,
                label="Deny",
                custom_id=f"deny,{member},{unique},{value}",
            ),
            Button(
                style=ButtonStyle.GREEN,
                label="Accept",
                custom_id=f"accept,{member},{unique},{value}",
            ),
        )
    ]


bot.start(TOKEN)
