"""Achievements table"""
TABLE_NAME = "achievements"
GUILD = 0
IDENT = 1
NAME = 2
ICON = 3
CONDITION = 4

def insert(cursor, guild_id, a_name, icon, condition):
    """Insert an element in the database"""
    cursor.execute(f"INSERT INTO {TABLE_NAME} (guild, a_name, icon, condition)"
        " values(%s, %s, %s, %s)",
        [guild_id, a_name, icon, condition])

def select(cursor, guild, ident = None, a_name = None, icon = None, condition = None):
    """Select constructed depending on the parameters that's given to it"""
    req = (f"SELECT guild, ident, a_name, icon, condition FROM {TABLE_NAME}"
        " where guild=%s")
    parm = []
    parm.insert(0, guild)
    if ident is not None:
        req = f"{req}AND ident=ANY(%s) "
        parm.insert(len(parm),ident)
    if a_name is not None:
        req = f"{req}AND a_name=%s "
        parm.insert(len(parm),a_name)
    if icon is not None:
        req = f"{req}AND icon=%s "
        parm.insert(len(parm),icon)
    if condition is not None:
        req = f"{req}AND condition=%s "
        parm.insert(len(parm),condition)
    cursor.execute(req,parm)
    return cursor.fetchall()

def delete(cursor, guild, ident = None, a_name = None):
    """Delete an element from the database"""
    req = f"DELETE FROM {TABLE_NAME} WHERE "
    parm = []
    parm.insert(0, guild)
    if ident is not None:
        req = f"{req}AND ident=ANY(%s) "
        parm.insert(len(parm),ident)
    if a_name is not None:
        req = f"{req}AND ident=%s "
        parm.insert(len(parm),a_name)
    cursor.execute(req,parm)
