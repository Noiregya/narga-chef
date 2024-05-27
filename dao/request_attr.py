"""Request attribution table"""
TABLE_NAME = "request_attr"
GUILD = 0
MEMBER = 1
REQUEST = 2

def insert(cursor, guild, member, request):
    """Insert an element in the database"""
    cursor.execute(f"INSERT INTO {TABLE_NAME} (guild, member, request)"
        " values(%s, %s, %s)",
        [guild, member, request])

def select(cursor, guild, member = None, request = None):
    """Select constructed depending on the parameters that's given to it"""
    req = (f"SELECT guild, member, request FROM {TABLE_NAME}"
        " where guild=%s")
    parm = []
    if member is not None:
        req = f"{req}AND member=%s "
        parm.insert(len(parm),member)
    if request is not None:
        req = f"{req}AND request=%s "
        parm.insert(len(parm),request)
    parm.insert(0, guild)
    cursor.execute(req,parm)
    return cursor.fetchall()

def delete(cursor, guild, member, request):
    """Delete an element from the database"""
    cursor.execute(f"DELETE FROM {TABLE_NAME} WHERE "
        "guild=%s AND member=%s AND request=%s",
        [guild, member, request])
