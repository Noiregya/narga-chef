"""Create or update the database"""
import os
import logging
from packaging.version import Version
from dotenv import load_dotenv
import psycopg

load_dotenv()

HOST = os.environ.get("host")
PASSWORD = os.environ.get("password")
DB_USER = os.environ.get("db_user")
DB_NAME = "narga"
SQL_DIRECTORY = "dao/sql/"

version = "0.0.0"

def get_sql_to_execute(current):
    files = os.listdir(SQL_DIRECTORY)
    filtered_files = list(filter(lambda file: Version(file.rsplit('.', maxsplit=1)[0]) > Version(current),files))
    return sorted(filtered_files, key=lambda file: Version(file.rsplit('.', maxsplit=1)[0]))

def run_updates():
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            for sql in get_sql_to_execute(version):
                    cursor.execute(open(f"{SQL_DIRECTORY}{sql}", "r", encoding="utf-8").read())

try:
    with psycopg.connect(
        f"dbname={DB_NAME} user={DB_USER} host={HOST} password={PASSWORD}"
    ) as connection:
        with connection.cursor() as cursor:
            try:
                cursor.execute("SELECT data_model_version FROM metanarga;")
                version = cursor.fetchone()[0]
            except psycopg.Error:
                logging.info("First execution detected, creating the database...")
            run_updates()
except psycopg.Error:
    logging.error(
        (
            "Unable to log into, or incorrect permissions for"
            " host %s, user %s on database %s with the provided password",
            HOST, DB_USER, DB_NAME,
        )
    )
