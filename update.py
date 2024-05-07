"""Called when the bot is updated"""
# pylint: disable=E1129
import os
import logging
from packaging.version import Version
from dotenv import load_dotenv

import psycopg

load_dotenv()
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("token")
HOST = os.environ.get("host")
PASSWORD = os.environ.get("password")
DB_USER = os.environ.get("db_user")
DB_NAME = os.environ.get("db_name")
SQL_DIRECTORY = "dao/sql/"

def get_sql_to_execute(current):
    """Get the list of SQL scripts to run for the update"""
    files = os.listdir(SQL_DIRECTORY)
    filtered_files = list(filter(lambda file: Version(file.rsplit('.', maxsplit=1)[0])
        > Version(current),files))
    return sorted(filtered_files, key=lambda file: Version(file.rsplit('.', maxsplit=1)[0]))

def run_updates():
    """Updates the database and returns True if an update has been done"""
    version = "0.0.0"
    try:
        with psycopg.connect(
            f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
        ) as gen_connection:
            with gen_connection.cursor() as gen_cursor:
                try:
                    gen_cursor.execute("SELECT data_model_version FROM metanarga;")
                    version = gen_cursor.fetchone()[0]
                except psycopg.Error:
                    logging.info("First execution detected, creating the database...")
    except psycopg.Error:
        logging.error(
            (
                "Unable to log into, or incorrect permissions for"
                " host %s, user %s on database %s with the provided password",
                HOST, DB_USER, DB_NAME,
            )
        )
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            to_execute = get_sql_to_execute(version)
            for sql in to_execute:
                cursor.execute(open(f"{SQL_DIRECTORY}{sql}", "r", encoding="utf-8").read())
            if len(to_execute) > 0:
                return True
            return False
