"""Rewards table"""
TABLE_NAME = "rewards"
GUILD = 0
IDENT = 1
NAME = 2
CONDITION = 3
NATURE = 4
ROLE = 5
POINTS_REQUIRED = 6

def insert(cursor, guild, name, condition, nature, r_role, points_required):
    """Insert an element in the database"""
    cursor.execute(f"INSERT INTO {TABLE_NAME} (guild, r_name, condition, nature, r_role, points_required)"
        " values(%s, %s, %s, %s, %s, %s)",
        [guild, name, condition, nature, r_role, points_required])


def select(cursor, guild, list_ident = None, name = None, condition = None, nature = None, r_role = None):
    """Select constructed depending on the parameters that's given to it"""
    req = (f"SELECT guild, ident, r_name, condition, nature, r_role, points_required FROM {TABLE_NAME}"
        " where guild=%s")
    parm = []
    if(list_ident is not None):
        req = f"{req}AND ident=ANY(%s) "
        parm.insert(len(parm),list_ident)
    if name is not None:
        req = f"{req}AND r_name=%s "
        parm.insert(len(parm),name)
    if condition is not None:
        req = f"{req}AND condition=%s "
        parm.insert(len(parm),condition)
    if nature is not None:
        req = f"{req}AND nature=%s "
        parm.insert(len(parm),nature)
    if r_role is not None:
        req = f"{req}AND r_role=%s "
        parm.insert(len(parm),r_role)
    parm.insert(0, guild)
    req = f"{req}ORDER BY ident"
    cursor.execute(req,parm)
    return cursor.fetchall()


def delete(cursor, guild, list_ident = None, name = None, condition = None, nature = None, r_role = None):
    """Delete an element from the database"""
    req = f"DELETE FROM {TABLE_NAME} WHERE guild=%s"
    parm = []
    if(list_ident is not None):
        req = f"{req}AND ident=ANY(%s) "
        parm.insert(len(parm),list_ident)
    if name is not None:
        req = f"{req}AND r_name=%s "
        parm.insert(len(parm),name)
    if condition is not None:
        req = f"{req}AND condition=%s "
        parm.insert(len(parm),condition)
    if nature is not None:
        req = f"{req}AND nature=%s "
        parm.insert(len(parm),nature)
    if r_role is not None:
        req = f"{req}AND r_role=%s "
        parm.insert(len(parm),r_role)
    parm.insert(0, guild)
    cursor.execute(req,parm)

