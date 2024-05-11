"""Reusable unitary functions"""

# Imports
import logging
from datetime import datetime
from interactions import (
    Modal,
    ParagraphText,
    spread_to_rows,
    Embed,
    EmbedField,
    StringSelectMenu,
    Button,
    ButtonStyle,
    ActionRow,
)
import dao.dao as dao
import dao.members as members
import dao.guilds as guilds
import dao.requests as requests
import dao.rewards as rewards

ONE_HOUR = 3600
PURPLE = "#7f03fc"
AQUAMARINE = "#00edd9"
PINK = "#ff66b0"
GOLD = "#ffc400"
SILVER = "#7c95a1"


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
    db_guild = dao.get_guild(guild_id)
    if db_guild is None:
        return [False, "Please register this guild by using the /setup command"]
    return [True, db_guild]


def generate_guild_card_embed(db_member, db_guild, rank):
    """Generates the embed for a guild card"""
    points = EmbedField(
        name=db_guild[guilds.CURRENCY],
        value=str(db_member[members.POINTS]),
        inline=True,
    )
    balance = EmbedField(
        name="Balance",
        value=str(db_member[members.POINTS] - db_member[members.SPENT]),
        inline=True,
    )
    rank = EmbedField(name="Rank", value=str(rank), inline=True)
    if db_member[members.NEXT_SUBMISSION_TIME].year is datetime.min.year:
        timestamp_string = "No submission yet"
    else:
        timestamp_next_request = db_member[members.NEXT_SUBMISSION_TIME].timestamp()
        timestamp_string = f"<t:{int(timestamp_next_request)}>"
    cooldown = EmbedField(name="Cooldown until", value=timestamp_string, inline=True)
    embed = Embed(
        color=PURPLE,
        title=f"Guild card for {db_member[members.NICKNAME]}",
        fields=[points, balance, rank, cooldown],
    )
    return embed


def requests_content(guild_id, request_type):
    """Format the requests in embeds"""
    size_chunk = 15
    ord_requests = request_per_column(guild_id, request_type)
    req_type = ord_requests.get("type")
    if len(req_type) < 1:
        return [Embed(title="No result", description=f"Couldn't find any {request_type}")]
    req_type = req_type[0]
    name_chunks = chunk(ord_requests["name"], size_chunk)
    effect_chunks = chunk(ord_requests["effect"], size_chunk)
    val_str = [f"{element}" for element in ord_requests["value"]]# Convert to strings
    value_chunks = chunk(val_str, size_chunk)
    embeds = []
    #pylint: disable=C0200
    #I'm not doing an enum here it makes no sense
    for i in range(len(name_chunks)):
        req_name = EmbedField(
            name="Name",
            value="\n".join(name_chunks[i]),
            inline=True,
        )
        req_effect = EmbedField(
            name="Effect",
            value="\n".join(effect_chunks[i]),
            inline=True,
        )
        req_value = EmbedField(
            name="Value",
            value="\n".join(value_chunks[i]),
            inline=True,
        )
        embed = Embed(
            color=PINK,
            title=f"Available {req_type}",
            fields=[req_name, req_effect, req_value],
        )
        embeds.append(embed)
    return embeds


def generate_leaderboard(db_leaderboard, currency):
    """Generate a leaderboard in a list of embeds to be paginated"""
    chunk_size = 15
    embeds = []
    ranks, names, points = [], [], []
    for i, member_rank in enumerate(db_leaderboard):
        ranks.append(member_rank[0])
        names.append(member_rank[2])
        points.append(member_rank[3])
        if i == 2:
            embeds.append(generate_podium(names, points, currency))
            ranks, names, points = [], [], []
        elif (i - 2) % chunk_size == 0:
            embeds.append(generate_rank_embeds(ranks, names, points, currency))
            ranks, names, points = [], [], []
    if len(ranks) > 0:
        embeds.append(generate_rank_embeds(ranks, names, points, currency))
    return embeds


def generate_podium(names, points, currency):
    """Generate a page of the leaderboard"""
    number_1 = EmbedField(
        name=f"🥇 {names[0]}",
        value=f"Leading with {points[0]} {currency}",
    )
    number_2 = EmbedField(
        name=f"🥈 {names[1]}",
        value=f"Close with {points[1]} {currency}",
    )
    number_3 = EmbedField(
        name=f"🥉 {names[2]}",
        value=f"Keeping up with {points[2]} {currency}",
    )
    embed = Embed(
        color=GOLD,
        title="Podium",
        fields=[number_1, number_2, number_3],
    )
    return embed


def generate_rank_embeds(ranks, names, points, currency):
    """Generate a page of the leaderboard"""
    rank_str = [f"{element}" for element in ranks]# Convert to strings
    point_str = [f"{element}" for element in points]
    rank_embed = EmbedField(
        name="Rank",
        value="\n".join(rank_str),
        inline=True,
    )
    name_embed = EmbedField(
        name="Name",
        value="\n".join(names),
        inline=True,
    )
    points_embed = EmbedField(
        name=currency.capitalize(),
        value="\n".join(point_str),
        inline=True,
    )
    embed = Embed(
        color=SILVER,
        title="Leaderboard",
        fields=[rank_embed, name_embed, points_embed],
    )
    return embed


def chunk(elements, size):
    """Divides a list into smaller lists of specified size"""
    res = []
    start = 0
    end = len(elements)
    for i in range(start, end, size):
        res.append(elements[i:i+size])
    return res


def get_image_attachements(message):
    """Gets the images url attached to a message"""
    images = []
    for attachement in message.attachments:
        if attachement.content_type.startswith("image"):
            images.append(attachement.url)
    return images


def generate_request_component(
    options, member_id, message_id, name="Request name", variation="name"
):
    """Generates a selector for users to pick an option"""
    res: list[ActionRow] = spread_to_rows(
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


def calculate_next_submission_time(previous_next, cooldown):
    """Gives the datetime of the next allowed submission"""
    if previous_next < datetime.now():
        previous_next = datetime.now()
    return datetime.fromtimestamp(
        previous_next.timestamp() + ONE_HOUR * float(cooldown)
    )


def calculate_prev_submission_time(previous_next, cooldown):
    """Gives the datetime of the next allowed submission"""
    return datetime.fromtimestamp(
        previous_next.timestamp() - ONE_HOUR * float(cooldown)
    )


def request_per_column(guild_id, request_type=None, name=None, effect=None):
    """Groups every column in lists"""
    db_requests = dao.get_requests(guild_id, request_type, name, effect)
    request_type = []
    name = []
    effect = []
    value = []
    for request in db_requests:
        request_type.append(request[requests.REQUEST_TYPE])
        name.append(request[requests.REQUEST_NAME])
        effect.append(request[requests.EFFECT])
        value.append(request[requests.VALUE])
    return {"type": request_type, "name": name, "effect": effect, "value": value}


def ordered_requests(guild_id, request_type=None, name=None, effect=None):
    """Groups every column in a 3-dimensional dictionnary"""
    db_requests = dao.get_requests(guild_id, request_type, name, effect)
    all_req = {}
    for request in db_requests:
        type_dict = all_req.get(request[requests.REQUEST_TYPE])
        if type_dict is None:
            all_req[request[requests.REQUEST_TYPE]] = {
                request[requests.REQUEST_NAME]: {
                    request[requests.EFFECT]: request[requests.VALUE]
                }
            }
            continue
        name_dict = type_dict.get(request[requests.REQUEST_NAME])
        if name_dict is None:
            type_dict[request[requests.REQUEST_NAME]] = {
                request[requests.EFFECT]: request[requests.VALUE]
            }
            continue
        effect_dict = name_dict.get(request[requests.EFFECT])
        if effect_dict is None:
            name_dict[request[requests.EFFECT]] = request[requests.VALUE]
            continue
    return all_req


def generate_shop_items(db_guild, db_rewards):
    """Generate messages of each of the provided items with interactions to buy them"""
    rewards_per_nature = {}
    for reward in db_rewards:
        nature = reward[rewards.NATURE]
        reward_content = reward[rewards.REWARD]
        points = reward[rewards.POINTS_REQUIRED]
        reward_nature_list = rewards_per_nature.get(nature)
        reward_nature_list = [] if reward_nature_list is None else reward_nature_list
        # get the list to append with the element
        reward_str = ""
        match nature:
            case "role":
                reward_str =  f"<@&{reward_content}>"
        message = {
            "content" : f"{nature.capitalize()} {reward_str} for {points} {db_guild[guilds.CURRENCY]}",
            "components" : ActionRow(
                Button(
                    style=ButtonStyle.GREEN,
                    label="Buy",
                    custom_id=f"buy,{nature},{reward_content},{points}",
                ),Button(
                    style=ButtonStyle.BLUE,
                    label="Toggle",
                    custom_id=f"toggle,{nature},{reward_content},none",
                )
            )
        }
        reward_nature_list.append(message)
        rewards_per_nature[nature] = reward_nature_list
    return rewards_per_nature
