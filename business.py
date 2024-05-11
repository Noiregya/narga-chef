"""Functions making up the most of the bot's algorithm"""

import logging
from datetime import datetime
import psycopg
from interactions.client.errors import (BotException)
import dao.dao as dao
import dao.members as members
import dao.guilds as guilds
import dao.requests as requests
import dao.rewards as rewards
import tools

MAX_OPTIONS = 25

eventDictionnary = {}


# Business
async def image_received(ctx, images):
    """A message with an image has been received"""
    guild = ctx.message.guild
    author = ctx.message.author
    user_ids = [author.id]
    async for user in ctx.message.mention_users:
        if user.id is not author.id:
            user_ids.append(user.id)
    is_setup, db_guild = tools.check_guild_setup(guild.id)
    is_right_channel = ctx.message.channel.id == db_guild[guilds.SUBMISSION_CHANNEL]
    # Check input and fetch from database
    guild_error = tools.check_in_guild(ctx.message)
    if guild_error is not None or is_setup is False or is_right_channel is False:
        return  # Nothing to do
    # Make sure that the member exists and update its nickname in the database
    db_member = dao.fetch_member(guild.id, author.id, author.display_name)
    if (
        db_member[members.NEXT_SUBMISSION_TIME].year != datetime.min.year
    ):  # The user submitted before
        timestamp_next_request = db_member[members.NEXT_SUBMISSION_TIME].timestamp()
        if datetime.now().timestamp() < timestamp_next_request:
            return await ctx.message.reply(
                "You will be able to submit your next request on:"
                f"<t:{int(timestamp_next_request)}>"
            )
    image_string = ";".join(images)
    eventDictionnary[f"image,{author.id},{ctx.message.id}"] = image_string
    eventDictionnary[f"users,{author.id},{ctx.message.id}"] = user_ids
    type_list = tools.request_per_column(guild.id)["type"]
    type_list = list(dict.fromkeys(type_list))# Remove doubles
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
    name_list = tools.request_per_column(ctx.guild.id, request_type=request_type)[
        "name"
    ]
    name_list = list(dict.fromkeys(name_list))# Remove doubles
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
    effect_list = tools.request_per_column(
        ctx.guild.id, request_type=request_type, name=name
    )["effect"]
    effect_list = list(dict.fromkeys(effect_list))# Remove doubles
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
    image_string = eventDictionnary.get(f"image,{req_member},{unique}")
    request_type = eventDictionnary.get(f"type,{req_member},{unique}")
    if image_string is not None and request_type is not None:
        name = eventDictionnary.get(f"name,{req_member},{unique}")
        images = image_string.split(";")
        content = await send_to_review(ctx, images, request_type, name, effect, unique)
        return await ctx.edit_origin(
            content=content,
            components=[],
        )
    else:
        return "Sorry, we lost track of your request... Please submit again"


async def accept_component(ctx, req_member, unique, value):
    """A component received when a user clicks the accept button"""
    image_string = eventDictionnary.get(f"image,{req_member},{unique}")
    if image_string is None:
        return await ctx.edit_origin(
            content=(
                f"This request expired, please ask <@{req_member}> to submit it again"
            ),
            components=[],
        )
    image_string = image_string.replace(";", "\n")
    request_type = eventDictionnary.get(f"type,{req_member},{unique}")
    name = eventDictionnary.get(f"name,{req_member},{unique}")
    effect = eventDictionnary.get(f"effect,{req_member},{unique}")
    users = eventDictionnary.get(f"users,{req_member},{unique}")
    last_request = "I forgor 💀"
    if request_type is not None:
        last_request = f"{request_type} {name} {effect}"
    # Update member
    member_pings = ""
    for user in users:
        await add_points_listener(ctx.guild, user, value)
        dao.update_member_submission(
            ctx.guild.id, user, last_request
        )
        # Send messages
        member_pings = member_pings + f"<@{user}> "
    await notify_member(ctx, member_pings, unique, value, fulfilled=True)
    clear_events(unique, req_member)
    return await ctx.edit_origin(
        content=(
            f"Request accepted by <@{ctx.member.id}> and"
            f" {value} points awarded to {member_pings}\n{image_string}"
        ),
        components=[],
    )


async def deny_component(ctx, req_member, unique, value):
    """A component received when a user clicks the deny button"""
    guild = ctx.guild.id
    member = ctx.member.id
    db_member = dao.get_member(guild, member)
    db_guild = dao.get_guild(guild)
    modal = tools.get_denial_reason_modal()
    image_string = eventDictionnary.get(f"image,{req_member},{unique}")
    await ctx.send_modal(modal=modal)
    if image_string is None:
        return await ctx.edit_origin(
            content=(
                f"This request expired, please ask <@{req_member}> to submit it again"
            ),
            components=[],
        )
    image_string = image_string.replace(";", "\n")
    # Response received
    modal_ctx = await ctx.bot.wait_for_modal(modal)
    paragraph = modal_ctx.responses["reason"]
    next_submission_time = tools.calculate_prev_submission_time(
        db_member[members.NEXT_SUBMISSION_TIME], db_guild[guilds.COOLDOWN]
    )
    dao.update_cooldown(guild, member, next_submission_time)
    clear_events(unique, req_member)
    await notify_member(
        ctx, f"<@{req_member}>", unique, value, reason=paragraph, fulfilled=False
    )
    await modal_ctx.send(content="Processing", ephemeral=True, delete_after=1.0)
    return await ctx.message.edit(
        content=(
            f"Request from <@{req_member}> denied by <@{ctx.member.id}>"
            f" for reason:\n{paragraph}\n{image_string}"
        ),
        components=[],
    )


async def buy_component(ctx, nature, reward_content, cost):
    """A component received when a member tries to buy a reward"""
    db_member = dao.get_member(ctx.guild.id, ctx.author.id)
    balance = db_member[members.POINTS] - db_member[members.SPENT]
    if balance >= cost:
        content, error = await award(ctx, nature, reward_content)
        if error:
            return content
        dao.add_spent(ctx.guild.id, ctx.author.id, cost)
    else:
        content = f"Not enough funds, cost: {cost} balance: {balance}"
    return content

async def toggle_component(ctx, nature, reward_content):
    """A component received when a member tries to toggle a reward"""
    if nature == "role":
        content = await toggle_role_reward(ctx, reward_content)
    if content is None:
        content = f"Could not toggle {nature}"
    return content


async def send_to_review(ctx, images, request_type, name, effect, unique):
    """Send a request to be reviewed"""
    guild = ctx.guild.id
    member = ctx.author.id
    db_member = dao.get_member(guild, member)
    db_guild = dao.get_guild(guild)
    next_submission_time = tools.calculate_next_submission_time(
        db_member[members.NEXT_SUBMISSION_TIME], db_guild[guilds.COOLDOWN]
    )
    dao.update_cooldown(guild, member, next_submission_time)
    db_request = dao.get_request(guild, request_type, name, effect)
    if len(db_guild) == 0:
        return "Please setup the guild again"
    if db_request is None or len(db_request) == 0:
        return (
            f"{request_type} {name} with effect {effect} doesn't exist."
            " Available requests might have changed"
        )
    await send_review_message(ctx, images, db_guild, db_request, unique)
    return (
        f"You have submitted a {request_type}: {name} with effect {effect},"
        " review is in progress"
    )


async def send_review_message(ctx, images, db_guild, db_request, unique):
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
    images = "\n".join(images)
    return await channel.send(
        f"<@{member}> submitted"
        f" {db_request[requests.REQUEST_TYPE]}"
        f" {db_request[requests.REQUEST_NAME]} with effect"
        f" {db_request[requests.EFFECT]} and value"
        f" {db_request[requests.VALUE]}\n" + images,
        components=components,
    )


async def notify_member(
    ctx, member_pings, message, points, reason=None, fulfilled=False
):
    """Notify members of the result of their request"""
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
    return await message.reply(f"{member_pings}{content}")


def clear_events(unique, member):
    """Delete the event from the event dictionnary"""
    try:
        del eventDictionnary[f"name,{unique},{member}"]
        del eventDictionnary[f"effect,{unique},{member}"]
        del eventDictionnary[f"image,{unique},{member}"]
    except KeyError:
        logging.info("Unable to delete event from the dictionnary")


def add_request(ctx, req_type, name, effect, value):
    """Add a new request to the database"""
    req = tools.ordered_requests(ctx.guild.id)
    if req is not None:
        if len(req) >= MAX_OPTIONS:
            return (
                "Could not add the request, there can only be a maximum of"
                f" {MAX_OPTIONS} types"
            )
        gotten_type = req.get(req_type)
        if gotten_type is not None:
            if len(gotten_type) >= MAX_OPTIONS:
                return (
                    f"Could not add the request, there can only be a maximum of"
                    f" {MAX_OPTIONS} names in {req_type}"
                )
            gotten_effect = req.get(req_type).get(name)
            if gotten_effect is not None and len(gotten_effect) >= MAX_OPTIONS:
                return (
                    f"Could not add the request, there can only be a maximum of"
                    f" {MAX_OPTIONS} effects for {name}"
                )
    try:
        dao.request_register(ctx.guild.id, req_type, name, effect, value)
    except psycopg.Error as e:
        logging.error(e)
        return (
            f"Could not add {req_type} {name} with effect {effect}"
            " please check that it doesn't already exists"
        )
    return (
        f"{req_type} {name} with effect {effect} and value {value} added"
    )


async def add_reward(
    ctx, reward, points_required, condition="milestone", nature="role"
):
    """Adds a new reward"""
    reward_string = f"<@&{reward.id}>"
    try:
        dao.insert_reward(ctx.guild.id, condition, nature, reward.id, points_required)
    except psycopg.Error as e:
        logging.error(e)
        return await ctx.send(
            f"Could not add {nature} {reward.name} obtained through {condition}"
            " please check that it doesn't already exists"
        )
    return await ctx.send(
        f"{nature} {reward_string} obtained through {condition} with {points_required}"
        " points added",
        ephemeral=True,
    )
    #  ctx.user.add_role(reward, "Milestone reward")


async def remove_reward(ctx, reward, condition="milestone", nature="role"):
    """Removes a reward"""
    reward_string = f"<@&{reward.id}>"
    try:
        dao.delete_reward(ctx.guild.id, condition, nature, reward.id)
    except psycopg.Error as e:
        logging.error(e)
        return await ctx.send(f"Could not delete this reward. {e}")
    return await ctx.send(
        f"{nature} {reward_string} obtained through {condition} removed", ephemeral=True
    )

async def update_rewards(guild_id, member, current_points):
    """Update the rewards a member deserves"""
    db_rewards = dao.get_rewards(guild_id)
    for reward in db_rewards:
        if reward[rewards.CONDITION] == "milestone"\
            and reward[rewards.NATURE] == "role"\
            and reward[rewards.POINTS_REQUIRED] <= current_points:
            try:
                await member.add_role(reward[rewards.REWARD], "Milestone reward")
            except BotException:
                return


async def add_points_listener(guild_ctx, member_id, value, member=None):
    """Business related to adding points"""
    db_member = dao.get_member(guild_ctx.id, member_id)
    if member is None:
        member = await guild_ctx.fetch_member(member_id)
    dao.add_points(guild_ctx.id, db_member[members.ID], value)
    await update_rewards(guild_ctx.id, member, db_member[members.POINTS] + value)


def generate_shop(db_guild):
    """Generate all the components to send to make the shop"""
    # Makes new shop
    guild_rewards = dao.get_rewards(db_guild[guilds.ID], condition="bought")
    return tools.generate_shop_items(db_guild, guild_rewards)


async def award(ctx, nature, reward_content):
    """Award a reward to a member"""
    content = None
    error = False
    guild_id = ctx.guild.id
    user_id = ctx.author.id
    db_award_attr = dao.select_award_attribution(guild_id, user_id, nature, reward_content)
    if len(db_award_attr) > 0:
        error = True
        content = f"Couldn't give {nature}, you already have it"
        return [content, error]
    dao.award_reward(guild_id, user_id, nature, reward_content)
    if nature == "role":
        await ctx.author.add_role(reward_content)
        content = f"Role <@&{reward_content}> awarded"
    if content is None:
        error = True
        content = f"Could not award reward for nature {nature}"
    return [content, error]


async def toggle_role_reward(ctx, role_id):
    """Toggles a role reward"""
    content = None
    guild_id = ctx.guild.id
    user = ctx.author
    db_award_attr = dao.select_award_attribution(guild_id, user.id, "role", role_id)
    if len(db_award_attr) == 0:
        content = "You haven't earned this reward yet"
        return content
    has_role = user.has_role(role_id)
    if has_role:
        await user.remove_role(role_id)
        content = f"Role <@&{role_id}> removed"
    else:
        await ctx.author.add_role(role_id)
        content = f"Role <@&{role_id}> given"
    return content
