"""Members table"""
TABLE_NAME = "members"
GUILD = 0
ID = 1
NICKNAME = 2
POINTS = 3
SPENT = 4
NEXT_SUBMISSION_TIME = 5
LAST_SUBMISSION = 6

# The nickname column is only used for looking at the database directly, it will never be used in the business
def insert(cursor, guild_id, member_id, nickname, points, spent, next_submission_time, last_submission):
    cursor.execute(f"INSERT INTO {TABLE_NAME} (guild, id, nickname, points, spent, next_submission_time, last_submission) values(%s, %s, %s, %s, %s, %s, %s)",
        [guild_id, member_id, nickname, points, spent, next_submission_time, last_submission])

def update(cursor, guild_id, member_id, nickname, points, spent, next_submission_time, last_submission):
    cursor.execute(f"UPDATE {TABLE_NAME} SET nickname=%s, points=%s, spent=%s, next_submission_time=%s, last_submission=%s WHERE guild=%s AND id=%s",
        [nickname, points, spent, next_submission_time, last_submission, guild_id, member_id])

def update_submission(cursor, guild_id, member_id, last_submission):
    cursor.execute(f"UPDATE {TABLE_NAME} SET last_submission=%s WHERE guild=%s AND id=%s",
        [last_submission, guild_id, member_id])

def set_cooldown(cursor, guild_id, member_id, next_submission_time):
    cursor.execute(f"UPDATE {TABLE_NAME} SET next_submission_time=%s WHERE guild=%s AND id=%s",
        [next_submission_time, guild_id, member_id])

def add_points(cursor, guild_id, member_id, points):
    cursor.execute(f"UPDATE {TABLE_NAME} SET points=points+%s WHERE guild=%s AND id=%s",
        [points, guild_id, member_id])

def add_spent(cursor, guild_id, member_id, spent):
    cursor.execute(f"UPDATE {TABLE_NAME} SET spent=spent + %s WHERE guild=%s AND id=%s",
        [spent, guild_id, member_id])

def reset_cooldown(cursor, guild_id, member_id):
    cursor.execute(f"UPDATE {TABLE_NAME} SET next_submission_time=NOW() WHERE guild=%s AND id=%s",
        [guild_id, member_id])

def select(cursor, guild_id, member_id):
    cursor.execute(f"SELECT guild, id, nickname, points, spent, next_submission_time, last_submission FROM {TABLE_NAME} where  guild=%s AND id=%s",
        [guild_id, member_id])
    return cursor.fetchone()

def rank(cursor, guild_id, member_id):
    cursor.execute(
        ";WITH cte AS("
        f"SELECT id, ROW_NUMBER() OVER(ORDER BY points DESC) rank FROM {TABLE_NAME} where guild=%s "
        ")"
        "SELECT rank from cte WHERE id=%s",
        [guild_id, member_id])
    return cursor.fetchone()