"""Achievement attribution table"""
TABLE_NAME = "achievement_attr"
GUILD = 0
MEMBER = 1
ACHIEVEMENT = 2

def insert(cursor, guild, member, achievement):
    """Insert an element in the database"""
    cursor.execute(f"INSERT INTO {TABLE_NAME} (guild, member, achievement)"
        " values(%s, %s, %s)",
        [guild, member, achievement])

def select(cursor, guild, member = None, achievement = None):
    """Select constructed depending on the parameters that's given to it"""
    req = (f"SELECT guild, member, achievement FROM {TABLE_NAME}"
        " where guild=%s")
    parm = []
    if member is not None:
        req = f"{req}AND member=%s "
        parm.insert(len(parm),member)
    if achievement is not None:
        req = f"{req}AND achievement=%s "
        parm.insert(len(parm),achievement)
    parm.insert(0, guild)
    cursor.execute(req,parm)
    return cursor.fetchall()

def delete(cursor, guild, member, achievement):
    """Delete an element from the database"""
    cursor.execute(f"DELETE FROM {TABLE_NAME} WHERE "
        "guild=%s AND member=%s AND achievement=%s",
        [guild, member, achievement])
