TABLE_NAME = "guilds"

def insert(cursor, guild_id, guild_name, currency, submission_channel, review_channel, info_channel, leaderboard, cooldown):
    cursor.execute("INSERT INTO guilds (id, guild_name, currency, submission_channel, review_channel, info_channel, leaderboard, cooldown) values(%s, %s, %s, %s, %s, %s, %s, %s)",
        [guild_id, guild_name, currency, submission_channel, review_channel, info_channel, leaderboard, cooldown])

def update(cursor, guild_id, guild_name, currency, submission_channel, review_channel, info_channel, cooldown):
    cursor.execute(f"UPDATE {TABLE_NAME} SET guild_name=%s, currency=%s, submission_channel=%s, review_channel=%s, info_channel=%s, cooldown=%s WHERE id=%s",
        [guild_name, currency, submission_channel, review_channel, info_channel, cooldown, guild_id])

def select(cursor, guild_id):
    cursor.execute("SELECT id, guild_name, currency, submission_channel, review_channel, info_channel, leaderboard, cooldown FROM guilds where id=%s",
        [guild_id])
    return cursor.fetchone()

def all(cursor):
    cursor.execute("SELECT id, guild_name, currency, submission_channel, review_channel, info_channel, leaderboard, cooldown FROM %s",
        [TABLE_NAME])
    return cursor.fetchone()