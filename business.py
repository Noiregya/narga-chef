"""Functions making up the most of the bot's algorithm"""

import os
from datetime import datetime
import json
import logging
import psycopg
from interactions.client.errors import BotException
import dao.dao as dao
import dao.members as members
import dao.guilds as guilds
import dao.requests as requests
import dao.rewards as rewards
import dao.request_attr as request_attr
import dao.reward_attr as reward_attr
import dao.achievements as achievements
import dao.achievement_attr as achievement_attr
import tools
import render.render as render

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
    type_list = list(dict.fromkeys(type_list))  # Remove doubles
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
    name_list = list(dict.fromkeys(name_list))  # Remove doubles
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
    effect_list = list(dict.fromkeys(effect_list))  # Remove doubles
    if len(effect_list) == 0:
        return await ctx.send(f"Could not find an effect for this {request_type}")
    return await ctx.edit_origin(
        content=f"Please tell us about your {request_type}",
        components=tools.generate_request_component(
            effect_list, req_member, unique, name="Request Effect", variation="effect"
        ),
    )


async def effect_component(ctx, effect, event_type, req_member, unique):
    """A component indicating the effect of request that have been received"""
    image_string = eventDictionnary.get(f"image,{req_member},{unique}")
    request_type = eventDictionnary.get(f"type,{req_member},{unique}")
    name = eventDictionnary.get(f"name,{req_member},{unique}")

    if image_string is not None and request_type is not None and name is not None:
        eventDictionnary[f"{event_type},{req_member},{unique}"] = effect
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
        dao.update_member_submission(ctx.guild.id, user, last_request)
        award_res = award_request(
            ctx.guild.id,
            user,
            request_type=request_type,
            request_name=name,
            request_effect=effect,
        )
        # Send messages
        member_pings = member_pings + f"<@{user}> "
    await notify_member(ctx, member_pings, unique, value, fulfilled=True)
    clear_events(unique, req_member)
    return await ctx.edit_origin(
        content=(
            f"Request accepted by <@{ctx.member.id}>"
            f"{award_res}\n"
            f"{value} points awarded to {member_pings}\n{image_string}"
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


async def buy_component(ctx, nature, ident, cost):
    """A component received when a member tries to buy a reward"""
    db_member = dao.fetch_member(ctx.guild.id, ctx.author.id, ctx.author.display_name)
    balance = db_member[members.POINTS] - db_member[members.SPENT]
    if balance >= cost:
        content, error = await award_reward(ctx, ident)
        if error:
            return content
        dao.add_spent(ctx.guild.id, ctx.author.id, cost)
    else:
        content = f"Not enough funds, cost: {cost} balance: {balance}"
    return content


async def toggle_component(ctx, nature, role_id):
    """A component received when a member tries to toggle a reward"""
    if nature == "role":
        content = await toggle_role_reward(ctx, role_id)
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
    return f"{req_type} {name} with effect {effect} and value {value} added"


async def add_reward(
    ctx,
    name,
    points_required,
    role_id = 0,
    currency = "points",
    condition = "milestone",
    nature = "role",
):
    """Adds a new reward"""
    if condition == "given":
        reward_string = name
    else:
        reward_string = f"{name} <@&{role_id}>"
    try:
        dao.insert_reward(ctx.guild.id, name, condition, nature, role_id, points_required)
    except psycopg.Error as e:
        logging.error(e)
        return await ctx.send(
            f"Could not add {nature} {name} obtained through {condition}"
            " please check that it doesn't already exists"
        )
    return await ctx.send(
        f"{nature} {reward_string} obtained through {condition} with {points_required}"
        f" {currency} added",
        ephemeral=True,
    )
    #  ctx.user.add_role(reward, "Milestone reward")


async def delete_reward(guild_id, ident):
    """Removes a reward"""
    try:
        dao.delete_reward(guild_id, list_ident = [ident])
    except psycopg.Error as e:
        logging.error(e)
        return f"Could not delete this reward. {e}"
    return f"{ident} removed"


def list_rewards(guild_id):
    """Make a string of all the rewards"""
    db_rewards = dao.get_rewards(guild_id)
    rewards_str = "\n".join(
        f"{rew[rewards.IDENT]};"
        f"{rew[rewards.NAME]};"
        f"{rew[rewards.NATURE]};"
        f"{rew[rewards.CONDITION]};"
        f"{rew[rewards.ROLE]};"
        f"{rew[rewards.POINTS_REQUIRED]}"
        for rew in db_rewards
    )
    return "Id ;Name; Nature ;Condition ;Role ;Points\n" f"{rewards_str}"


def list_reward_completed(guild_id, member_id):
    """Lists all the rewards a user have completed"""
    db_reward_attr = dao.get_reward_attribution(guild_id, member_id)
    list_ident = [int(row[reward_attr.REWARD]) for row in db_reward_attr]
    db_rewards = dao.get_rewards(guild_id, list_ident=list_ident)
    rewards_str = "\n".join(
        f"{rew[rewards.IDENT]};"
        f"{rew[rewards.NAME]};"
        f"{rew[rewards.NATURE]};"
        f"{rew[rewards.CONDITION]};"
        f"{rew[rewards.ROLE]};"
        f"{rew[rewards.POINTS_REQUIRED]}"
        for rew in db_rewards
    )
    return "Id; Name; Nature ;Condition ;Role ;Points\n" f"{rewards_str}"


def list_requests(guild_id, request_type):
    """Make a string of all the requests"""
    db_requests = dao.get_requests(guild_id, request_type=request_type)
    requests_str = "\n".join(
        f"{req[rewards.IDENT]};"
        f"{req[requests.REQUEST_NAME]};"
        f"{req[requests.EFFECT]};"
        f"{req[requests.VALUE]}"
        for req in db_requests
    )
    return "Id ;Name; Effect ;Value ;Points\n" f"{requests_str}"


def list_request_completed(guild_id, member_id):
    """Make a string of all the requests that a member completed"""
    db_request_attr = dao.get_request_attribution(guild_id, member_id)
    list_ident = [int(row[request_attr.REQUEST]) for row in db_request_attr]
    db_requests = dao.get_requests(guild_id, list_ident=list_ident)
    requests_str = "\n".join(
        f"{req[rewards.IDENT]};"
        f"{req[requests.REQUEST_NAME]};"
        f"{req[requests.EFFECT]};"
        f"{req[requests.VALUE]}"
        for req in db_requests
    )
    return (
        f"<@{member_id}> has completed the following\n"
        "Id ;Name; Effect ;Value ;Points\n"
        f"{requests_str}"
    )


def award_request(
    guild_id, member_id, ident = None, request_type=None, request_name=None, request_effect=None
):
    """award a request to a user"""
    list_ident = None
    if ident is not None:
        list_ident = [ident]
    db_requests = dao.get_requests(
        guild_id, list_ident = list_ident, request_type=request_type, name=request_name, effect=request_effect
    )
    if len(db_requests) == 0:
        return "It seems that the request no longer exists in the database"
    db_request = db_requests[0]
    ident = db_request[requests.IDENT]
    try:
        dao.award_request(guild_id, member_id, ident)
    except psycopg.Error:
        pass
    return (f"<@{member_id}> is considered as having completed request {ident}")


async def update_rewards(guild_id, member, current_points):
    """Update the rewards a member deserves"""
    db_rewards = dao.get_rewards(guild_id)
    for reward in db_rewards:
        if (
            reward[rewards.CONDITION] == "milestone"
            and reward[rewards.NATURE] == "role"
            and reward[rewards.POINTS_REQUIRED] <= current_points
        ):
            try:
                await member.add_role(reward[rewards.ROLE], "Milestone reward")
            except BotException:
                return


async def add_points_listener(guild_ctx, member_id, value):
    """Business related to adding points"""
    db_member = dao.get_member(guild_ctx.id, member_id)
    member = await guild_ctx.fetch_member(member_id)
    db_member = dao.fetch_member(guild_ctx.id, member_id, member.display_name)
    dao.add_points(guild_ctx.id, db_member[members.ID], value)
    await update_rewards(guild_ctx.id, member, db_member[members.POINTS] + value)


def generate_shop(db_guild, roles):
    """Generate all the components to send to make the shop"""
    # Makes new shop
    guild_rewards = dao.get_rewards(db_guild[guilds.ID], condition="bought")
    return tools.generate_shop_items(db_guild, guild_rewards, roles)


def give_reward(guild_id, member_id, ident):
    """give a reward to a member"""
    db_reward = dao.get_rewards(guild_id, list_ident=[ident])
    if len(db_reward) == 0:
        return f"No reward with ident {ident}"
    try:
        dao.award_reward(guild_id, member_id, ident)
    except psycopg.Error as e:
        print(e)
        return "Error adding reward"
    return "Reward added"


async def award_reward(ctx, ident):
    """Award a reward to a member"""
    content = None
    error = False
    guild_id = ctx.guild.id
    member_id = ctx.author.id
    db_award_attr = dao.get_reward_attribution(guild_id, member_id, ident)
    if len(db_award_attr) > 0:
        error = True
        content = "Couldn't give this award, you already have it"
        return [content, error]
    dao.award_reward(guild_id, member_id, ident)
    db_rewards = dao.get_rewards(guild_id, list_ident=[ident])
    if len(db_rewards) < 1:
        error = True
        content = f"Reward number {ident} doesn't exist anymore, ask an admin for help"
        return [content, error]
    db_reward = db_rewards[0]
    if db_reward[dao.rewards.NATURE] == "role":
        await ctx.author.add_role(db_reward[dao.rewards.ROLE])
        content = f"Role <@&{db_reward[dao.rewards.ROLE]}> awarded"
    if content is None:
        error = True
        content = f"Could not award reward {ident}"
    return [content, error]


async def toggle_role_reward(ctx, ident):
    """Toggles a role reward"""
    content = None
    guild_id = ctx.guild.id
    user = ctx.author
    db_rewards = dao.get_rewards(guild_id, nature="role", list_ident=[ident])
    if len(db_rewards) == 0:
        return "This role can't be obtained anymore"
    db_reward = db_rewards[0]
    role_id = db_reward[dao.rewards.ROLE]
    db_award_attr = dao.get_reward_attribution(
        guild_id, user.id, ident
    )
    if len(db_award_attr) == 0:
        return "You haven't earned this reward yet"
    has_role = user.has_role(role_id)
    if has_role:
        await user.remove_role(role_id)
        content = f"Role <@&{role_id}> removed"
    else:
        await ctx.author.add_role(role_id)
        content = f"Role <@&{role_id}> given"
    return content


def conditions_fulfilled(db_member, db_req_attr, db_rew_attr, conditions):
    """Check if all the achievement conditions are fulfilled"""
    requests_lst, rewards_lst, points = conditions
    obtained = False
    if db_member[members.POINTS] >= points:
        obtained = True
    if not obtained:
        return obtained
    obtained = True
    for cond_req in requests_lst:
        obtained = False
        for attr in db_req_attr:
            if attr[request_attr.REQUEST] == cond_req:
                obtained = True
                break
        if not obtained:
            break
    if not obtained:
        return obtained
    obtained = True
    for cond_rew in rewards_lst:
        obtained = False
        for attr in db_rew_attr:
            if attr[reward_attr.REWARD] == cond_rew:
                obtained = True
                break
        if not obtained:
            break
    return obtained


def update_achievements(guild_id, member_id):
    """Adds all the missing achievements to the user if obtained"""
    res = ""
    db_achievements = dao.select_achievements(guild_id)
    db_member = dao.get_member(guild_id, member_id)
    db_req_attr = dao.get_request_attribution(guild_id, member_id)
    db_rew_attr = dao.get_reward_attribution(guild_id, member_id)
    db_requests = dao.get_requests(guild_id)
    db_rewards = dao.get_rewards(guild_id)
    for achievement in db_achievements:
        is_parsed, conditions = tools.parse_condition(achievement[achievements.CONDITION])
        if not is_parsed:
            res = f"{res}Can't parse condition for achievement {achievement[achievements.NAME]}\n"
            continue
        requests_lst, rewards_lst, points = conditions
        missing_req, missing_rew = missing_condition(requests_lst, rewards_lst, db_requests, db_rewards)
        if len(missing_req) > 0 or len(missing_rew) > 0:
            dao.request_delete(guild_id, ident=missing_req)
            dao.delete_reward(guild_id, list_ident=missing_rew)
            res = (f"{res}Missing requests {missing_req} and rewards {missing_rew} from database\n"
                f"Achievement {achievement[achievements.NAME]} ignored, please delete it\n")
            continue
        if conditions_fulfilled(db_member, db_req_attr, db_rew_attr, conditions):
            # Achievement has been obtained
            try:
                dao.award_achievement(guild_id, member_id, achievement[achievements.IDENT])
                res = f"{res}Added achievement {achievement[achievements.NAME]}\n"
            except psycopg.Error:
                continue
    return res


def missing_condition(requests_lst, rewards_lst, db_requests, db_rewards):
    """Checks the conditions against the database objects to make sure it exists"""
    missing_req = []
    for request in requests_lst:
        present = False
        for db_req in db_requests:
            if db_req[requests.IDENT] == request:
                present = True
                break
        if not present:
            missing_req.append(request)
    missing_rew = []
    for reward in rewards_lst:
        present = False
        for db_rew in db_rewards:
            if db_rew[rewards.IDENT] == reward:
                present = True
                break
        if not present:
            missing_rew.append(reward)
    return (missing_req, missing_rew)


async def add_achievement(guild_id, name, image, condition, description):
    """Add the following achievement"""
    is_parsed, conditions = tools.parse_condition(condition)
    blob = await render.download(image.url)
    icon = render.resize(render.SMALL_ICON, render.SMALL_ICON, blob = blob)
    if is_parsed:
        requests_lst, rewards_lst, points = conditions
        no_condition = len(requests_lst) == 0 and len(rewards_lst) == 0 and points == 0
    if not is_parsed or no_condition:
        return (f"{conditions} you have to specify the following:\n"
            "requests: A list of request id the member must complete\n"
            "rewards: A list of rewards id the member must have obtained\n"
            "points: The number of total points a user must have reached\n"
            "It must be a json object in the following fashion:\n"
            "```JSON\n{\"requests\": [1,6,23], \"rewards\": [1,22,34], \"points\": 500}```")
    if image.content_type.startswith("image") is False:
        return ("Incorrect attachement for image. Please provide a proper image."
            "Animated GIFs are not supported. Recommanded size is 48*48.")
    db_requests = dao.get_requests(guild_id, list_ident=requests_lst)
    db_rewards = dao.get_rewards(guild_id, list_ident=rewards_lst)
    missing_req = tools.missing_ident(requests_lst, db_requests, dao.requests.IDENT)
    missing_rew = tools.missing_ident(rewards_lst, db_rewards, dao.rewards.IDENT)
    if len(missing_req) > 0 or len(missing_rew) > 0:
        return ("The following don't exist in the database:\n"
            f"Requests {missing_req}, Rewards {missing_rew}")
    json_condition = json.dumps({"requests":requests_lst, "rewards":rewards_lst, "points":points})
    try:
        dao.insert_achievement(guild_id, name, icon, json_condition, description)
    except psycopg.Error as e:
        logging.error(e)
        return (
            f"Could not add {name} please check that it doesn't already exists"
        )
    return f"Achievement {name} added"

def list_achievements(guild_id):
    """Make a string of all the achievements"""
    db_achievements = dao.select_achievements(guild_id)
    return tools.generate_achievements(db_achievements)


async def get_card_image(db_member, db_guild, rank, pfp=None):
    """Get the rendered image of a user's guild card"""
    res = ""
    currency = db_guild[guilds.CURRENCY]
    guild_id = db_member[members.GUILD]
    member_id = db_member[members.ID]
    points = db_member[members.POINTS]
    nick = db_member[members.NICKNAME]
    balance = points - db_member[members.SPENT]
    next_sub_t = db_member[members.NEXT_SUBMISSION_TIME]
    # Update the user's achievements
    res = f"{res}\n{update_achievements(guild_id, member_id)}"
    db_achievements = dao.select_achievements(guild_id)
    db_achievement_attr = dao.select_achievement_attr(guild_id, member_id)
    icon_achievements = []
    for ach in db_achievements:
        for attr in db_achievement_attr:
            if ach[achievements.IDENT] == attr[achievement_attr.ACHIEVEMENT]:
                icon_achievements.append(ach[achievements.ICON])
                break
    # last_sub = db_member[dao.members.LAST_SUBMISSION]
    png = os.path.abspath(f"render/{guild_id}_{member_id}_card.png")
    # Replaces image if exists
    # render.clear_cache(png)
    images = await render.cache_images(guild_id, member_id, pfp_url=pfp)

    if next_sub_t.year is datetime.min.year:
        next_req_str = "No submission yet"
    else:
        delta = round(next_sub_t.timestamp() - datetime.now().timestamp())
        if delta < 0:
            next_req_str = "You can submit now"
        else:
            next_req_str = f"Submit in: {tools.human_readable_delta(delta)}"

    render.generate_guild_card(
        png,
        member_id,
        nick,
        currency,
        balance,
        points,
        rank,
        pfp=images.get("pfp"),
        achievements=icon_achievements,
        next_req_str=next_req_str,
    )
    return png


async def delete_achievement(guild_id, a_name):
    """Removes an achievement"""
    try:
        dao.achievement_delete(guild_id, a_name)
    except psycopg.Error as e:
        logging.error(e)
        return f"Could not delete this achievement. {e}"
    return f"{a_name} removed"