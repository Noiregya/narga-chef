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
import dao.achievements as achievements
import dao.reward_attr as reward_attr
import dao.request_attr as request_attr
import dao.achievement_attr as achievement_attr

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
            return members.rank(cursor, guild_id, member_id)[0][0]


def get_leaderboard(guild_id: int):
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            return members.rank(cursor, guild_id)


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


def update_member_submission(guild_id: int, member_id: int, last_submission: str):
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            return members.update_submission(
                cursor, guild_id, member_id, last_submission
            )

def update_cooldown(guild_id: int, member_id: int, next_submission_time: datetime):
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            return members.set_cooldown(
                cursor, guild_id, member_id, next_submission_time
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


def request_delete(guild_id, ident = None, request_type = None, request_name = None, effect = None, list_ident = None):
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            return requests.delete(cursor, guild_id, ident, request_type, request_name, effect, list_ident)


def get_request(guild_id, request_type, name, effect):
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            return requests.selectOne(cursor, guild_id, request_type, name, effect)


def get_requests(guild_id, request_type=None, name=None, effect=None, list_ident=None):
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
                list_ident=list_ident,
            )


def add_points(guild_id, member_id, points):
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            return members.add_points(cursor, guild_id, member_id, points)

def add_spent(guild_id, member_id, points):
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            return members.add_spent(cursor, guild_id, member_id, points)


def guild_exists(cursor, guild_id):
    """True if the guild exists in the database"""
    return guilds.select(cursor, guild_id) is not None


def refresh_and_get_member(cursor, guild_id, member_id, nickname):
    """Create member if it doesn't exist, update its nickname then gets it"""
    db_member = members.select(cursor, guild_id, member_id)
    if db_member is None:
        members.insert(cursor, guild_id, member_id, nickname, 0, 0, datetime.min, None)
        db_member = members.select(cursor, guild_id, member_id)
    else:  # Update nickname for database maintenability
        members.update(
            cursor,
            db_member[members.GUILD],
            db_member[members.ID],
            nickname,
            db_member[members.POINTS],
            db_member[members.SPENT],
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


def delete_reward(guild_id, list_ident=None, condition=None, nature=None, reward_id=None):
    """Delete a reward in the database"""
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            return rewards.delete(cursor, guild_id, list_ident, condition, nature, reward_id)


def get_rewards(guild_id, list_ident=None, condition=None, nature=None, reward_id=None):
    """Selects a reward in the database"""
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            return rewards.select(cursor, guild_id, list_ident, condition, nature, reward_id)


def award_reward(guild_id, user_id, reward):
    """Links a reward to a user"""
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            return reward_attr.insert(cursor, guild_id, user_id, reward)


def deny_reward(guild_id, user_id, reward):
    """Unlinks a reward to a user"""
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            return reward_attr.delete(cursor, guild_id, user_id, reward)


def get_reward_attribution(guild_id, user_id, ident = None):
    """Selects award attributions"""
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            return reward_attr.select(cursor, guild_id, user_id, ident)


def award_request(guild_id, user_id, request):
    """Links a request to a user"""
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            return request_attr.insert(cursor, guild_id, user_id, request)


def deny_request(guild_id, user_id, request):
    """Unlinks a request to a user"""
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            return request_attr.delete(cursor, guild_id, user_id, request)


def get_request_attribution(guild_id, member_id, ident = None):
    """Gets request attributions"""
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            return request_attr.select(cursor, guild_id, member_id, ident)

def insert_achievement(guild_id, a_name, icon, condition):
    """Insert a reward in the database"""
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            return achievements.insert(cursor, guild_id, a_name, icon, condition)


def select_achievements(guild, ident = None, name = None, icon = None, condition = None):
    """Selects request attributions"""
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            return achievements.select(cursor, guild, ident, name, icon, condition)


def select_achievement_attr(guild, member = None, achievement = None):
    """Selects achievement attributions"""
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            return achievement_attr.select(cursor, guild, member, achievement)


def award_achievement(guild, member, achievement):
    """Award achievement to a member"""
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            return achievement_attr.insert(cursor, guild, member, achievement)
