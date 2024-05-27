"""Rewards attribution table"""
TABLE_NAME = "reward_attr"
GUILD = 0
MEMBER = 1
REWARD = 2

def insert(cursor, guild, member, reward):
    """Insert an element in the database"""
    cursor.execute(f"INSERT INTO {TABLE_NAME} (guild, member, reward)"
        " values(%s, %s, %s)",
        [guild, member, reward])

def select(cursor, guild, member = None, reward = None):
    """Select constructed depending on the parameters that's given to it"""
    req = (f"SELECT guild, member, reward FROM {TABLE_NAME}"
        " where guild=%s")
    parm = []
    if member is not None:
        req = f"{req}AND member=%s "
        parm.insert(len(parm),member)
    if reward is not None:
        req = f"{req}AND reward=%s "
        parm.insert(len(parm),reward)
    parm.insert(0, guild)
    cursor.execute(req,parm)
    return cursor.fetchall()

def delete(cursor, guild, member, reward):
    """Delete an element from the database"""
    cursor.execute(f"DELETE FROM {TABLE_NAME} WHERE "
        "guild=%s AND member=%s AND reward=%s",
        [guild, member, reward])
