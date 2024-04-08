TABLE_NAME = "requests"
# 0 - guild
# 1 - request_name
# 2 - effect
# 3 - value

# The nickname column is only used for looking at the database directly, it will never be used in the business
def insert(cursor, guild, request_name, effect, value):
    cursor.execute(f"INSERT INTO {TABLE_NAME} (guild, request_name, effect, value) values(%s, %s, %s, %s)",
        [guild, request_name, effect, value])

def update(cursor, guild, request_name, effect, value):
    cursor.execute(f"UPDATE {TABLE_NAME} SET value=%s WHERE guild=%s AND request_name=%s AND effect=%s",
        [value, guild, request_name, effect])

def delete(cursor, guild, request_name, effect):
    cursor.execute(f"DELETE FROM {TABLE_NAME} WHERE guild=%s AND request_name=%s AND effect=%s",
        [guild, request_name, effect])

def select(cursor, guild, request_name, effect):
    cursor.execute(f"SELECT guild, request_name, effect, value FROM {TABLE_NAME} where guild=%s AND request_name=%s AND effect=%s",
        [guild, request_name, effect])
    return cursor.fetchone()

def all(cursor, guild):
    cursor.execute(f"SELECT guild, request_name, effect, value FROM {TABLE_NAME} where guild=%s",
        [guild])
    return cursor.fetchall()