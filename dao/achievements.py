"""Achievements table"""
TABLE_NAME = "achievements"
GUILD = 0
NAME = 1
IMAGE = 2
C_POINTS = 3
C_REWARDS = 4
C_REQUESTS = 5


# The nickname column is only used for looking at the database directly, it will never be used in the business
def insert(cursor, guild_id, name, image, c_points, c_rewards, c_requests):
    cursor.execute(f"INSERT INTO {TABLE_NAME} (guild, name, image, c_points, c_rewards, c_requests) values(%s, %s, %s, %s, %s, %s)",
        [guild_id, name, image, c_points, c_rewards, c_requests])

def update(cursor, guild_id, name, image, c_points, c_rewards, c_requests):
    cursor.execute(f"UPDATE {TABLE_NAME} SET image=%s, c_points=%s, c_rewards=%s, c_requests=%s WHERE guild=%s AND name=%s",
        [image, c_points, c_rewards, c_requests, guild_id, name])

def select(cursor, guild_id, name):
    cursor.execute(f"SELECT guild_id, name, image, c_points, c_rewards, c_requests FROM {TABLE_NAME} where  guild=%s AND id=%s",
        [guild_id, name])
    return cursor.fetchone()

def delete(cursor, guild_id, name):
    cursor.execute(f"DELETE FROM {TABLE_NAME} WHERE guild=%s AND name=%s",
        [guild_id, name])