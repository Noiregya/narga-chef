"""Rewards table"""
TABLE_NAME = "rewards"
GUILD = 0
IDENT = 1
CONDITION = 2
NATURE = 3
REWARD = 4
POINTS_REQUIRED = 5

def insert(cursor, guild, condition, nature, reward, points_required):
    """Insert an element in the database"""
    cursor.execute(f"INSERT INTO {TABLE_NAME} (guild, condition, nature, reward, points_required)"
        " values(%s, %s, %s, %s, %s)",
        [guild, condition, nature, reward, points_required])

def select(cursor, guild, list_ident = None, condition = None, nature = None, reward = None):
    """Select constructed depending on the parameters that's given to it"""
    req = (f"SELECT guild, ident, condition, nature, reward, points_required FROM {TABLE_NAME}"
        " where guild=%s")
    parm = []
    if(list_ident is not None):
        req = f"{req}AND ident=ANY(%s) "
        parm.insert(len(parm),list_ident)
    if condition is not None:
        req = f"{req}AND condition=%s "
        parm.insert(len(parm),condition)
    if nature is not None:
        req = f"{req}AND nature=%s "
        parm.insert(len(parm),nature)
    if reward is not None:
        req = f"{req}AND reward=%s "
        parm.insert(len(parm),reward)
    parm.insert(0, guild)
    req = f"{req}ORDER BY nature "
    cursor.execute(req,parm)
    return cursor.fetchall()

def delete(cursor, guild, list_ident = None, condition = None, nature = None, reward = None):
    """Delete an element from the database"""
    req = f"DELETE FROM {TABLE_NAME} WHERE guild=%s"
    parm = []
    if(list_ident is not None):
        req = f"{req}AND ident=ANY(%s) "
        parm.insert(len(parm),list_ident)
    if condition is not None:
        req = f"{req}AND condition=%s "
        parm.insert(len(parm),condition)
    if nature is not None:
        req = f"{req}AND nature=%s "
        parm.insert(len(parm),nature)
    if reward is not None:
        req = f"{req}AND reward=%s "
        parm.insert(len(parm),reward)
    parm.insert(0, guild)
    cursor.execute(req,parm)

