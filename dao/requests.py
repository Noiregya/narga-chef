"""Requests table"""
TABLE_NAME = "requests"
GUILD = 0
IDENT = 1
REQUEST_TYPE = 2
REQUEST_NAME = 3
EFFECT = 4
VALUE = 5

# The nickname column is only used for looking at the database directly, it will never be used in the business
def insert(cursor, guild, request_type, request_name, effect, value):
    cursor.execute(f"INSERT INTO {TABLE_NAME} (guild, request_type, request_name, effect, value) values(%s, %s, %s, %s, %s)",
        [guild, request_type, request_name, effect, value])

def update(cursor, guild, request_type, request_name, effect, value):
    cursor.execute(f"UPDATE {TABLE_NAME} SET value=%s WHERE guild=%s AND request_type=%s AND request_name=%s AND effect=%s",
        [value, guild, request_type, request_name, effect])

def delete(cursor, guild, request_type, request_name, effect):
    cursor.execute(f"DELETE FROM {TABLE_NAME} WHERE guild=%s AND request_type=%s AND request_name=%s AND effect=%s",
        [guild, request_type, request_name, effect])

def selectOne(cursor, guild, request_type, request_name, effect):
    cursor.execute(f"SELECT guild, ident, request_type, request_name, effect, value FROM {TABLE_NAME} where guild=%s AND request_type=%s AND request_name=%s AND effect=%s",
        [guild, request_type, request_name, effect])
    return cursor.fetchone()

# A select with optionnal name and effect
def select(cursor, guild, ident = None, request_type = None, request_name = None, effect = None, list_ident = None):
    req = f"SELECT guild, ident, request_type, request_name, effect, value FROM {TABLE_NAME} where guild=%s "
    parm = []
    if(ident != None):
        req = f"{req}AND ident=%s "
        parm.insert(len(parm),ident)
    if(request_type != None):
        req = f"{req}AND request_type=%s "
        parm.insert(len(parm),request_type)
    if(request_name != None):
        req = f"{req}AND request_name=%s "
        parm.insert(len(parm),request_name)
    if(effect != None):
        req = f"{req}AND effect=%s "
        parm.insert(len(parm),effect)
    if(list_ident != None):
        req = f"{req}AND ident=ANY(%s) "
        parm.insert(len(parm),list_ident)
    parm.insert(0, guild)
    cursor.execute(req, parm)
    return cursor.fetchall()