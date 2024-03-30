import psycopg
import guilds
import members
import options
import requests

async with await psycopg.AsyncConnection.connect(
        "dbname=narga user=narga") as connection:
    async with connection.cursor() as cursor:
        await cursor.execute(
            "INSERT INTO test (num, data) VALUES (%s, %s)",
            (100, "abc'def"))
        await cursor.execute("SELECT * FROM test")
        await cursor.fetchone()
        # will return (1, 100, "abc'def")
        async for record in cursor:
            print(record)

def setup(guild: int, guild_name: int, currency: str, submission_channel: int, review_channel: int, info_channel: int):
    print(id)