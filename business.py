"""Functions making up the most of the bot's algorithm"""

import logging
from datetime import datetime
import dao.dao as dao
import dao.members as members
import dao.guilds as guilds
import dao.requests as requests
import tools

ONE_HOUR = 3600

eventDictionnary = {}


# Business
async def image_received(ctx, image):
    """A message with an image has been received"""
    guild = ctx.message.guild
    author = ctx.message.author
    is_setup, db_guild = tools.check_guild_setup(guild.id)
    is_right_channel = ctx.message.channel.id == db_guild[guilds.SUBMISSION_CHANNEL]
    # Check input and fetch from database
    guild_error = tools.check_in_guild(ctx.message)
    if guild_error is not None or is_setup is False or is_right_channel is False:
        return  # Nothing to do
    # Make sure that the member exists and update its nickname in the database
    db_member = dao.get_member(guild.id, author.id, author.display_name)
    if (
        db_member[members.LAST_SUBMISION_TIME] != datetime.min
    ):  # The user submitted before
        timestamp_next_request = (
            db_member[members.LAST_SUBMISION_TIME].timestamp()
            + float(db_guild[7]) * ONE_HOUR
        )
        if datetime.utcnow().timestamp() < timestamp_next_request:
            return await ctx.message.reply(
                "You will be able to submit your next request on:"
                f"<t:{int(timestamp_next_request)}>"
            )
    eventDictionnary[f"image,{author.id},{ctx.message.id}"] = image.url
    type_list = dao.request_per_column(guild.id)["type"]
    if len(type_list) == 0:
        return await ctx.send("Please start by registering requests for this guild")
    return await ctx.message.reply(
        "Please tell us about your request",
        components=tools.generate_request_component(
            type_list, author.id, ctx.message.id, name="Request Type", variation="type"
        ),
    )


async def type_component(ctx, request_type, event_type, req_member, unique):
    """A component indicating the type of request that have been received"""
    eventDictionnary[f"{event_type},{req_member},{unique}"] = request_type
    name_list = dao.request_per_column(ctx.guild.id, request_type=request_type)["name"]
    if len(name_list) == 0:
        return await ctx.send(f"Could not find any {request_type}")
    return await ctx.edit_origin(
        content=f"Please tell us about your {request_type}",
        components=tools.generate_request_component(
            name_list, req_member, unique, name="Request Name", variation="name"
        ),
    )


async def name_component(ctx, name, event_type, req_member, unique):
    """A component indicating the name of request that have been received"""
    request_type = eventDictionnary.get(f"type,{req_member},{unique}")
    eventDictionnary[f"{event_type},{req_member},{unique}"] = name
    effect_list = dao.request_per_column(
        ctx.guild.id, request_type=request_type, name=name
    )["effect"]
    if len(effect_list) == 0:
        return await ctx.send(f"Could not find an effect for this {request_type}")
    return await ctx.edit_origin(
        content=f"Please tell us about your {request_type}",
        components=tools.generate_request_component(
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
    dao.add_points(ctx.guild.id, req_member, value)
    last_request = "I forgor 💀"
    if request_type is not None:
        last_request = f"{request_type.capitalize()} {name} {effect}"
    dao.update_member_submission(ctx.guild.id, req_member, last_request)
    clear_events(unique, req_member)
    # Send messages
    await notify_member(ctx, req_member, unique, value, fulfilled=True)
    return await ctx.edit_origin(
        content=(
            f"{image}\nRequest accepted by <@{ctx.member.id}> and"
            f" {value} points awarded to <@{req_member}>"
        ),
        components=[],
    )


async def deny_component(ctx, req_member, unique, value):
    """A component received when a user clicks the deny button"""
    modal = tools.get_denial_reason_modal()
    image = eventDictionnary.get(f"image,{req_member},{unique}")
    await ctx.send_modal(modal=modal)
    # Response received
    modal_ctx = await ctx.bot.wait_for_modal(modal)
    paragraph = modal_ctx.responses["reason"]
    dao.add_points(ctx.guild.id, req_member, value)
    clear_events(unique, req_member)
    await notify_member(
        ctx, req_member, unique, value, reason=paragraph, fulfilled=False
    )
    await modal_ctx.send(content="Processing", ephemeral=True, delete_after=1.0)
    return await ctx.message.edit(
        content=(
            f"{image}\nRequest from <@{req_member}> denied by <@{ctx.member.id}>"
            f" for reason:\n{paragraph}"
        ),
        components=[],
    )


async def send_to_review(ctx, image, request_type, name, effect, unique):
    """Send a request to be reviewed"""
    guild = ctx.guild.id
    db_request = dao.get_request(guild, request_type, name, effect)
    db_guild = dao.get_guild(guild)
    if len(db_guild) == 0:
        return "Please setup the guild again"
    if db_request is None or len(db_request) == 0:
        return (
            f"{request_type.capitalize()} {name} with effect {effect} doesn't exist."
            " Available requests might have changed"
        )
    await send_review_message(ctx, image, db_guild, db_request, unique)
    return (
        f"You have submitted a {request_type}: {name} with effect {effect},"
        " review is in progress"
    )


async def send_review_message(ctx, image, db_guild, db_request, unique):
    """Send the message in the review channel"""
    member = ctx.user.id
    channel = await ctx.guild.fetch_channel(db_guild[guilds.REVIEW_CHANNEL])
    if channel is None:
        return await ctx.channel.send(
            (
                f"Error, I cannot see channel"
                f"<#{db_guild[guilds.REVIEW_CHANNEL]}>, check the setup and bot rights"
            )
        )
    components = tools.generate_review_component(
        member, unique, db_request[requests.VALUE]
    )
    return await channel.send(
        f"{image}\n<@{member}> submitted"
        f" {db_request[requests.REQUEST_TYPE]}"
        f" {db_request[requests.REQUEST_NAME]} with effect"
        f" {db_request[requests.EFFECT]} and value"
        f" {db_request[requests.VALUE]}",
        components=components,
        attachements=image,
    )


async def notify_member(ctx, member, message, points, reason=None, fulfilled=False):
    """Notify a member of the result of their request"""
    db_guild = dao.get_guild(ctx.guild.id)
    channel = await ctx.guild.fetch_channel(db_guild[guilds.SUBMISSION_CHANNEL])
    message = await channel.fetch_message(message)
    if fulfilled:
        content = (
            f"Congratulations, your request have been accepted by <@{ctx.user.id}>"
            f" and you have been awarded {points} points"
        )
    else:
        content = f"<@{ctx.user.id}> denied your request"
    if reason is not None:
        content = f"{content} here's why:\n{reason}"
    if message is None:  # The request message can't be fetched
        await channel.send(f"<@{member}> {content}")
    else:
        await message.reply(content)


def clear_events(unique, member):
    """Delete the event from the event dictionnary"""
    try:
        del eventDictionnary[f"name,{unique},{member}"]
        del eventDictionnary[f"effect,{unique},{member}"]
        del eventDictionnary[f"image,{unique},{member}"]
    except KeyError:
        logging.info("Unable to delete event from the dictionnary")
