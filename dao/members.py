"""Members table"""
TABLE_NAME = "members"
GUILD = 0
ID = 1
NICKNAME = 2
POINTS = 3
NEXT_SUBMISSION_TIME = 4
LAST_SUBMISSION = 5

# The nickname column is only used for looking at the database directly, it will never be used in the business
def insert(cursor, guild_id, member_id, nickname, points, next_submission_time, last_submission):
    cursor.execute(f"INSERT INTO {TABLE_NAME} (guild, id, nickname, points, next_submission_time, last_submission) values(%s, %s, %s, %s, %s, %s)",
        [guild_id, member_id, nickname, points, next_submission_time, last_submission])

def update(cursor, guild_id, member_id, nickname, points, next_submission_time, last_submission):
    cursor.execute(f"UPDATE {TABLE_NAME} SET nickname=%s, points=%s, next_submission_time=%s, last_submission=%s WHERE guild=%s AND id=%s",
        [nickname, points, next_submission_time, last_submission, guild_id, member_id])

def update_submission(cursor, guild_id, member_id, next_submission_time, last_submission):
    cursor.execute(f"UPDATE {TABLE_NAME} SET next_submission_time=%s, last_submission=%s WHERE guild=%s AND id=%s",
        [next_submission_time, last_submission, guild_id, member_id])

def add_points(cursor, guild_id, member_id, points):
    cursor.execute(f"UPDATE {TABLE_NAME} SET points=points + %s WHERE guild=%s AND id=%s",
        [points, guild_id, member_id])

def reset_cooldown(cursor, guild_id, member_id):
    cursor.execute(f"UPDATE {TABLE_NAME} SET next_submission_time=NOW() WHERE guild=%s AND id=%s",
        [guild_id, member_id])

def select(cursor, guild_id, member_id):
    cursor.execute(f"SELECT guild, id, nickname, points, next_submission_time, last_submission FROM {TABLE_NAME} where  guild=%s AND id=%s",
        [guild_id, member_id])
    return cursor.fetchone()

def all(cursor):
    cursor.execute(f"SELECT guild, id, nickname, points, next_submission_time, last_submission FROM {TABLE_NAME}")
    return cursor.fetchall()

def rank(cursor, guild_id, member_id):
    cursor.execute(f"SELECT guild, id, ROW_NUMBER() OVER(ORDER BY points DESC) FROM {TABLE_NAME} where guild=%s AND id=%s",
        [guild_id, member_id])
    return cursor.fetchone()