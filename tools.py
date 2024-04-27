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
    Attachment,
)
import dao.dao as dao
import dao.members as members
import dao.guilds as guilds
import dao.requests as requests

ONE_HOUR = 3600
PURPLE = "#7f03fc"
AQUAMARINE = "#00edd9"


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
    rank = EmbedField(name="Rank", value=str(rank[2]), inline=True)
    if db_member[members.NEXT_SUBMISSION_TIME].year is datetime.min.year:
        timestamp_string = "No submission yet"
    else:
        timestamp_next_request = db_member[members.NEXT_SUBMISSION_TIME].timestamp()
        timestamp_string = f"<t:{int(timestamp_next_request)}>"
    cooldown = EmbedField(name="Cooldown", value=timestamp_string, inline=True)
    embed = Embed(
        color=PURPLE,
        title=f"Guild card for {db_member[members.NICKNAME]}",
        fields=[points, rank, cooldown],
    )
    return embed


def requests_content(db_requests):
    """Format the requests in a string"""
    res = "```csv\nType; Name; Effect; Value\n"
    for request in db_requests:
        res = (
            f"{res}"
            f"{request[requests.REQUEST_TYPE]};"
            f"{request[requests.REQUEST_NAME]};"
            f"{request[requests.EFFECT]};"
            f"{request[requests.VALUE]}\n"
        )
    return f"{res}```"


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
    res: list[ActionRow] = spread_to_rows(  # TODO: check size limit
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
