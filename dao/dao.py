"""Entry point for database requests"""

# pylint: disable=E1129

import os
from datetime import datetime
from dotenv import load_dotenv
import psycopg
import dao.guilds as guilds
import dao.members as members
import dao.requests as requests
import dao.rewards as rewards

load_dotenv()

HOST = os.environ.get("host")
PASSWORD = os.environ.get("password")
DB_USER = os.environ.get("db_user")
DB_NAME = os.environ.get("db_name")

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
                return guilds.update(
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
                return guilds.insert(
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
            return guilds.select(cursor, guild_id)


def get_rank(guild_id: int, member_id: int):
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            return members.rank(cursor, guild_id, member_id)


def fetch_member(guild_id: int, member_id: int, nickname: str):
    """Refreshes and return db member"""
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            return refresh_and_get_member(cursor, guild_id, member_id, nickname)


def get_member(guild_id: int, member_id: int):
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            return members.select(cursor, guild_id, member_id)


def update_member_submission(
    guild_id: int, member_id: int, next_submission_time: datetime, last_submission: str
):
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            return members.update_submission(
                cursor, guild_id, member_id, next_submission_time, last_submission
            )


def cooldown_reset(guild_id: int, member_id: int):
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            return members.reset_cooldown(cursor, guild_id, member_id)


def request_register(guild_id, request_type, name, effect, value):
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            return requests.insert(cursor, guild_id, request_type, name, effect, value)


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
            return members.add_points(cursor, guild_id, member_id, points)


def guild_exists(cursor, guild_id):
    """True if the guild exists in the database"""
    return guilds.select(cursor, guild_id) is not None


def refresh_and_get_member(cursor, guild_id, member_id, nickname):
    """Create member if it doesn't exist, update its nickname then gets it"""
    db_member = members.select(cursor, guild_id, member_id)
    if db_member is None:
        members.insert(cursor, guild_id, member_id, nickname, 0, datetime.min, None)
        db_member = members.select(cursor, guild_id, member_id)
    else:  # Update nickname for database maintenability
        members.update(
            cursor,
            db_member[members.GUILD],
            db_member[members.ID],
            nickname,
            db_member[members.POINTS],
            db_member[members.NEXT_SUBMISSION_TIME],
            db_member[members.LAST_SUBMISSION],
        )
    return db_member


def insert_reward(guild_id, condition, nature, reward_id, points_required):
    """Insert a reward in the database"""
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            return rewards.insert(
                cursor, guild_id, condition, nature, reward_id, points_required
            )


def delete_reward(guild_id, condition, nature, reward_id):
    """Delete a reward in the database"""
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            return rewards.delete(cursor, guild_id, condition, nature, reward_id)

def get_rewards(guild_id, condition=None, nature=None, reward_id=None):
    """Selects a reward in the database"""
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            return rewards.select(cursor, guild_id, condition, nature, reward_id)
