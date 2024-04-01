import os
from dotenv import load_dotenv
import psycopg
import dao.guilds
import dao.members
import dao.options
import dao.requests

HOST = os.environ["host"]
PASSWORD = os.environ["password"]

# connection = psycopg.connect(f"dbname=narga user=narga host={HOST} password={PASSWORD}")

def setup(guild_id: int, guild_name: int, currency: str, submission_channel: int, review_channel: int, info_channel: int, cooldown: int):
    with psycopg.connect(f"dbname=narga user=narga host={HOST} password={PASSWORD}") as connection:
        with connection.cursor() as cursor:
            res = dao.guilds.select(cursor, guild_id)
            #cursor.execute("SELECT id, guild_name, currency, submission_channel, review_channel, info_channel, leaderboard, cooldown FROM guilds where id=%s"
            #    ,[guild_id])
            if(res != None):
                dao.guilds.update(cursor, guild_id, guild_name, currency, submission_channel, review_channel, info_channel, cooldown)
            else:
                dao.guilds.insert(cursor, guild_id, guild_name, currency, submission_channel, review_channel, info_channel, None, cooldown)
