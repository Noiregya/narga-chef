TABLE_NAME = "guilds"

# - 0 id
# - 1 guild_name
# - 2 currency
# - 3 submission_channel
# - 4 review_channel
# - 5 info_channel
# - 6 leaderboard
# - 7 cooldown

def insert(cursor, guild_id, guild_name, currency, submission_channel, review_channel, info_channel, leaderboard, cooldown):
    cursor.execute(f"INSERT INTO {TABLE_NAME} (id, guild_name, currency, submission_channel, review_channel, info_channel, leaderboard, cooldown) values(%s, %s, %s, %s, %s, %s, %s, %s)",
        [guild_id, guild_name, currency, submission_channel, review_channel, info_channel, leaderboard, cooldown])

def update(cursor, guild_id, guild_name, currency, submission_channel, review_channel, info_channel, cooldown):
    cursor.execute(f"UPDATE {TABLE_NAME} SET guild_name=%s, currency=%s, submission_channel=%s, review_channel=%s, info_channel=%s, cooldown=%s WHERE id=%s",
        [guild_name, currency, submission_channel, review_channel, info_channel, cooldown, guild_id])

def select(cursor, guild_id):
    cursor.execute(f"SELECT id, guild_name, currency, submission_channel, review_channel, info_channel, leaderboard, cooldown FROM {TABLE_NAME} where id=%s",
        [guild_id])
    return cursor.fetchone()

def all(cursor):
    cursor.execute(f"SELECT id, guild_name, currency, submission_channel, review_channel, info_channel, leaderboard, cooldown FROM {TABLE_NAME}")
    return cursor.fetchall()