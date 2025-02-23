"""Members table"""
TABLE_NAME = "members"
GUILD = 0
ID = 1
NICKNAME = 2
POINTS = 3
SPENT = 4
NEXT_SUBMISSION_TIME = 5
LAST_SUBMISSION = 6
THEME = 7

# The nickname column is only used for looking at the database directly, it will never be used in the business
def insert(cursor, guild_id, member_id, nickname, points, spent, next_submission_time, last_submission, theme):
    cursor.execute(f"INSERT INTO {TABLE_NAME} (guild, id, nickname, points, spent, next_submission_time, last_submission, theme) values(%s, %s, %s, %s, %s, %s, %s, %s)",
        [guild_id, member_id, nickname, points, spent, next_submission_time, last_submission, theme])

def update(cursor, guild_id, member_id, nickname, points, spent, next_submission_time, last_submission, theme):
    cursor.execute(f"UPDATE {TABLE_NAME} SET nickname=%s, points=%s, spent=%s, next_submission_time=%s, last_submission=%s, theme=%s WHERE guild=%s AND id=%s",
        [nickname, points, spent, next_submission_time, last_submission, guild_id, member_id, theme])

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

def set_theme(cursor, guild_id, member_id, theme):
    cursor.execute(f"UPDATE {TABLE_NAME} SET theme=%s WHERE guild=%s AND id=%s",
        [theme, guild_id, member_id])

def reset_cooldown(cursor, guild_id, member_id):
    cursor.execute(f"UPDATE {TABLE_NAME} SET next_submission_time=NOW() WHERE guild=%s AND id=%s",
        [guild_id, member_id])

def select(cursor, guild_id, member_id):
    cursor.execute(f"SELECT guild, id, nickname, points, spent, next_submission_time, last_submission, theme FROM {TABLE_NAME} where  guild=%s AND id=%s",
        [guild_id, member_id])
    return cursor.fetchone()

def rank(cursor, guild_id, member_id = None):
    req = (";WITH cte AS("
        f"SELECT ROW_NUMBER() OVER(ORDER BY points DESC) rank, id, nickname, points FROM {TABLE_NAME} "
        "WHERE guild=%s) "
        "SELECT rank, id, nickname, points FROM cte ")
    parm = [guild_id]
    if member_id is not None:
        req = f"{req}WHERE id=%s "
        parm.insert(len(parm), member_id)
    cursor.execute(req,parm)
    return cursor.fetchall()