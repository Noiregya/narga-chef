import os
from datetime import datetime
from dotenv import load_dotenv
import psycopg
import dao.guilds
import dao.members
import dao.options
import dao.requests

HOST = os.environ["host"]
PASSWORD = os.environ["password"]
DB_USER = os.environ["db_user"]
DB_NAME = "narga"

# connection = psycopg.connect(f"dbname=narga user=narga host={HOST} password={PASSWORD}")

def setup(guild_id: int, guild_name: int, currency: str, submission_channel: int, review_channel: int, info_channel: int, cooldown: int):
    #Reconnecting everytime because else the connect object will go out of scope
    with psycopg.connect(f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}") as connection: 
        with connection.cursor() as cursor:
            res = dao.guilds.select(cursor, guild_id)
            if(res != None):
                dao.guilds.update(cursor, guild_id, guild_name, currency, submission_channel, review_channel, info_channel, cooldown)
            else:
                dao.guilds.insert(cursor, guild_id, guild_name, currency, submission_channel, review_channel, info_channel, None, cooldown)

def refreshAndGetMember(cursor, guild_id, member_id, nickname):
    res = dao.members.select(cursor, guild_id, member_id)
    if(res == None):
        dao.members.insert(cursor, guild_id, member_id, nickname, 0, datetime.utcnow(), None)
        res = dao.members.select(cursor, guild_id, member_id)
    else: #Update nickname for database maintenability
        dao.members.update(cursor, res[0], res[1], nickname, res[3], res[4], res[5])
    return res

def getGuild(guild_id: int):
    with psycopg.connect(f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}") as connection:
        with connection.cursor() as cursor:
            return dao.guilds.select(cursor, guild_id)

def getRank(guild_id: int, member_id: int):
    with psycopg.connect(f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}") as connection:
        with connection.cursor() as cursor:
            return dao.members.rank(cursor, guild_id, member_id)

def getMember(guild_id: int, member_id: int, nickname: str):
    with psycopg.connect(f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}") as connection:
        with connection.cursor() as cursor:
            return refreshAndGetMember(cursor, guild_id, member_id, nickname)

def requestRegister(guild_id, name, effect, value):
    with psycopg.connect(f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}") as connection:
        with connection.cursor() as cursor:
            return dao.requests.insert(cursor, guild_id, name, effect, value)

def requestDelete(guild_id, name, effect):
    with psycopg.connect(f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}") as connection:
        with connection.cursor() as cursor:
            return dao.requests.delete(cursor, guild_id, name, effect)

def getRequest(guild_id, name, effect):
    with psycopg.connect(f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}") as connection:
        with connection.cursor() as cursor:
            return dao.requests.selectOne(cursor, guild_id, name, effect)

def requests(guild_id, name, effect):
    with psycopg.connect(f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}") as connection:
        with connection.cursor() as cursor:
            return dao.requests.select(cursor, guild_id, name, effect)

# Groups every column in lists 
def requestPerColumn(guid_id, name = None, effect = None):
    db_res = requests(guid_id, name, effect)
    name = []
    effect = []
    value = []
    for row in db_res:
        name.append(row[1])
        effect.append(row[2])
        value.append(row[3])
    return [name, effect, value]
