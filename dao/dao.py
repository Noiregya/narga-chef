"""Entry point for database requests"""

import os
from datetime import datetime
from dotenv import load_dotenv
import psycopg
import dao.guilds
import dao.members
import dao.requests as requests

load_dotenv()

HOST = os.environ.get("host")
PASSWORD = os.environ.get("password")
DB_USER = os.environ.get("db_user")
DB_NAME = "narga"

# connection = psycopg.connect(f"dbname=narga user=narga host={HOST} password={PASSWORD}")


def setup(
    guild_id: int,
    guild_name: int,
    currency: str,
    submission_channel: int,
    review_channel: int,
    info_channel: int,
    cooldown: int,
):
    # Reconnecting everytime because else the connect object will go out of scope
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            if guild_exists(cursor, guild_id):
                return dao.guilds.update(
                    cursor,
                    guild_id,
                    guild_name,
                    currency,
                    submission_channel,
                    review_channel,
                    info_channel,
                    cooldown,
                )
            else:
                return dao.guilds.insert(
                    cursor,
                    guild_id,
                    guild_name,
                    currency,
                    submission_channel,
                    review_channel,
                    info_channel,
                    None,
                    cooldown,
                )


def get_guild(guild_id: int):
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            return dao.guilds.select(cursor, guild_id)


def get_rank(guild_id: int, member_id: int):
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            return dao.members.rank(cursor, guild_id, member_id)


def get_member(guild_id: int, member_id: int, nickname: str):
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            return refresh_and_get_member(cursor, guild_id, member_id, nickname)


def update_member_submission(guild_id: int, member_id: int, last_submission: str):
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            return dao.members.update_submission(
                cursor, guild_id, member_id, datetime.utcnow(), last_submission
            )


def request_register(guild_id, request_type, name, effect, value):
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            return requests.insert(
                cursor, guild_id, request_type, name, effect, value
            )


def request_delete(guild_id, request_type, name, effect):
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            return requests.delete(cursor, guild_id, request_type, name, effect)


def get_request(guild_id, request_type, name, effect):
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            return requests.selectOne(cursor, guild_id, request_type, name, effect)


def get_requests(guild_id, request_type=None, name=None, effect=None):
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            return requests.select(
                cursor,
                guild_id,
                request_type=request_type,
                request_name=name,
                effect=effect,
            )


def add_points(guild_id, member_id, points):
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            return dao.members.add_points(cursor, guild_id, member_id, points)


def guild_exists(cursor, guild_id):
    """True if the guild exists in the database"""
    return dao.guilds.select(cursor, guild_id) is not None


def refresh_and_get_member(cursor, guild_id, member_id, nickname):
    """Create member if it doesn't exist, update its nickname then gets it"""
    db_member = dao.members.select(cursor, guild_id, member_id)
    if db_member is None:
        dao.members.insert(cursor, guild_id, member_id, nickname, 0, datetime.min, None)
        db_member = dao.members.select(cursor, guild_id, member_id)
    else:  # Update nickname for database maintenability
        dao.members.update(
            cursor,
            db_member[dao.members.GUILD],
            db_member[dao.members.ID],
            nickname,
            db_member[dao.members.POINTS],
            db_member[dao.members.LAST_SUBMISION_TIME],
            db_member[dao.members.LAST_SUBMISION_TIME],
        )
    return db_member


def request_per_column(guid_id, request_type=None, name=None, effect=None):
    """Groups every column in lists"""
    db_requests = get_requests(guid_id, request_type, name, effect)
    request_type = []
    name = []
    effect = []
    value = []
    for request in db_requests:
        request_type.append(request[requests.REQUEST_TYPE])
        name.append(request[requests.REQUEST_NAME])
        effect.append(request[requests.EFFECT])
        value.append(request[requests.VALUE])
    request_type = list(dict.fromkeys(request_type))
    name = list(dict.fromkeys(name))
    effect = list(dict.fromkeys(effect))
    value = list(dict.fromkeys(value))
    return {"type": request_type, "name": name, "effect": effect, "value": value}
