TABLE_NAME = "guilds"

async def insert(cursor, id, guild_name, currency, submission_channel, review_channel, info_channel, leaderboard):
    return cursor.execute("INSERT INTO %s (id, guild_name, currency, submission_channel, review_channel, info_channel, leaderboard) values(%s, %s, %s, %s, %s, %s, %s)",
        (TABLE_NAME, id, guild_name, currency, submission_channel, review_channel, info_channel))

async def update(cursor, id, guild_name, currency, submission_channel, review_channel, info_channel, leaderboard):
    return cursor.execute("UPDATE %s SET (guild_name=%s, currency=%s, submission_channel=%s, review_channel=%s, info_channel=%s, leaderboard=%s) WHERE id=%s",
        (TABLE_NAME, guild_name, currency, submission_channel, review_channel, info_channel, leaderboard, id))

async def select(cursor, id):
    return cursor.execute("SELECT id, guild_name, currency, submission_channel, review_channel, info_channel, leaderboard FROM %s where id=%d",
        (TABLE_NAME, id))

async def all(cursor):
    return cursor.execute("SELECT id, guild_name, currency, submission_channel, review_channel, info_channel, leaderboard FROM %s",
        (TABLE_NAME))